import json
from pathlib import Path
from typing import Any, Dict, List


class HawkeyeResultParser:
    def parse(self, detections_json_path: Path, fps: float) -> List[Dict[str, Any]]:
        with detections_json_path.open("r", encoding="utf-8") as handle:
            payload = json.load(handle)

        raw_detections = payload.get("detections", [])
        results: List[Dict[str, Any]] = []

        for index, detection in enumerate(raw_detections, start=1):
            frame_number = self._frame_number(detection)
            confidence = self._confidence(detection)
            results.append(
                {
                    "id": f"FOD-{index:03d}",
                    "frame": frame_number,
                    "timestamp": self._format_timestamp(frame_number, fps),
                    "distance_m": None,
                    "coordinates": {
                        "x": None,
                        "y": None,
                    },
                    "confidence": confidence,
                }
            )

        return results

    @staticmethod
    def _frame_number(detection: Dict[str, Any]) -> int:
        for key in ("confirm_idx", "frame", "first_idx"):
            value = detection.get(key)
            if value is not None:
                try:
                    return int(value)
                except (TypeError, ValueError):
                    continue
        return 0

    @staticmethod
    def _confidence(detection: Dict[str, Any]) -> float:
        for key in ("yolo_conf", "cls_prob", "confidence"):
            value = detection.get(key)
            if value is not None:
                try:
                    return round(float(value), 2)
                except (TypeError, ValueError):
                    continue
        return 0.0

    @staticmethod
    def _format_timestamp(frame_number: int, fps: float) -> str:
        total_seconds = int(frame_number / fps) if fps else 0
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        seconds = total_seconds % 60
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
