"""
HAWKEYE FOD — Track-Before-Detect pipeline (ISOLATED from the YOLO/PatchCore code).

This module is deliberately self-contained: it imports only cv2 + numpy and never
touches anything under detection/. It implements the cheap, causal stages of the
streaming pipeline described in the design:

  Stage A  EgoMotion   : frame-to-frame ground homography from sparse optical flow,
                         + a pixel-lock test that flags lens/sensor artifacts.
  Stage B  Proposer    : high-recall / low-precision small-blob proposer run on a
                         short sliding-window *stabilized stack* (warp the last N
                         frames onto the current one -> denoised, slightly
                         super-resolved view that buys back SNR on tiny objects).

Stage C (temporal accumulation + a learned confirm-classifier) lives elsewhere and
consumes the candidates this module emits.

Facts this is tuned to (see memory/project_hawkeye_fod.md):
  - 1920x1080, ~30 fps, moving fisheye camera over bare aggregate concrete.
  - FOD target band ~10-30 px (we propose 8-40 px to keep recall).
  - No camera calibration available -> we register in distorted image space. Over a
    short window (~5 frames / 0.16 s) the local distortion is ~affine, so a single
    homography is an adequate stabilizer. Explicit fisheye undistortion is a
    documented later upgrade (set Config.undistort_map to enable).
"""
from __future__ import annotations

import dataclasses
from dataclasses import dataclass, field
from typing import Iterator, Optional

import cv2
import numpy as np


# --------------------------------------------------------------------------- #
# Config
# --------------------------------------------------------------------------- #
@dataclass
class Config:
    # --- ground region of interest (fractions of height) ---
    # Top is sky/buildings/horizon; very bottom can be the camera body / dark corner.
    roi_y_min: float = 0.22
    roi_y_max: float = 0.97

    # --- Stage A: ego-motion ---
    max_features: int = 1200          # goodFeaturesToTrack cap
    feature_quality: float = 0.01
    feature_min_dist: int = 8
    ransac_thresh: float = 3.0        # px reprojection for findHomography RANSAC
    min_track_pts: int = 40           # below this we declare registration failed

    # --- Stage B: stabilized stack + proposer ---
    stack_size: int = 5               # frames in the sliding window (incl. current)
    # MULTI-SCALE top-hat kernels: must span the whole target band, because a
    # single small kernel only responds to features SMALLER than itself and
    # suppresses the interior of larger objects. Sizes ~ object diameters.
    tophat_ksizes: tuple = (7, 15, 31)
    # LOCAL adaptive threshold: z = (resp - local_mean) / local_std over a window,
    # fire where z > thresh_z. Local normalization stops a few very strong responses
    # (painted line, bright spots) from raising a global bar above moderate objects.
    thresh_z: float = 1.5             # high-recall operating point (Stage C filters)
    local_win: int = 65               # neighborhood for local mean/std (px)
    nms_radius: float = 12.0          # suppress duplicate candidates within this radius
    patch_for_centroid: int = 9       # local window radius used elsewhere
    min_side_px: float = 8.0          # sqrt(area) lower bound
    max_side_px: float = 40.0         # sqrt(area) upper bound
    max_aspect: float = 3.0           # reject streaks/cracks
    min_fill: float = 0.18            # blob area / bbox area (reject thin/scattered)

    # --- pixel-lock (artifact) test ---
    # A real ground point moves with H; a lens/sensor artifact stays pixel-locked.
    # We compare, at each candidate, local appearance stability vs the H-predicted
    # motion. Candidates that DON'T move with the ground are tagged 'pixel_locked'.
    pixel_lock_disp_px: float = 1.5   # if H predicts < this motion we can't judge -> unknown
    pixel_lock_ncc: float = 0.85      # NCC between cur patch and *same-pixel* prev patch

    # optional precomputed fisheye undistortion maps (map1, map2); None = skip
    undistort_map: Optional[tuple] = None


# --------------------------------------------------------------------------- #
# Stage A: ego-motion ground registration
# --------------------------------------------------------------------------- #
class EgoMotion:
    """Estimates pairwise ground homography H (prev -> cur) from sparse LK flow."""

    def __init__(self, cfg: Config):
        self.cfg = cfg
        self.prev_gray: Optional[np.ndarray] = None

    def _roi_mask(self, h: int, w: int) -> np.ndarray:
        m = np.zeros((h, w), np.uint8)
        y0 = int(self.cfg.roi_y_min * h)
        y1 = int(self.cfg.roi_y_max * h)
        m[y0:y1, :] = 255
        return m

    def estimate(self, gray: np.ndarray):
        """Return (H, n_inliers, ok). H maps prev pixel -> cur pixel."""
        cfg = self.cfg
        if self.prev_gray is None:
            self.prev_gray = gray
            return None, 0, False

        h, w = gray.shape
        mask = self._roi_mask(h, w)
        p0 = cv2.goodFeaturesToTrack(
            self.prev_gray, maxCorners=cfg.max_features,
            qualityLevel=cfg.feature_quality, minDistance=cfg.feature_min_dist,
            mask=mask)
        H, n_in, ok = None, 0, False
        if p0 is not None and len(p0) >= cfg.min_track_pts:
            p1, st, _ = cv2.calcOpticalFlowPyrLK(self.prev_gray, gray, p0, None)
            if p1 is not None:
                st = st.reshape(-1).astype(bool)
                a, b = p0.reshape(-1, 2)[st], p1.reshape(-1, 2)[st]
                if len(a) >= cfg.min_track_pts:
                    H, inl = cv2.findHomography(a, b, cv2.RANSAC, cfg.ransac_thresh)
                    if H is not None:
                        n_in = int(inl.sum())
                        ok = n_in >= cfg.min_track_pts
        self.prev_gray = gray
        return H, n_in, ok


# --------------------------------------------------------------------------- #
# Stabilized stack (sliding window warped onto the current frame)
# --------------------------------------------------------------------------- #
class StabilizedStack:
    """
    Maintains the last N grayscale frames and the chain of pairwise homographies,
    and produces a temporal median of all of them warped into the *current* frame.
    Median over registered views denoises aggregate texture flicker while preserving
    a real object that is consistently present at one ground location.
    """

    def __init__(self, cfg: Config):
        self.cfg = cfg
        self.frames: list[np.ndarray] = []   # grayscale, oldest -> newest
        self.H_pairs: list[np.ndarray] = []  # H_pairs[i] maps frames[i] -> frames[i+1]

    def push(self, gray: np.ndarray, H_prev_to_cur: Optional[np.ndarray]):
        if self.frames and H_prev_to_cur is not None:
            self.H_pairs.append(H_prev_to_cur)
        elif self.frames:                     # registration failed -> identity (no warp)
            self.H_pairs.append(np.eye(3))
        self.frames.append(gray)
        while len(self.frames) > self.cfg.stack_size:
            self.frames.pop(0)
            self.H_pairs.pop(0)

    def current(self) -> np.ndarray:
        return self.frames[-1]

    def stacked(self) -> np.ndarray:
        """Median of every buffered frame warped into the current frame's coords."""
        cur = self.frames[-1]
        h, w = cur.shape
        layers = [cur.astype(np.float32)]
        # Warp each older frame forward to current using the cumulative homography.
        for i in range(len(self.frames) - 1):
            H = np.eye(3)
            for j in range(i, len(self.H_pairs)):   # frames[i] -> ... -> current
                H = self.H_pairs[j] @ H
            warped = cv2.warpPerspective(
                self.frames[i].astype(np.float32), H, (w, h),
                flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)
            layers.append(warped)
        return np.median(np.stack(layers, 0), axis=0).astype(np.uint8)


# --------------------------------------------------------------------------- #
# Stage B: small-blob proposer
# --------------------------------------------------------------------------- #
class Proposer:
    """High-recall top-hat/black-hat blob proposer on the stabilized stack."""

    def __init__(self, cfg: Config):
        self.cfg = cfg
        self.ses = [cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (k, k))
                    for k in cfg.tophat_ksizes]

    def propose(self, gray_stack: np.ndarray) -> list[dict]:
        cfg = self.cfg
        h, w = gray_stack.shape
        # Multi-scale top-hat (bright blobs) + black-hat (dark blobs). Taking the max
        # over kernel sizes gives a response that covers the whole 8-40 px band
        # instead of only features smaller than one fixed kernel.
        resp = np.zeros((h, w), np.float32)
        for se in self.ses:
            wth = cv2.morphologyEx(gray_stack, cv2.MORPH_TOPHAT, se)
            bth = cv2.morphologyEx(gray_stack, cv2.MORPH_BLACKHAT, se)
            resp = np.maximum(resp, np.maximum(wth, bth).astype(np.float32))

        # Local z-score normalization (box-filter mean/std over local_win).
        win = (cfg.local_win, cfg.local_win)
        lm = cv2.boxFilter(resp, -1, win, normalize=True)
        lsq = cv2.boxFilter(resp * resp, -1, win, normalize=True)
        lstd = np.sqrt(np.maximum(lsq - lm * lm, 0.0)) + 1e-3
        z = (resp - lm) / lstd

        # ROI threshold -> connected components -> shape filter -> NMS.
        # Factored out so the GPU proposer (pipeline_gpu) reuses the EXACT same blob
        # extraction; only the z map upstream is computed on CPU here vs GPU there.
        return extract_blobs(z, cfg)

    def _nms(self, cands: list[dict]) -> list[dict]:
        return nms_blobs(cands, self.cfg)


def extract_blobs(z: np.ndarray, cfg: Config) -> list[dict]:
    """Threshold a z-score response map inside the ROI, connected-component it, filter
    by size/aspect/fill, and NMS. Shared by the CPU and GPU proposers.

    Vectorized: the per-component shape filter and the radius NMS run in numpy rather
    than a Python loop over (potentially thousands of) raw components, which dominated
    the per-frame cost at the high-recall operating point (~300 cands/frame)."""
    h, w = z.shape
    y0, y1 = int(cfg.roi_y_min * h), int(cfg.roi_y_max * h)
    # CC only the ROI band (the rest is zero anyway); add y0 back to y coords.
    band = (z[y0:y1, :] > cfg.thresh_z).astype(np.uint8)
    n, _, stats, cent = cv2.connectedComponentsWithStats(band, connectivity=8)
    if n <= 1:
        return []
    st = stats[1:].astype(np.float64)               # drop background label 0
    ce = cent[1:].copy(); ce[:, 1] += y0
    bx = st[:, 0]; by = st[:, 1] + y0
    bw = st[:, 2]; bh = st[:, 3]; area = st[:, 4]
    side = np.sqrt(bw * bh)
    asp = np.maximum(bw, bh) / np.maximum(1.0, np.minimum(bw, bh))
    fill = area / (bw * bh)
    keep = ((side >= cfg.min_side_px) & (side <= cfg.max_side_px) &
            (asp <= cfg.max_aspect) & (fill >= cfg.min_fill))
    if not keep.any():
        return []
    bx = bx[keep]; by = by[keep]; bw = bw[keep]; bh = bh[keep]; side = side[keep]
    cx = ce[keep, 0]; cy = ce[keep, 1]
    scores = z[np.clip(cy.astype(int), 0, h - 1), np.clip(cx.astype(int), 0, w - 1)]

    # Greedy radius NMS: keep strongest, suppress within nms_radius. Preallocated
    # kept buffer (no per-step realloc) keeps this well under a ms at ~300 cands.
    order = np.argsort(-scores)
    r2 = cfg.nms_radius ** 2
    m = order.shape[0]
    kx = np.empty(m, np.float64); ky = np.empty(m, np.float64); nk = 0
    kept = []
    for j in order:
        px = cx[j]; py = cy[j]
        if nk and ((kx[:nk] - px) ** 2 + (ky[:nk] - py) ** 2).min() <= r2:
            continue
        kx[nk] = px; ky[nk] = py; nk += 1
        kept.append({
            "bbox": [int(bx[j]), int(by[j]), int(bx[j] + bw[j]), int(by[j] + bh[j])],
            "centroid": [float(px), float(py)],
            "side_px": float(side[j]),
            "score": float(scores[j]),
        })
    return kept


def nms_blobs(cands: list[dict], cfg: Config) -> list[dict]:
    """Greedy radius NMS over a list of candidate dicts (kept for callers that work
    with dicts; extract_blobs does its NMS on arrays directly)."""
    r2 = cfg.nms_radius ** 2
    kept = []
    for c in sorted(cands, key=lambda d: -d["score"]):
        cx, cy = c["centroid"]
        if all((cx - k["centroid"][0]) ** 2 + (cy - k["centroid"][1]) ** 2 > r2
               for k in kept):
            kept.append(c)
    return kept


# --------------------------------------------------------------------------- #
# Pixel-lock (artifact) test
# --------------------------------------------------------------------------- #
def _ncc(a: np.ndarray, b: np.ndarray) -> float:
    a = a.astype(np.float32) - a.mean()
    b = b.astype(np.float32) - b.mean()
    d = np.sqrt((a * a).sum() * (b * b).sum())
    return float((a * b).sum() / d) if d > 1e-6 else 0.0


def tag_pixel_locked(cands: list[dict], cur_gray: np.ndarray,
                     prev_gray: Optional[np.ndarray],
                     H_prev_to_cur: Optional[np.ndarray], cfg: Config) -> None:
    """
    Mark each candidate 'pixel_locked' = True if it stays correlated with the SAME
    pixel location in the previous frame even though H predicts the ground moved
    there. Such things are lens/sensor artifacts, not objects on the ground.
    Adds keys: 'pixel_locked' (bool|None) and 'ground_disp_px'.
    """
    for c in cands:
        c["pixel_locked"] = None
        c["ground_disp_px"] = None
    if prev_gray is None or H_prev_to_cur is None:
        return
    h, w = cur_gray.shape
    Hinv = np.linalg.inv(H_prev_to_cur)
    r = max(4, cfg.patch_for_centroid)
    for c in cands:
        cx, cy = c["centroid"]
        # Where did this ground point come from in the previous frame?
        src = Hinv @ np.array([cx, cy, 1.0])
        src = src[:2] / src[2]
        disp = float(np.hypot(cx - src[0], cy - src[1]))
        c["ground_disp_px"] = disp
        if disp < cfg.pixel_lock_disp_px:
            continue  # camera barely moved here -> can't judge
        xi, yi = int(round(cx)), int(round(cy))
        if not (r <= xi < w - r and r <= yi < h - r):
            continue
        cur_patch = cur_gray[yi - r:yi + r, xi - r:xi + r]
        # If it's pixel-locked, the SAME pixel window in prev still matches it.
        prev_patch_same = prev_gray[yi - r:yi + r, xi - r:xi + r]
        c["pixel_locked"] = _ncc(cur_patch, prev_patch_same) >= cfg.pixel_lock_ncc


# --------------------------------------------------------------------------- #
# Top-level streaming driver
# --------------------------------------------------------------------------- #
def process_video(path: str, cfg: Config, emit_stride: int = 1,
                  max_frames: Optional[int] = None,
                  start: int = 0) -> Iterator[dict]:
    """
    Reads EVERY frame so ego-motion / stack stay continuous (optical flow needs
    small inter-frame motion), but only runs the proposer and yields a result every
    `emit_stride` frames (avoids harvesting near-duplicate crops).

    Yields one dict per *emitted* frame:
      { 'idx', 'frame'(BGR), 'stack'(gray), 'cands'(list), 'reg_ok', 'n_inliers' }
    `max_frames` counts emitted frames.
    """
    cap = cv2.VideoCapture(path)
    if not cap.isOpened():
        raise RuntimeError(f"cannot open {path}")
    if start:
        cap.set(cv2.CAP_PROP_POS_FRAMES, start)

    ego = EgoMotion(cfg)
    stack = StabilizedStack(cfg)
    proposer = Proposer(cfg)
    prev_gray = None
    idx = start
    n_emitted = 0
    while True:
        ok, frame = cap.read()
        if not ok:
            break
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        if cfg.undistort_map is not None:
            m1, m2 = cfg.undistort_map
            gray = cv2.remap(gray, m1, m2, cv2.INTER_LINEAR)
            frame = cv2.remap(frame, m1, m2, cv2.INTER_LINEAR)

        # ego-motion + stack updated on EVERY frame (continuity)
        H, n_in, reg_ok = ego.estimate(gray)
        stack.push(gray, H if reg_ok else None)

        if (idx - start) % emit_stride == 0:
            stacked = stack.stacked()
            cands = proposer.propose(stacked)
            tag_pixel_locked(cands, gray, prev_gray, H if reg_ok else None, cfg)
            yield {"idx": idx, "frame": frame, "stack": stacked,
                   "cands": cands, "reg_ok": reg_ok, "n_inliers": n_in,
                   "H": H if reg_ok else None}
            n_emitted += 1
            if max_frames is not None and n_emitted >= max_frames:
                break
        prev_gray = gray
        idx += 1
    cap.release()


def config_to_dict(cfg: Config) -> dict:
    d = dataclasses.asdict(cfg)
    d.pop("undistort_map", None)
    return d
