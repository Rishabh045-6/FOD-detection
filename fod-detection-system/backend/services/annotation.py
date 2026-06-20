from typing import Dict

import cv2
import numpy as np


class VideoAnnotator:
    BOX_COLOR = (0, 0, 255)
    TEXT_COLOR = (255, 255, 255)
    BACKGROUND_COLOR = (0, 0, 180)

    def annotate(self, frame: np.ndarray, detection: Dict) -> np.ndarray:
        x1, y1, x2, y2 = detection["bbox"]
        label = f"{detection['id']} | {detection['distance_m']:.1f}m | {round(detection['confidence'] * 100):d}%"

        cv2.rectangle(frame, (x1, y1), (x2, y2), self.BOX_COLOR, 2)

        (text_width, text_height), baseline = cv2.getTextSize(
            label, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2
        )
        top = max(0, y1 - text_height - baseline - 8)
        cv2.rectangle(
            frame,
            (x1, top),
            (x1 + text_width + 10, top + text_height + baseline + 8),
            self.BACKGROUND_COLOR,
            -1,
        )
        cv2.putText(
            frame,
            label,
            (x1 + 5, top + text_height + 2),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            self.TEXT_COLOR,
            2,
            cv2.LINE_AA,
        )
        return frame
