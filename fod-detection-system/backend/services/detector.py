from pathlib import Path
from typing import List

import numpy as np

try:
    from ultralytics import YOLO
except ImportError:  # pragma: no cover
    YOLO = None


class FODDetector:
    def __init__(self, model_path: Path, confidence_threshold: float = 0.25):
        self.model_path = model_path
        self.confidence_threshold = confidence_threshold
        self.model = None

    def load(self) -> None:
        if YOLO is None:
            raise RuntimeError("Ultralytics YOLO is not installed")
        if not self.model_path.exists():
            raise RuntimeError(f"Model file not found: {self.model_path}")
        try:
            self.model = YOLO(str(self.model_path))
        except Exception as exc:
            raise RuntimeError(f"Failed to load YOLO model: {exc}") from exc

    def predict(self, frame: np.ndarray) -> List[dict]:
        if self.model is None:
            raise RuntimeError("Model not loaded")

        results = self.model.predict(source=frame, verbose=False, conf=self.confidence_threshold)
        detections: List[dict] = []

        for result in results:
            boxes = getattr(result, "boxes", None)
            if boxes is None:
                continue
            for box in boxes:
                x1, y1, x2, y2 = box.xyxy[0].tolist()
                detections.append(
                    {
                        "bbox": [int(x1), int(y1), int(x2), int(y2)],
                        "confidence": float(box.conf[0].item()),
                    }
                )

        return detections
