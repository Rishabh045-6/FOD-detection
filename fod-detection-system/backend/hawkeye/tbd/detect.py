"""
Stage C end-to-end: Stage A/B candidates -> track-before-detect persistence ->
tiny CNN confirm. Emits a FOD detection only when a candidate (a) persists at the
same GROUND location across K frames (associated via the ego-motion homography) and
(b) the classifier confirms the object on its best observation.

Run from C:\\Apps\\Hawkeye:
  # precision check on FOD-free footage (target: ~0 confirmed detections)
  py -3.12 tbd/detect.py --video clean1.mp4 --weights tbd/runs/cls/best.pt --max-frames 1500
  # behavior on a real test recording
  py -3.12 tbd/detect.py --video recording_20250521_144850.mp4 --weights tbd/runs/cls/best.pt
"""
from __future__ import annotations

import argparse
import json
import os
import queue
import sys
import threading

import cv2
import numpy as np
import torch

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pipeline import Config, process_video
from pipeline_gpu import process_video_gpu
from train_classifier import TinyNet, PATCH


# --------------------------------------------------------------------------- #
# Track-before-detect
# --------------------------------------------------------------------------- #
class Track:
    _next = 0

    def __init__(self, idx, pos, bbox):
        self.id = Track._next; Track._next += 1
        self.pos = np.array(pos, np.float32)     # last pixel position
        self.hits = 1
        self.misses = 0
        self.matched_now = True                  # got a candidate this frame
        self.best_side = (bbox[2] - bbox[0] + bbox[3] - bbox[1]) / 2.0
        self.best_bbox = bbox
        self.best_pos = np.array(pos, np.float32)
        self.probs = []                          # classifier prob per observation
        self.cls_prob = None                     # aggregate (mean) prob
        self.confirmed = False
        self.emitted = False
        self.first_idx = idx
        self.last_idx = idx


class Tracker:
    def __init__(self, link_dist=14.0, min_streak=4, max_misses=3):
        self.link_dist = link_dist
        self.min_streak = min_streak
        self.max_misses = max_misses
        self.tracks: list[Track] = []

    def update(self, idx, cands, H):
        # Vectorized track-priority greedy NN association. Semantics are identical to
        # the old per-(track,cand) Python double loop (iterate tracks in list order,
        # each claims its nearest still-free candidate within link_dist), but the
        # distance math is one numpy matrix instead of ~T*C interpreted iterations --
        # at the high-recall operating point (T~400, C~300) that loop was ~120 ms/frame.
        T = len(self.tracks)
        C = len(cands)
        # float64 here matches the original per-track math (H is float64 from cv2;
        # prediction divides in float64 then casts to float32) so associations -- and
        # thus confirmed-track counts -- are bit-for-bit the same as the scalar loop.
        cent = (np.array([c["centroid"] for c in cands], np.float64)
                if C else np.zeros((0, 2), np.float64))
        used = np.zeros(C, bool)

        if T:
            pos = np.array([t.pos for t in self.tracks], np.float64)        # [T,2]
            if H is not None:
                ph = np.c_[pos, np.ones(T)] @ np.asarray(H, np.float64).T
                pred = (ph[:, :2] / ph[:, 2:3]).astype(np.float32)
            else:
                pred = pos.astype(np.float32)
            if C:
                # [T,C] euclidean distances track-pred -> candidate (np.hypot to match
                # the original's per-pair hypot to the ULP -> identical associations)
                diff = pred[:, None, :] - cent[None, :, :]
                d = np.hypot(diff[:, :, 0], diff[:, :, 1])
                for i, t in enumerate(self.tracks):
                    row = np.where(used, np.inf, d[i])
                    j = int(row.argmin())
                    if row[j] < self.link_dist:
                        used[j] = True
                        c = cands[j]
                        t.pos = cent[j].astype(np.float32)
                        t.hits += 1; t.misses = 0; t.last_idx = idx; t.matched_now = True
                        if c["side_px"] >= t.best_side:    # keep the largest (closest) view
                            t.best_side = c["side_px"]; t.best_bbox = c["bbox"]
                            t.best_pos = cent[j].astype(np.float32)
                    else:
                        t.matched_now = False; t.misses += 1
            else:
                for t in self.tracks:
                    t.matched_now = False; t.misses += 1

        # spawn tracks for unmatched candidates (skip pixel-locked artifacts)
        for j, c in enumerate(cands):
            if used[j] or c.get("pixel_locked"):
                continue
            self.tracks.append(Track(idx, c["centroid"], c["bbox"]))

        # retire stale tracks
        self.tracks = [t for t in self.tracks if t.misses <= self.max_misses]


# --------------------------------------------------------------------------- #
_SENTINEL = object()


def prefetch(gen, size=4):
    """Run `gen` on a background thread feeding a bounded queue, so the producer
    (decode + ego-motion + GPU Stage A/B) overlaps with the consumer (tracker +
    classifier) instead of running serially. The two stages are mostly on different
    hardware -- A/B is CPU-heavy (LK + connected-components) plus some GPU, the
    classifier is GPU -- so overlapping them recovers most of the smaller stage's time.
    """
    q = queue.Queue(maxsize=size)

    def worker():
        try:
            for item in gen:
                q.put(item)
        except Exception as e:                  # surface producer errors to consumer
            q.put(("__err__", e))
        finally:
            q.put(_SENTINEL)

    threading.Thread(target=worker, daemon=True).start()
    while True:
        item = q.get()
        if item is _SENTINEL:
            break
        if isinstance(item, tuple) and len(item) == 2 and item[0] == "__err__":
            raise item[1]
        yield item


def load_classifier(weights, device):
    ck = torch.load(weights, map_location=device)
    net = TinyNet().to(device); net.load_state_dict(ck["state_dict"]); net.eval()
    return net


def _extract(frame, pos):
    h, w = frame.shape[:2]
    half = PATCH // 2
    x0 = int(np.clip(pos[0] - half, 0, w - PATCH))
    y0 = int(np.clip(pos[1] - half, 0, h - PATCH))
    patch = frame[y0:y0 + PATCH, x0:x0 + PATCH]
    if patch.shape[:2] != (PATCH, PATCH):
        return None
    return cv2.cvtColor(patch, cv2.COLOR_BGR2RGB).astype(np.float32) / 255.0


def classify_patch(net, frame, pos, device):
    rgb = _extract(frame, pos)
    if rgb is None:
        return 0.0
    t = torch.from_numpy(rgb.transpose(2, 0, 1)[None]).to(device)
    with torch.no_grad():
        return float(net(t).softmax(1)[0, 1].cpu())


def classify_batch(net, frame, positions, device):
    """Classify many positions in one forward pass. Returns list of probs.

    Patch extraction is vectorized: slice each PATCHxPATCH crop (cheap), then do the
    BGR->RGB flip + transpose + scale ONCE on the stacked batch instead of a per-patch
    cv2.cvtColor (that Python loop was ~6 ms/frame at ~300 tracks)."""
    out = [0.0] * len(positions)
    if not positions:
        return out
    h, w = frame.shape[:2]
    half = PATCH // 2
    patches, valid = [], []
    for i, p in enumerate(positions):
        x0 = int(np.clip(p[0] - half, 0, w - PATCH))
        y0 = int(np.clip(p[1] - half, 0, h - PATCH))
        patch = frame[y0:y0 + PATCH, x0:x0 + PATCH]
        if patch.shape[:2] == (PATCH, PATCH):
            patches.append(patch); valid.append(i)
    if patches:
        # Upload raw uint8 BGR patches and do the BGR->RGB flip + NCHW transpose + /255
        # on the GPU. The CPU equivalent (negative-stride flip + ascontiguousarray +
        # float cast) was ~3.3 ms/frame at ~300 patches -- the dominant classify cost,
        # bigger than the TinyNet forward itself. The result is numerically identical.
        arr = np.stack(patches)                            # [N,P,P,3] uint8 BGR (cheap)
        t = torch.from_numpy(arr).to(device)               # uint8 on device
        t = t.permute(0, 3, 1, 2).float().div_(255.0)      # [N,3,P,P] BGR float
        t = t[:, [2, 1, 0]]                                # BGR -> RGB on device
        with torch.no_grad():
            pr = net(t).softmax(1)[:, 1].cpu().numpy()
        for k, i in enumerate(valid):
            out[i] = float(pr[k])
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--video", required=True)
    ap.add_argument("--weights", default="tbd/runs/cls/best.pt")
    ap.add_argument("--out", default=None)
    ap.add_argument("--max-frames", type=int, default=None)
    ap.add_argument("--start", type=int, default=0)
    ap.add_argument("--cls-thresh", type=float, default=0.7,
                    help="min MEAN classifier prob over a track's observations")
    ap.add_argument("--min-pos-frac", type=float, default=0.6,
                    help="min fraction of observations with prob>=0.5")
    ap.add_argument("--min-streak", type=int, default=5)
    ap.add_argument("--link-dist", type=float, default=14.0)
    ap.add_argument("--no-video", action="store_true", help="skip annotated mp4")
    ap.add_argument("--gpu", action="store_true",
                    help="use the GPU Stage A/B pipeline (pipeline_gpu) for 30-fps")
    ap.add_argument("--ego-downscale", type=int, default=2,
                    help="(--gpu) run ego-motion LK on a 1/N gray; global H needs no full res")
    ap.add_argument("--no-prefetch", action="store_true",
                    help="(--gpu) disable the producer/consumer overlap thread")
    ap.add_argument("--ego-max-features", type=int, default=None,
                    help="(--gpu) cap ego-motion corners (default 1200); ~600 is plenty "
                         "for a global homography and cuts goodFeaturesToTrack+LK")
    ap.add_argument("--dump-fp", default=None,
                    help="dir to save best-patch of each confirmed detection "
                         "(hard negatives when run on FOD-free footage)")
    args = ap.parse_args()
    if args.dump_fp:
        os.makedirs(args.dump_fp, exist_ok=True)

    name = os.path.splitext(os.path.basename(args.video))[0]
    out_dir = args.out or os.path.join("tbd/runs/detect", name)
    os.makedirs(out_dir, exist_ok=True)
    device = "cuda" if torch.cuda.is_available() else "cpu"
    net = load_classifier(args.weights, device)

    cfg = Config()
    tracker = Tracker(link_dist=args.link_dist, min_streak=args.min_streak)
    detections = []           # confirmed FOD events
    writer = None

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
    import time as _time
    _t0 = _time.perf_counter(); _nproc = 0
    for r in stream:
        frame = r["frame"]; idx = r["idx"]
        _nproc += 1
        tracker.update(idx, r["cands"], r["H"])
        # Classify (batched) the current observation of every track matched this
        # frame, then confirm only on SUSTAINED evidence: enough hits AND a high mean
        # prob AND most observations positive. Aggregate clumps may fool the net from
        # one angle, not from many -> temporal integration of the classifier.
        matched = [t for t in tracker.tracks if t.matched_now]
        probs = classify_batch(net, frame, [t.pos for t in matched], device)
        for t, p in zip(matched, probs):
            t.probs.append(p)
        for t in tracker.tracks:
            if t.emitted or t.hits < args.min_streak or len(t.probs) < args.min_streak:
                continue
            mean_p = float(np.mean(t.probs))
            pos_frac = float(np.mean([p >= 0.5 for p in t.probs]))
            if mean_p >= args.cls_thresh and pos_frac >= args.min_pos_frac:
                t.cls_prob = mean_p; t.confirmed = True; t.emitted = True
                if args.dump_fp:
                    h, w = frame.shape[:2]; half = PATCH // 2
                    x0 = int(np.clip(t.best_pos[0] - half, 0, w - PATCH))
                    y0 = int(np.clip(t.best_pos[1] - half, 0, h - PATCH))
                    cv2.imwrite(os.path.join(args.dump_fp,
                                f"fp_{idx:06d}_{t.id}.png"),
                                frame[y0:y0 + PATCH, x0:x0 + PATCH])
                detections.append({
                    "track_id": t.id, "first_idx": t.first_idx, "confirm_idx": idx,
                    "pos": [float(t.best_pos[0]), float(t.best_pos[1])],
                    "bbox": [int(v) for v in t.best_bbox],
                    "side_px": float(t.best_side), "cls_prob": mean_p,
                    "pos_frac": pos_frac, "hits": t.hits,
                })

        if not args.no_video:
            if writer is None:
                h, w = frame.shape[:2]
                writer = cv2.VideoWriter(os.path.join(out_dir, f"{name}_tbd.mp4"),
                                         cv2.VideoWriter_fourcc(*"H264"), 30, (w, h))
            vis = frame.copy()
            for t in tracker.tracks:
                if t.confirmed:
                    x1, y1, x2, y2 = t.best_bbox
                    cv2.rectangle(vis, (x1 - 4, y1 - 4), (x2 + 4, y2 + 4), (0, 0, 255), 2)
                    cv2.putText(vis, f"FOD {t.cls_prob:.2f}", (x1 - 4, y1 - 8),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 1)
            writer.write(vis)
    if writer:
        writer.release()
    if torch.cuda.is_available():
        torch.cuda.synchronize()
    _dt = _time.perf_counter() - _t0
    _fps = _nproc / _dt if _dt else 0.0
    print(f"end-to-end: {_nproc} frames in {_dt:.1f}s -> {_fps:.1f} fps "
          f"({'GPU A/B' if args.gpu else 'CPU A/B'}"
          f"{', video-write ON' if not args.no_video else ''})")

    summary = {
        "video": args.video, "weights": args.weights,
        "params": {"cls_thresh": args.cls_thresh, "min_streak": args.min_streak,
                   "link_dist": args.link_dist},
        "confirmed_detections": len(detections),
        "unique_tracks_confirmed": len({d["track_id"] for d in detections}),
        "detections": detections[:500],
    }
    with open(os.path.join(out_dir, "detections.json"), "w") as f:
        json.dump(summary, f, indent=2)
    print("=" * 60)
    print(f"video                 : {args.video}")
    print(f"CONFIRMED detections  : {len(detections)}  "
          f"(unique tracks {summary['unique_tracks_confirmed']})")
    print(f"output                : {out_dir}")
    print("=" * 60)


if __name__ == "__main__":
    main()
