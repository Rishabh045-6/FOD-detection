"""
HAWKEYE FOD — GPU port of the Track-Before-Detect Stage A/B pipeline.

Drop-in for pipeline.process_video: same Config, same per-frame output contract
(idx, frame, cands, H, reg_ok, n_inliers, stack), so detect.py and the eval scorer
can switch to it with a flag. The expensive dense-array stages move to the GPU via
PyTorch, leaving the CPU only the cheap bits:

  Stage A  EgoMotion  : sparse LK optical flow stays on CPU (no good torch sparse-LK),
                        but runs on a DOWNSCALED gray (ego_downscale) since a global
                        ground homography needs no full-res detail -> ~3-4x cheaper.
  StabilizedStack     : per-frame perspective warps  -> F.grid_sample  (GPU)
                        temporal median of the stack  -> torch.median   (GPU)
  Stage B  Proposer   : multi-scale top-hat/black-hat -> max_pool2d morphology (GPU)
                        local z-score (box mean/std)   -> avg_pool2d      (GPU)
                        threshold + connected-comps    -> reuse pipeline.extract_blobs
                                                          on the downloaded z map (CPU,
                                                          ~1-2 ms; CC has no torch op).

Numerics are CLOSE but not bit-identical to the CPU path (square structuring element
vs MORPH_ELLIPSE, float vs uint8 median, replicate vs reflect borders). Re-verify the
operating point against eval/runs/144850_ground_truth before trusting the FP/recall
numbers — see eval/score_tbd_parallel.py --gpu.

Why this hits 30 fps: the CPU profile (tbd/profile_pipeline.py) spends ~88% of a
239 ms/frame budget in stacked()+propose(), both pure dense math the RTX-class GPU
runs in single-digit ms, and the frame never leaves the GPU between them.
"""
from __future__ import annotations

import os
import sys
from typing import Iterator, Optional

import dataclasses

import cv2
import numpy as np
import torch
import torch.nn.functional as F

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pipeline import Config, EgoMotion, extract_blobs, tag_pixel_locked


# --------------------------------------------------------------------------- #
# GPU morphology / box-filter primitives
# --------------------------------------------------------------------------- #
def _pad_replicate(x: torch.Tensor, p: int) -> torch.Tensor:
    return F.pad(x, (p, p, p, p), mode="replicate")


def _dilate(x: torch.Tensor, k: int) -> torch.Tensor:
    """Grayscale dilation with a k×k flat SE = max over the window. Separable: a row
    pass then a column pass give the exact k×k max at O(k) instead of O(k^2)."""
    xp = _pad_replicate(x, k // 2)
    xp = F.max_pool2d(xp, (1, k), stride=1)          # horizontal max -> width back to W
    return F.max_pool2d(xp, (k, 1), stride=1)        # vertical max   -> height back to H


def _erode(x: torch.Tensor, k: int) -> torch.Tensor:
    """Grayscale erosion = min over the window = -max(-x). Separable, replicate border."""
    xp = _pad_replicate(-x, k // 2)
    xp = F.max_pool2d(xp, (1, k), stride=1)
    return -F.max_pool2d(xp, (k, 1), stride=1)


def _box(x: torch.Tensor, k: int) -> torch.Tensor:
    """Normalized box filter (mean over k×k) with replicate border, matching
    cv2.boxFilter(normalize=True) in the interior. Separable (row mean then col mean)."""
    xp = _pad_replicate(x, k // 2)
    xp = F.avg_pool2d(xp, (1, k), stride=1)
    return F.avg_pool2d(xp, (k, 1), stride=1)


# --------------------------------------------------------------------------- #
# Stabilized stack (GPU)
# --------------------------------------------------------------------------- #
class GpuStabilizedStack:
    """GPU twin of pipeline.StabilizedStack. Holds the last N grays as [1,1,H,W]
    float32 GPU tensors and warps each onto the current frame with grid_sample,
    then takes the temporal median — all on device."""

    def __init__(self, cfg: Config, device: str):
        self.cfg = cfg
        self.device = device
        self.frames: list[torch.Tensor] = []      # [1,1,H,W] float32, oldest->newest
        self.H_pairs: list[np.ndarray] = []        # frames[i] -> frames[i+1]
        self._base: Optional[tuple] = None         # cached (xs, ys) meshgrid for (H,W)

    def push(self, gray_t: torch.Tensor, H_prev_to_cur: Optional[np.ndarray]):
        if self.frames and H_prev_to_cur is not None:
            self.H_pairs.append(H_prev_to_cur)
        elif self.frames:
            self.H_pairs.append(np.eye(3))
        self.frames.append(gray_t)
        while len(self.frames) > self.cfg.stack_size:
            self.frames.pop(0)
            self.H_pairs.pop(0)

    def _grid_for(self, Hmat: np.ndarray, H: int, W: int) -> torch.Tensor:
        """Sampling grid that pulls src pixels for each dst pixel via Hinv (Hmat maps
        src->dst, so dst(x,y) samples src at Hinv@[x,y,1]). Normalized for
        align_corners=False."""
        if self._base is None or self._base[2] != (H, W):
            ys, xs = torch.meshgrid(
                torch.arange(H, device=self.device, dtype=torch.float32),
                torch.arange(W, device=self.device, dtype=torch.float32),
                indexing="ij")
            self._base = (xs, ys, (H, W))
        xs, ys, _ = self._base
        Hinv = torch.from_numpy(np.linalg.inv(Hmat).astype(np.float32)).to(self.device)
        sx = Hinv[0, 0] * xs + Hinv[0, 1] * ys + Hinv[0, 2]
        sy = Hinv[1, 0] * xs + Hinv[1, 1] * ys + Hinv[1, 2]
        sw = Hinv[2, 0] * xs + Hinv[2, 1] * ys + Hinv[2, 2]
        sx = sx / sw
        sy = sy / sw
        gx = (sx + 0.5) * (2.0 / W) - 1.0
        gy = (sy + 0.5) * (2.0 / H) - 1.0
        return torch.stack([gx, gy], dim=-1).unsqueeze(0)   # [1,H,W,2]

    def stacked(self) -> torch.Tensor:
        """Temporal median of every buffered frame warped into current coords.
        Returns [1,1,H,W] float32 on device."""
        cur = self.frames[-1]
        _, _, H, W = cur.shape
        nold = len(self.frames) - 1
        if nold == 0:
            return cur
        # Warp all older frames in ONE batched grid_sample (N=nold) to cut launches.
        srcs = torch.cat(self.frames[:nold], dim=0)      # [nold,1,H,W]
        grids = []
        for i in range(nold):
            Hmat = np.eye(3)
            for j in range(i, len(self.H_pairs)):        # frames[i] -> ... -> current
                Hmat = self.H_pairs[j] @ Hmat
            grids.append(self._grid_for(Hmat, H, W))
        grid = torch.cat(grids, dim=0)                   # [nold,H,W,2]
        warped = F.grid_sample(srcs, grid, mode="bilinear",
                               padding_mode="border", align_corners=False)
        stack = torch.cat([cur, warped], dim=0)          # [K,1,H,W]
        med = stack.median(dim=0).values                 # [1,H,W]
        return med.unsqueeze(0)                           # [1,1,H,W]


# --------------------------------------------------------------------------- #
# Stage B proposer (GPU)
# --------------------------------------------------------------------------- #
class GpuProposer:
    """GPU twin of pipeline.Proposer. Computes the multi-scale top-hat z-score map on
    the GPU, then reuses pipeline.extract_blobs on the downloaded z (CC + shape filter
    + NMS have no GPU op and run in ~1-2 ms on the sparse mask)."""

    def __init__(self, cfg: Config, device: str):
        self.cfg = cfg
        self.device = device

    def propose(self, gray_stack: torch.Tensor) -> list[dict]:
        cfg = self.cfg
        x = gray_stack                                  # [1,1,H,W] float32
        resp = torch.zeros_like(x)
        for k in cfg.tophat_ksizes:
            opening = _dilate(_erode(x, k), k)          # erode then dilate
            closing = _erode(_dilate(x, k), k)          # dilate then erode
            wth = x - opening                           # white top-hat (bright blobs)
            bth = closing - x                           # black-hat   (dark blobs)
            resp = torch.maximum(resp, torch.maximum(wth, bth))

        win = cfg.local_win
        lm = _box(resp, win)
        lsq = _box(resp * resp, win)
        lstd = torch.sqrt(torch.clamp(lsq - lm * lm, min=0.0)) + 1e-3
        z = (resp - lm) / lstd                          # [1,1,H,W]

        z_np = z[0, 0].detach().cpu().numpy()
        return extract_blobs(z_np, cfg)


# --------------------------------------------------------------------------- #
# Ego-motion on a downscaled gray (global homography needs no full-res detail)
# --------------------------------------------------------------------------- #
class ScaledEgoMotion:
    """Runs the CPU LK ego-motion on a 1/s downscaled gray and rescales the resulting
    homography back to full resolution: H_full = S^{-1} @ H_small @ S, where S scales
    full->small. s=1 falls back to the exact full-res estimator."""

    def __init__(self, cfg: Config, downscale: int = 2,
                 max_features: Optional[int] = None):
        self.cfg = cfg
        self.s = max(1, int(downscale))
        # A global planar homography is well-determined by a few hundred inliers, so the
        # default 1200 corners is overkill; fewer corners cuts goodFeaturesToTrack+LK
        # without moving H. Override only the ego's feature cap, not the shared Config.
        ego_cfg = dataclasses.replace(cfg, max_features=max_features) if max_features else cfg
        self.ego = EgoMotion(ego_cfg)

    def estimate(self, gray_full: np.ndarray):
        if self.s == 1:
            return self.ego.estimate(gray_full)
        small = cv2.resize(gray_full, None, fx=1.0 / self.s, fy=1.0 / self.s,
                           interpolation=cv2.INTER_AREA)
        H_s, n_in, ok = self.ego.estimate(small)
        if H_s is None:
            return None, n_in, ok
        s = float(self.s)
        S = np.array([[1.0 / s, 0, 0], [0, 1.0 / s, 0], [0, 0, 1.0]])
        Sinv = np.array([[s, 0, 0], [0, s, 0], [0, 0, 1.0]])
        H_full = Sinv @ H_s @ S
        return H_full, n_in, ok


# --------------------------------------------------------------------------- #
# Streaming driver (GPU)
# --------------------------------------------------------------------------- #
def process_video_gpu(path: str, cfg: Config, emit_stride: int = 1,
                      max_frames: Optional[int] = None, start: int = 0,
                      device: Optional[str] = None, ego_downscale: int = 2,
                      ego_max_features: Optional[int] = None,
                      ) -> Iterator[dict]:
    """GPU drop-in for pipeline.process_video. Same yield dict, except 'stack' is None
    (downstream never consumes it; skipping the download saves a copy/frame)."""
    device = device or ("cuda" if torch.cuda.is_available() else "cpu")
    cap = cv2.VideoCapture(path)
    if not cap.isOpened():
        raise RuntimeError(f"cannot open {path}")
    if start:
        cap.set(cv2.CAP_PROP_POS_FRAMES, start)

    ego = ScaledEgoMotion(cfg, downscale=ego_downscale, max_features=ego_max_features)
    stack = GpuStabilizedStack(cfg, device)
    proposer = GpuProposer(cfg, device)
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

        H, n_in, reg_ok = ego.estimate(gray)
        gray_t = torch.from_numpy(gray).to(device, torch.float32).unsqueeze(0).unsqueeze(0)
        stack.push(gray_t, H if reg_ok else None)

        if (idx - start) % emit_stride == 0:
            stacked = stack.stacked()
            cands = proposer.propose(stacked)
            tag_pixel_locked(cands, gray, prev_gray, H if reg_ok else None, cfg)
            yield {"idx": idx, "frame": frame, "stack": None,
                   "cands": cands, "reg_ok": reg_ok, "n_inliers": n_in,
                   "H": H if reg_ok else None}
            n_emitted += 1
            if max_frames is not None and n_emitted >= max_frames:
                break
        prev_gray = gray
        idx += 1
    cap.release()
