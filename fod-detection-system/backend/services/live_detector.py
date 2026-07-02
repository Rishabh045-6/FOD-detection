from __future__ import annotations

import cv2
from typing import Dict, Any, List, Tuple

import numpy as np

from hawkeye.tbd.detect_fused import HawkeyeDetector


class LiveDetector:

    def __init__(
        self,
        tbd_weights: str,
        yolo_weights: str,
    ):

        self.detector = HawkeyeDetector(
            tbd_weights=tbd_weights,
            yolo_weights=yolo_weights,
        )

    def process_frame(
        self,
        frame: np.ndarray,
    ) -> Tuple[np.ndarray, List[Dict[str, Any]], bool]:

        annotated, detections = self.detector.process_frame(
            frame
        )

        return (
            annotated,
            detections,
            len(detections) > 0,
        )