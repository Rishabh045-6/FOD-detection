"""
HAWKEYE FOD — fused TBD-GPU + YOLO-v5 (SPD-Conv + NWD) detector (Option B′).
Refactored into a high-speed stateful class interface for unified reuse 
across both standard offline file analysis and low-latency live streaming loops.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time as _time
from typing import Optional, Dict, Any, List, Tuple

import cv2
import numpy as np
import torch

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pipeline import Config, process_video
from pipeline_gpu import process_video_gpu
from train_classifier import TinyNet, PATCH
from detect import Track, Tracker, prefetch, load_classifier, classify_batch


def _register_spdconv():
    """Register SPD-Conv (Upgrade 2) before YOLO load so SPD checkpoints unpickle."""
    try:
        sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        from detection.arch.hawkeye_arch import ensure_registered
        ensure_registered()
    except Exception:
        pass


def load_yolo(weights: str, device_arg, imgsz: int = 1280):
    _register_spdconv()
    from ultralytics import YOLO
    print(f"[fused] loading YOLO from {weights}")
    model = YOLO(weights)
    dummy = np.zeros((imgsz, imgsz, 3), np.uint8)
    model.predict(dummy, conf=0.05, imgsz=imgsz, device=device_arg, verbose=False)
    print(f"[fused] YOLO warm-up done (imgsz={imgsz})")
    return model


def yolo_infer(model, frame, conf_floor: float, imgsz: int, device_arg) -> list:
    r = model.predict(frame, conf=conf_floor, imgsz=imgsz,
                      device=device_arg, verbose=False)[0]
    boxes = []
    if r.boxes is not None and len(r.boxes):
        for b in r.boxes:
            x1, y1, x2, y2 = [float(v) for v in b.xyxy[0]]
            boxes.append([x1, y1, x2, y2, float(b.conf[0])])
    return boxes


def _center(box) -> tuple[float, float]:
    return (box[0] + box[2]) / 2, (box[1] + box[3]) / 2


def _near(cx: float, cy: float, pos, dist: float) -> bool:
    return abs(cx - pos[0]) <= dist and abs(cy - pos[1]) <= dist


def yolo_near_track(yolo_boxes: list, pos, agree_dist: float, yolo_conf: float) -> bool:
    for b in yolo_boxes:
        if b[4] < yolo_conf:
            continue
        cx, cy = _center(b)
        if _near(cx, cy, pos, agree_dist):
            return True
    return False


def near_confirmed(box, confirmed_tracks: list, agree_dist: float) -> bool:
    cx, cy = _center(box)
    for t in confirmed_tracks:
        if _near(cx, cy, t.pos, agree_dist):
            return True
    return False


def warp_boxes(boxes: list, H) -> list:
    if H is None or not boxes:
        return boxes
    Hm = np.asarray(H, np.float64)
    out = []
    for b in boxes:
        pts = np.array([[b[0], b[1], 1.0], [b[2], b[3], 1.0]], np.float64)
        ph = pts @ Hm.T
        ph = ph[:, :2] / ph[:, 2:3]
        x1, y1 = ph[0]
        x2, y2 = ph[1]
        out.append([min(x1, x2), min(y1, y2), max(x1, x2), max(y1, y2), b[4]])
    return out


# --------------------------------------------------------------------------- #
# Core Stateful Abstraction Interface
# --------------------------------------------------------------------------- #

class HawkeyeDetector:
    def __init__(self, tbd_weights: str, yolo_weights: str, args: Optional[argparse.Namespace] = None):
        """
        Initializes the shared sensor fusion processing pipeline.
        Loads neural network layers exactly once into VRAM.
        """
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.device_arg = 0 if self.device == "cuda" else "cpu"

        # Safe defaults configuration context tracking profiles
        self.cls_thresh_solo = getattr(args, 'cls_thresh_solo', 0.94)
        self.cls_thresh_boosted = getattr(args, 'cls_thresh_boosted', 0.70)
        self.min_pos_frac = getattr(args, 'min_pos_frac', 0.6)
        self.min_streak_boosted = getattr(args, 'min_streak_boosted', 3)
        self.min_streak_solo = getattr(args, 'min_streak_solo', 5)
        self.link_dist = getattr(args, 'link_dist', 14.0)
        self.yolo_conf = getattr(args, 'yolo_conf', 0.25)
        self.yolo_agree_dist = getattr(args, 'yolo_agree_dist', 20.0)
        self.yolo_imgsz = getattr(args, 'yolo_imgsz', 1536)
        self.yolo_stride = getattr(args, 'yolo_stride', 4)

        # Permanent In-Memory Weight Registers
        self.cls_net = load_classifier(tbd_weights, self.device)
        self.yolo = load_yolo(yolo_weights, self.device_arg, self.yolo_imgsz)

        # Stateful cross-frame cache memories
        self.tracker = Tracker(link_dist=self.link_dist, min_streak=self.min_streak_solo)
        self.yolo_boxes: list = []
        self.frame_index = 0
        self.n_yolo_runs = 0
        self.prev_gray = None
        self.background = None
    
    def _generate_candidates(self, frame: np.ndarray):
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        if self.prev_gray is None:
            self.prev_gray = gray
            self.background = gray.astype(np.float32)
            return [], np.eye(3, dtype=np.float32)

        pts = cv2.goodFeaturesToTrack(
            self.prev_gray,
            maxCorners=800,
            qualityLevel=0.01,
            minDistance=10,
        )

        H = np.eye(3, dtype=np.float32)

        if pts is not None:
            nxt, st, _ = cv2.calcOpticalFlowPyrLK(
                self.prev_gray,
                gray,
                pts,
                None,
            )

            if nxt is not None:
                good_old = pts[st == 1]
                good_new = nxt[st == 1]

                if len(good_old) >= 4:
                    H, _ = cv2.findHomography(
                        good_old,
                        good_new,
                        cv2.RANSAC,
                        3.0,
                    )

                    if H is None:
                        H = np.eye(3, dtype=np.float32)

        self.prev_gray = gray

        cv2.accumulateWeighted(
            gray,
            self.background,
            0.02,
        )

        bg = cv2.convertScaleAbs(self.background)
        diff = cv2.absdiff(gray, bg)
        _, mask = cv2.threshold(
            diff,
            25,
            255,
            cv2.THRESH_BINARY,
        )
        mask = cv2.morphologyEx(
            mask,
            cv2.MORPH_OPEN,
            np.ones((3, 3), np.uint8),
        )

        contours, _ = cv2.findContours(
            mask,
            cv2.RETR_EXTERNAL,
            cv2.CHAIN_APPROX_SIMPLE,
        )

        cands = []
        for cnt in contours:
            x, y, w, h = cv2.boundingRect(cnt)
            if w * h < 16:
                continue
            cands.append(
                {
                    "bbox": [x, y, x + w, y + h],
                    "centroid": (
                        x + w / 2,
                        y + h / 2,
                    ),
                    "side_px": max(w, h),
                }
            )

        return cands, H

    def process_frame(
        self,
        frame: np.ndarray,
        cands: Optional[List[Dict[str, Any]]] = None,
        H: Optional[np.ndarray] = None,
    ) -> Tuple[np.ndarray, List[Dict[str, Any]]]:
        """
        Processes a single unified input frame matrix item.
        
        Args:
            frame: Raw BGR input frame image matrix.
            cands: Optional candidate list for legacy batch stream compatibility.
            H: Optional homography matrix for legacy batch stream compatibility.
        """
        self.frame_index += 1
        detections_this_frame = []
        vis_frame = frame.copy()

        if cands is None or H is None:
            cands, H = self._generate_candidates(frame)

        # 1. Strided YOLO Inference Execution Pipeline
        run_yolo = ((self.frame_index - 1) % self.yolo_stride) == 0
        if run_yolo:
            self.yolo_boxes = yolo_infer(self.yolo, frame, self.yolo_conf, self.yolo_imgsz, self.device_arg)
            self.n_yolo_runs += 1
        else:
            self.yolo_boxes = warp_boxes(self.yolo_boxes, H)

        # 2. Update tracking layers and analyze candidates blocks
        self.tracker.update(self.frame_index, cands, H)

        matched = [t for t in self.tracker.tracks if t.matched_now]
        probs = classify_batch(self.cls_net, frame, [t.pos for t in matched], self.device)
        for t, p in zip(matched, probs):
            t.probs.append(p)

        # 3. Dynamic Sensor Fusion Confirmation Policy Verification
        streak_floor = min(self.min_streak_boosted, self.min_streak_solo)
        for t in self.tracker.tracks:
            if t.emitted or t.hits < streak_floor or len(t.probs) < streak_floor:
                continue
                
            boosted = yolo_near_track(self.yolo_boxes, t.pos, self.yolo_agree_dist, self.yolo_conf)
            if boosted:
                eff_streak = self.min_streak_boosted
                eff_cls = self.cls_thresh_boosted
            else:
                eff_streak = self.min_streak_solo
                eff_cls = self.cls_thresh_solo

            if t.hits < eff_streak or len(t.probs) < eff_streak:
                continue
                
            mean_p = float(np.mean(t.probs))
            pos_frac = float(np.mean([p >= 0.5 for p in t.probs]))
            
            if mean_p >= eff_cls and pos_frac >= self.min_pos_frac:
                t.cls_prob = mean_p
                t.confirmed = True
                t.emitted = True
                t.yolo_boosted = boosted
                src = "tbd_boosted" if boosted else "tbd_solo"
                
                detections_this_frame.append({
                    "source": src,
                    "track_id": t.id,
                    "first_idx": t.first_idx,
                    "confirm_idx": self.frame_index,
                    "pos": [float(t.best_pos[0]), float(t.best_pos[1])],
                    "bbox": [int(v) for v in t.best_bbox],
                    "side_px": float(t.best_side),
                    "cls_prob": mean_p,
                    "pos_frac": pos_frac,
                    "hits": t.hits,
                    "yolo_boosted": boosted,
                })

        # 4. Process Standalone YOLO-Only High-Speed Alerts
        confirmed_tracks = [t for t in self.tracker.tracks if t.confirmed]
        for b in self.yolo_boxes:
            if b[4] < self.yolo_conf:
                continue
            if near_confirmed(b, confirmed_tracks, self.yolo_agree_dist):
                continue
                
            cx, cy = _center(b)
            detections_this_frame.append({
                "source": "yolo_only",
                "confirm_idx": self.frame_index,
                "pos": [float(cx), float(cy)],
                "bbox": [int(b[0]), int(b[1]), int(b[2]), int(b[3])],
                "side_px": float(max(b[2] - b[0], b[3] - b[1])),
                "yolo_conf": float(b[4]),
            })

        # 5. Apply Video HUD Annotation Overlay Graphics Layers
        for t in self.tracker.tracks:
            if t.confirmed:
                x1, y1, x2, y2 = t.best_bbox
                cv2.rectangle(vis_frame, (x1 - 4, y1 - 4), (x2 + 4, y2 + 4), (0, 0, 255), 2)
                tag = "B" if getattr(t, "yolo_boosted", False) else "S"
                label = f"TBD {tag} {t.cls_prob:.2f}"
                cv2.putText(vis_frame, label, (x1 - 4, y1 - 8), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 0, 255), 1)
                
        for b in self.yolo_boxes:
            if b[4] < self.yolo_conf:
                continue
            bx1, by1, bx2, by2 = int(b[0]), int(b[1]), int(b[2]), int(b[3])
            if near_confirmed(b, confirmed_tracks, self.yolo_agree_dist):
                cv2.rectangle(vis_frame, (bx1, by1), (bx2, by2), (255, 255, 0), 1)
            else:
                cv2.rectangle(vis_frame, (bx1, by1), (bx2, by2), (255, 0, 0), 2)
                cv2.putText(vis_frame, f"Y {b[4]:.2f}", (bx1, by1 - 4), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (255, 0, 0), 1)

        return vis_frame, detections_this_frame


# --------------------------------------------------------------------------- #
# Legacy Subprocess Batch Execution Wrapper
# --------------------------------------------------------------------------- #

def main():
    ap = argparse.ArgumentParser(description="Fused TBD-GPU + YOLO real-time detector script interface wrapper")
    ap.add_argument("--video", required=True)
    ap.add_argument("--tbd-weights", default="tbd/runs/cls_v7/best.pt")
    ap.add_argument("--yolo-weights", default="best_y11_v5.engine")
    ap.add_argument("--out", default=None)
    ap.add_argument("--max-frames", type=int, default=None)
    ap.add_argument("--start", type=int, default=0)
    ap.add_argument("--cls-thresh-solo", type=float, default=0.94)
    ap.add_argument("--cls-thresh-boosted", type=float, default=0.70)
    ap.add_argument("--min-pos-frac", type=float, default=0.6)
    ap.add_argument("--min-streak-boosted", type=int, default=3)
    ap.add_argument("--min-streak-solo", type=int, default=5)
    ap.add_argument("--link-dist", type=float, default=14.0)
    ap.add_argument("--yolo-conf", type=float, default=0.25)
    ap.add_argument("--yolo-agree-dist", type=float, default=20.0)
    ap.add_argument("--yolo-imgsz", type=int, default=1536)
    ap.add_argument("--yolo-stride", type=int, default=4)
    ap.add_argument("--gpu", action="store_true")
    ap.add_argument("--ego-downscale", type=int, default=4)
    ap.add_argument("--ego-max-features", type=int, default=None)
    ap.add_argument("--no-prefetch", action="store_true")
    ap.add_argument("--no-video", action="store_true")
    args = ap.parse_args()

    name = os.path.splitext(os.path.basename(args.video))[0]
    out_dir = args.out or os.path.join("tbd", "runs", "detect_fused", name)
    os.makedirs(out_dir, exist_ok=True)

    # Instantiate the unified class layout runner
    detector = HawkeyeDetector(args.tbd_weights, args.yolo_weights, args)

    cfg = Config()
    if args.gpu:
        stream = process_video_gpu(args.video, cfg, emit_stride=1,
                                   max_frames=args.max_frames, start=args.start,
                                   device=detector.device, ego_downscale=args.ego_downscale,
                                   ego_max_features=args.ego_max_features)
        if not args.no_prefetch:
            stream = prefetch(stream)
    else:
        stream = process_video(args.video, cfg, emit_stride=1, max_frames=args.max_frames, start=args.start)

    all_detections = []
    writer: Optional[cv2.VideoWriter] = None
    t0 = _time.perf_counter()
    nproc = 0

    for r in stream:
        nproc += 1
        # Call the standalone processing method directly
        vis, frame_dets = detector.process_frame(r["frame"], r["cands"], r["H"])
        all_detections.extend(frame_dets)

        if not args.no_video:
            if writer is None:
                h, w = r["frame"].shape[:2]
                writer = cv2.VideoWriter(os.path.join(out_dir, f"{name}_fused.mp4"),
                                         cv2.VideoWriter_fourcc(*"H264"), 30, (w, h))
            writer.write(vis)

        if nproc % 500 == 0:
            dt = _time.perf_counter() - t0
            fps = nproc / dt
            print(f"[fused] frame {nproc:5d}  {fps:.1f} fps  total_detections={len(all_detections)}")

    if writer:
        writer.release()

    dt = _time.perf_counter() - t0
    fps = nproc / dt if dt else 0.0

    # Write summary block metrics metadata matching expectations
    summary = {
        "video": args.video,
        "counts": {"total": len(all_detections)},
        "detections": all_detections[:5000]
    }
    with open(os.path.join(out_dir, "detections.json"), "w") as f:
        json.dump(summary, f, indent=2)

    print(f"Batch Processing Complete. Processed {nproc} frames at {fps:.1f} FPS.")


if __name__ == "__main__":
    main()