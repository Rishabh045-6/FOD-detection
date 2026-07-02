"""
Reusable Hawkeye detector.

This class contains EVERYTHING needed to process either

- one frame (live)
- an entire video (offline)

without duplicating the pipeline.

Both detect_fused.py and LiveDetector will simply create ONE instance
of this class and reuse it.
"""

from __future__ import annotations

import sys
import os
from typing import Optional

import cv2
import numpy as np
import torch

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from pipeline import (
    Config,
    EgoMotion,
    StabilizedStack,
    Proposer,
)

from pipeline_gpu import (
    GpuStabilizedStack,
    GpuProposer,
)

from detect import (
    Tracker,
    load_classifier,
    classify_batch,
)

# ----------------------------------------------------------------------
# SPD Registration
# ----------------------------------------------------------------------


def register_spdconv():

    try:

        sys.path.insert(
            0,
            os.path.dirname(
                os.path.dirname(
                    os.path.abspath(__file__)
                )
            ),
        )

        from detection.arch.hawkeye_arch import ensure_registered

        ensure_registered()

    except Exception:

        pass


# ----------------------------------------------------------------------
# YOLO Loader
# ----------------------------------------------------------------------


def load_yolo(weights, device, imgsz):

    register_spdconv()

    from ultralytics import YOLO

    print(f"[hawkeye] loading {weights}")

    model = YOLO(weights)

    dummy = np.zeros((imgsz, imgsz, 3), np.uint8)

    model.predict(
        dummy,
        imgsz=imgsz,
        conf=0.05,
        device=device,
        verbose=False,
    )

    print("[hawkeye] warmup complete")

    return model


# ----------------------------------------------------------------------
# Detector
# ----------------------------------------------------------------------


class HawkeyeDetector:

    def __init__(

        self,

        tbd_weights,

        yolo_weights,

        use_gpu=True,

        yolo_imgsz=640,

        yolo_stride=4,

        yolo_conf=0.25,

        yolo_agree_dist=20,

        link_dist=14,

        cls_thresh_solo=0.94,

        cls_thresh_boosted=0.70,

        min_pos_frac=0.60,

        min_streak_solo=5,

        min_streak_boosted=3,

    ):

        self.device = (
            "cuda"
            if torch.cuda.is_available() and use_gpu
            else "cpu"
        )

        self.device_arg = (
            0
            if self.device == "cuda"
            else "cpu"
        )

        self.cfg = Config()

        # ---------- Stage A/B state ----------
        self.prev_gray = None
        self.prev_pts = None
        self.H = np.eye(3, dtype=np.float32)

        # background model
        self.background = None

        # frame counter
        self.stage_frame = 0

        # -----------------------------
        # Stage A/B
        # -----------------------------

        if self.device == "cuda":

            self.stack = GpuStabilizedStack(
                self.cfg,
                self.device,
            )

            self.proposer = GpuProposer(
                self.cfg,
                self.device,
            )

        else:

            self.stack = StabilizedStack(
                self.cfg
            )

            self.proposer = Proposer(
                self.cfg
            )

        self.ego = EgoMotion(self.cfg)

        # -----------------------------
        # Networks
        # -----------------------------

        self.cls_net = load_classifier(
            tbd_weights,
            self.device,
        )

        self.yolo = load_yolo(
            yolo_weights,
            self.device_arg,
            yolo_imgsz,
        )

        # -----------------------------
        # Tracker
        # -----------------------------

        self.tracker = Tracker(
            link_dist=link_dist,
            min_streak=min_streak_solo,
        )

        # -----------------------------
        # Parameters
        # -----------------------------

        self.yolo_stride = yolo_stride
        self.yolo_imgsz = yolo_imgsz
        self.yolo_conf = yolo_conf
        self.yolo_agree_dist = yolo_agree_dist

        self.cls_thresh_solo = cls_thresh_solo
        self.cls_thresh_boosted = cls_thresh_boosted

        self.min_pos_frac = min_pos_frac

        self.min_streak_solo = min_streak_solo
        self.min_streak_boosted = min_streak_boosted

        # -----------------------------
        # Runtime State
        # -----------------------------

        self.frame_index = 0

        self.yolo_boxes = []

        self.prev_gray = None

        self.n_yolo_runs = 0

    def _generate_candidates(self, frame):
        """
        Execute Stage A/B on ONE frame.

        Returns
        -------
        cands : list
        H : homography
        """

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        # first frame
        if self.prev_gray is None:

            self.prev_gray = gray

            self.background = gray.astype(np.float32)

            return [], np.eye(3, dtype=np.float32)

        # ------------------------------------------------
        # Ego Motion
        # ------------------------------------------------

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

        # ------------------------------------------------
        # Background Update
        # ------------------------------------------------

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