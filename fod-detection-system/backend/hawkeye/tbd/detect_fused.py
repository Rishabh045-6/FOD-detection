"""
HAWKEYE FOD — fused TBD-GPU + YOLO-v5 (SPD-Conv + NWD) detector (Option B′).

Architecture (real-time, one GPU):
  Producer thread : decode + ego-motion + GPU Stage A/B  (via prefetch queue)
  Main thread     : YOLO inference → Tracker.update → classify_batch → confirm

The two stages naturally pipeline: while main processes frame N (YOLO ~20ms), the
producer is preparing frame N+1..N+3 in the prefetch queue. On an RTX-class GPU the
effective bottleneck is Stage A/B (~33ms), not YOLO (~20ms), so throughput is close
to the standalone TBD GPU rate.

Confirm policy (Option B′: YOLO as streak booster + stricter solo bar):
  - YOLO fires within --yolo-agree-dist px of track centroid (conf >= --yolo-conf):
        effective min_streak = --min-streak-boosted   [default 3]
        effective cls_thresh = --cls-thresh-boosted   [default 0.70]
  - YOLO silent (B′ solo branch):
        effective min_streak = --min-streak-solo      [default 5]
        effective cls_thresh = --cls-thresh-solo      [default 0.94]
  The solo cls_thresh=0.94 was swept on 144850 dense GT: 9× fewer FPs at zero recall
  cost (real FOD tracks cluster at mean prob ≥0.94; FP aggregate clumps sit 0.70-0.90).

YOLO-only detections:
  Any YOLO box (conf >= --yolo-conf) whose center is NOT within --yolo-agree-dist px
  of any currently confirmed TBD track is emitted as a standalone "yolo_only" event.
  This captures medium/large FOD that TBD would take longer to confirm.

YOLO model: v5_spd_both (SPD-Conv + NWD loss, imgsz 1536, trained 2026-06-18).
  Multi-episode recall 16/21 (0.762) vs v4 11/21 (0.52); FP/neg=0.14 unchanged.
  SPDConv is auto-registered before load via _register_spdconv().

Video annotation colours:
  RED   thick  — TBD-confirmed track (any source)
  BLUE  thick  — YOLO-only detection (no overlapping confirmed TBD track)
  CYAN  thin   — YOLO box that corroborates an active TBD track (context)

Run from C:\\Apps\\Hawkeye:
  py -3.12 tbd/detect_fused.py \\
      --video recording_20250521_144850.mp4 \\
      --gpu

For faster real-time use --yolo-imgsz 1280 or 640 (cuts YOLO latency, small accuracy
loss on FOD >= 25px; tiny 15-25px FOD is handled by TBD anyway).
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time as _time
from typing import Optional

import cv2
import numpy as np
import torch

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pipeline import Config, process_video
from pipeline_gpu import process_video_gpu
from train_classifier import TinyNet, PATCH
from detect import Track, Tracker, prefetch, load_classifier, classify_batch


def _register_spdconv():
    """Register SPD-Conv (Upgrade 2) before YOLO load so SPD checkpoints unpickle.
    Guarded no-op for plain checkpoints / envs without the detection package."""
    try:
        sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        from detection.arch.hawkeye_arch import ensure_registered
        ensure_registered()
    except Exception:
        pass


# --------------------------------------------------------------------------- #
# YOLO helpers
# --------------------------------------------------------------------------- #

def load_yolo(weights: str, device_arg, imgsz: int = 1280):
    """Load YOLO weights. Accepts a .pt checkpoint OR a TensorRT .engine file —
    ultralytics dispatches to the TRT runtime transparently for .engine. The warm-up
    MUST use the deployment imgsz: a fixed-shape engine (built at a single imgsz/batch)
    rejects a mismatched input, so the old imgsz=64 dummy would crash a 1280 engine."""
    _register_spdconv()  # so SPD-Conv (Upgrade 2) checkpoints can be loaded
    from ultralytics import YOLO
    print(f"[fused] loading YOLO from {weights}")
    model = YOLO(weights)
    dummy = np.zeros((imgsz, imgsz, 3), np.uint8)
    model.predict(dummy, conf=0.05, imgsz=imgsz, device=device_arg, verbose=False)
    print(f"[fused] YOLO warm-up done (imgsz={imgsz})")
    return model


def yolo_infer(model, frame, conf_floor: float, imgsz: int, device_arg) -> list:
    """Return list of [x1, y1, x2, y2, conf] from one YOLO forward pass."""
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
    """True if any YOLO box (conf >= yolo_conf) has its center within agree_dist of pos."""
    for b in yolo_boxes:
        if b[4] < yolo_conf:
            continue
        cx, cy = _center(b)
        if _near(cx, cy, pos, agree_dist):
            return True
    return False


def near_confirmed(box, confirmed_tracks: list, agree_dist: float) -> bool:
    """True if this YOLO box center falls within agree_dist of any confirmed TBD track."""
    cx, cy = _center(box)
    for t in confirmed_tracks:
        if _near(cx, cy, t.pos, agree_dist):
            return True
    return False


def warp_boxes(boxes: list, H) -> list:
    """Forward-propagate cached YOLO boxes by one frame's ego-motion homography so a box
    detected on a YOLO frame stays spatially aligned on the strided in-between frames.

    H uses the same point-transform convention as Tracker.update (maps the previous
    frame's coords -> the current frame's), so applying the current frame's H to the
    cached boxes each non-YOLO frame walks them forward incrementally. We warp the two
    bbox corners and re-axis-align; for the near-rigid ground homography over a 1-3 frame
    stride the residual shape error is well inside --yolo-agree-dist. If H is unavailable
    (registration failed) the boxes are left as-is — better stale than discarded over a
    single frame."""
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
# Main
# --------------------------------------------------------------------------- #

def main():
    ap = argparse.ArgumentParser(
        description="Fused TBD-GPU + YOLO-v4 real-time detector (Option B)")
    ap.add_argument("--video", required=True)
    ap.add_argument("--tbd-weights", default="tbd/runs/cls_v7/best.pt")
    ap.add_argument("--yolo-weights",
                    default="best_y11_v5.engine",
                    help="YOLO weights (.pt or .engine); default = v5_spd_both TRT engine "
                         "(FP16, built @imgsz 1536 to match --yolo-imgsz). Rollback: "
                         "best_y11_v4.engine. Source .pt: "
                         "detection/runs/fod_train/v5_spd_both/weights/best.pt")
    ap.add_argument("--out", default=None,
                    help="output dir (default: tbd/runs/detect_fused/<video_name>)")
    ap.add_argument("--max-frames", type=int, default=None)
    ap.add_argument("--start", type=int, default=0)

    # TBD confirm params. Option B': the SOLO branch (no YOLO corroboration -- the
    # bulk of tracks and the source of nearly all FPs) faces a STRICTER cls bar than
    # the YOLO-corroborated branch. Solo cls 0.94 was the swept knee on the 144850
    # dense GT (eval/sweep_fused.py): 9x fewer FPs at zero recall cost. The boosted
    # branch stays easy (0.70) since YOLO agreement already vouches for it.
    ap.add_argument("--cls-thresh-solo", type=float, default=0.94,
                    help="min mean classifier prob to confirm a TBD-solo track (B')")
    ap.add_argument("--cls-thresh-boosted", type=float, default=0.70,
                    help="min mean classifier prob to confirm a YOLO-corroborated track")
    ap.add_argument("--min-pos-frac", type=float, default=0.6,
                    help="min fraction of observations with prob >= 0.5")
    ap.add_argument("--min-streak-boosted", type=int, default=3,
                    help="min_streak when YOLO corroborates the track")
    ap.add_argument("--min-streak-solo", type=int, default=5,
                    help="min_streak when YOLO is silent (TBD-only confirm)")
    ap.add_argument("--link-dist", type=float, default=14.0,
                    help="max px displacement for track association")

    # YOLO params
    ap.add_argument("--yolo-conf", type=float, default=0.25,
                    help="YOLO conf threshold for both corroboration and YOLO-only output")
    ap.add_argument("--yolo-agree-dist", type=float, default=20.0,
                    help="px radius: YOLO box center must be within this of TBD centroid")
    ap.add_argument("--yolo-imgsz", type=int, default=1536,
                    help="YOLO inference size; v5 was trained at 1536 (use 1280/640 for speed)")
    ap.add_argument("--yolo-stride", type=int, default=4,
                    help="run YOLO every N frames (Upgrade 3); cached boxes are warped "
                         "forward by ego-motion H on the in-between frames. N=1 is the "
                         "per-frame baseline. YOLO is mostly silent on tiny FOD (TBD "
                         "carries recall there), so N=2-4 cuts the consumer-thread "
                         "bottleneck at negligible accuracy cost.")

    # Pipeline
    ap.add_argument("--gpu", action="store_true",
                    help="use GPU Stage A/B pipeline (required for ~30fps)")
    ap.add_argument("--ego-downscale", type=int, default=4,
                    help="run ego-motion LK on a 1/N gray; the global ground homography "
                         "is over-determined so coarse LK is free. N=4 GT-verified safe "
                         "(2026-06-17, score_tbd_parallel --episodes): event recall "
                         "10/21 and FP 8/1.14-per-neg-frame IDENTICAL to N=2 baseline.")
    ap.add_argument("--ego-max-features", type=int, default=None)
    ap.add_argument("--no-prefetch", action="store_true",
                    help="disable producer/consumer overlap thread")
    ap.add_argument("--no-video", action="store_true", help="skip annotated mp4")
    args = ap.parse_args()

    name = os.path.splitext(os.path.basename(args.video))[0]
    out_dir = args.out or os.path.join("tbd", "runs", "detect_fused", name)
    os.makedirs(out_dir, exist_ok=True)

    device = "cuda" if torch.cuda.is_available() else "cpu"
    device_arg = 0 if device == "cuda" else "cpu"   # ultralytics wants int 0 for GPU

    print(f"[fused] device: {device}")
    cls_net = load_classifier(args.tbd_weights, device)
    yolo = load_yolo(args.yolo_weights, device_arg, args.yolo_imgsz)

    cfg = Config()
    # min_streak stored on tracker is unused in fused confirm logic (we compute
    # eff_streak per-track below); pass solo value as documentation.
    tracker = Tracker(link_dist=args.link_dist, min_streak=args.min_streak_solo)
    detections: list[dict] = []
    writer: Optional[cv2.VideoWriter] = None

    if args.gpu:
        stream = process_video_gpu(args.video, cfg, emit_stride=1,
                                   max_frames=args.max_frames, start=args.start,
                                   device=device, ego_downscale=args.ego_downscale,
                                   ego_max_features=args.ego_max_features)
        if not args.no_prefetch:
            stream = prefetch(stream)
    else:
        stream = process_video(args.video, cfg, emit_stride=1,
                               max_frames=args.max_frames, start=args.start)

    t0 = _time.perf_counter()
    nproc = 0
    yolo_boxes: list = []          # last YOLO result, warped forward between strided runs
    n_yolo_runs = 0

    for r in stream:
        frame = r["frame"]
        idx = r["idx"]
        nproc += 1

        # ── YOLO inference (Upgrade 3: strided) ──
        # Run YOLO every --yolo-stride frames in the main thread (overlaps Stage A/B in
        # the producer thread). On the in-between frames reuse the cached boxes, warped
        # forward by this frame's ego-motion H so the boost / agree / yolo_only tests
        # stay spatially valid. TBD's own tracking carries temporal integrity between runs.
        run_yolo = ((nproc - 1) % args.yolo_stride) == 0
        if run_yolo:
            yolo_boxes = yolo_infer(yolo, frame, args.yolo_conf,
                                    args.yolo_imgsz, device_arg)
            n_yolo_runs += 1
        else:
            yolo_boxes = warp_boxes(yolo_boxes, r["H"])

        # ── TBD Stage C: associate candidates, classify, confirm ──
        tracker.update(idx, r["cands"], r["H"])

        matched = [t for t in tracker.tracks if t.matched_now]
        probs = classify_batch(cls_net, frame, [t.pos for t in matched], device)
        for t, p in zip(matched, probs):
            t.probs.append(p)

        # The cheapest confirm path needs min_streak_boosted hits; no track below that
        # floor can confirm under EITHER branch. Gate on it FIRST so the per-track
        # np.mean / pos_frac / yolo_near_track work runs only for the handful of mature
        # tracks, not all ~400 live tracks every frame. That O(tracks) Python/numpy --
        # not YOLO -- was the bulk of the non-Stage-A/B fused cost (same lesson as the
        # vectorized Tracker.update). The values are only used after the streak gate, so
        # deferring them past it is behaviour-preserving.
        streak_floor = min(args.min_streak_boosted, args.min_streak_solo)
        for t in tracker.tracks:
            if t.emitted or t.hits < streak_floor or len(t.probs) < streak_floor:
                continue
            boosted = yolo_near_track(
                yolo_boxes, t.pos, args.yolo_agree_dist, args.yolo_conf)
            if boosted:
                eff_streak = args.min_streak_boosted
                eff_cls = args.cls_thresh_boosted
            else:
                eff_streak = args.min_streak_solo
                eff_cls = args.cls_thresh_solo

            if t.hits < eff_streak or len(t.probs) < eff_streak:
                continue
            mean_p = float(np.mean(t.probs))
            pos_frac = float(np.mean([p >= 0.5 for p in t.probs]))
            if mean_p >= eff_cls and pos_frac >= args.min_pos_frac:
                t.cls_prob = mean_p
                t.confirmed = True
                t.emitted = True
                t.yolo_boosted = boosted
                src = "tbd_boosted" if boosted else "tbd_solo"
                detections.append({
                    "source": src,
                    "track_id": t.id,
                    "first_idx": t.first_idx,
                    "confirm_idx": idx,
                    "pos": [float(t.best_pos[0]), float(t.best_pos[1])],
                    "bbox": [int(v) for v in t.best_bbox],
                    "side_px": float(t.best_side),
                    "cls_prob": mean_p,
                    "pos_frac": pos_frac,
                    "hits": t.hits,
                    "yolo_boosted": boosted,
                })

        # ── YOLO-only: boxes not overlapping any confirmed TBD track ──
        confirmed_tracks = [t for t in tracker.tracks if t.confirmed]
        for b in yolo_boxes:
            if b[4] < args.yolo_conf:
                continue
            if near_confirmed(b, confirmed_tracks, args.yolo_agree_dist):
                continue
            cx, cy = _center(b)
            detections.append({
                "source": "yolo_only",
                "confirm_idx": idx,
                "pos": [float(cx), float(cy)],
                "bbox": [int(b[0]), int(b[1]), int(b[2]), int(b[3])],
                "side_px": float(max(b[2] - b[0], b[3] - b[1])),
                "yolo_conf": float(b[4]),
            })

        # ── video annotation ──
        if not args.no_video:
            if writer is None:
                h, w = frame.shape[:2]
                writer = cv2.VideoWriter(
                    os.path.join(out_dir, f"{name}_fused.mp4"),
                    cv2.VideoWriter_fourcc(*"H264"), 30, (w, h))
            vis = frame.copy()
            for t in tracker.tracks:
                if t.confirmed:
                    x1, y1, x2, y2 = t.best_bbox
                    cv2.rectangle(vis, (x1 - 4, y1 - 4), (x2 + 4, y2 + 4),
                                  (0, 0, 255), 2)
                    tag = "B" if getattr(t, "yolo_boosted", False) else "S"
                    label = f"TBD {tag} {t.cls_prob:.2f}"
                    cv2.putText(vis, label, (x1 - 4, y1 - 8),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 0, 255), 1)
            for b in yolo_boxes:
                if b[4] < args.yolo_conf:
                    continue
                bx1, by1, bx2, by2 = int(b[0]), int(b[1]), int(b[2]), int(b[3])
                if near_confirmed(b, confirmed_tracks, args.yolo_agree_dist):
                    # corroborating an active TBD track — cyan thin overlay
                    cv2.rectangle(vis, (bx1, by1), (bx2, by2), (255, 255, 0), 1)
                else:
                    # YOLO-only — blue thick
                    cv2.rectangle(vis, (bx1, by1), (bx2, by2), (255, 0, 0), 2)
                    cv2.putText(vis, f"Y {b[4]:.2f}", (bx1, by1 - 4),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.45, (255, 0, 0), 1)
            writer.write(vis)

        if nproc % 500 == 0:
            dt = _time.perf_counter() - t0
            fps = nproc / dt
            n_tbd = sum(1 for d in detections if d["source"] != "yolo_only")
            n_yo = sum(1 for d in detections if d["source"] == "yolo_only")
            print(f"[fused] frame {nproc:5d}  {fps:.1f} fps  "
                  f"tbd_confirmed={n_tbd}  yolo_only_dets={n_yo}")

    if writer:
        writer.release()
    if torch.cuda.is_available():
        torch.cuda.synchronize()

    dt = _time.perf_counter() - t0
    fps = nproc / dt if dt else 0.0

    n_boosted = sum(1 for d in detections if d.get("source") == "tbd_boosted")
    n_solo    = sum(1 for d in detections if d.get("source") == "tbd_solo")
    n_yolo    = sum(1 for d in detections if d.get("source") == "yolo_only")

    summary = {
        "video": args.video,
        "tbd_weights": args.tbd_weights,
        "yolo_weights": args.yolo_weights,
        "params": {
            "cls_thresh_solo": args.cls_thresh_solo,
            "cls_thresh_boosted": args.cls_thresh_boosted,
            "min_pos_frac": args.min_pos_frac,
            "min_streak_boosted": args.min_streak_boosted,
            "min_streak_solo": args.min_streak_solo,
            "link_dist": args.link_dist,
            "yolo_conf": args.yolo_conf,
            "yolo_agree_dist": args.yolo_agree_dist,
            "yolo_imgsz": args.yolo_imgsz,
            "yolo_stride": args.yolo_stride,
            "yolo_runs": n_yolo_runs,
        },
        "counts": {
            "tbd_boosted": n_boosted,
            "tbd_solo": n_solo,
            "yolo_only": n_yolo,
            "total": len(detections),
        },
        "detections": detections[:5000],
    }
    out_json = os.path.join(out_dir, "detections.json")
    with open(out_json, "w") as f:
        json.dump(summary, f, indent=2)

    print("=" * 60)
    print(f"video            : {args.video}")
    print(f"frames           : {nproc}  @  {fps:.1f} fps")
    print(f"YOLO runs        : {n_yolo_runs}/{nproc}  (stride={args.yolo_stride})")
    print(f"TBD boosted      : {n_boosted}  (YOLO-corroborated, streak={args.min_streak_boosted})")
    print(f"TBD solo         : {n_solo}    (TBD-only, streak={args.min_streak_solo})")
    print(f"YOLO only        : {n_yolo}   (large FOD, YOLO-direct)")
    print(f"total detections : {len(detections)}")
    print(f"output           : {out_dir}")
    print("=" * 60)


if __name__ == "__main__":
    main()
