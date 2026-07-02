import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from services.calibration import load_calibration
from services.distance_estimator import DistanceEstimator
from services.coordinate_transform import CoordinateTransformer


class HawkeyeResultParser:

    def __init__(self):
        base_dir = Path(__file__).resolve().parent.parent

        calibration = load_calibration(
            base_dir / "config" / "camera_calibration.json"
        )

        self.distance_estimator = DistanceEstimator(calibration)
        self.coordinate_transformer = CoordinateTransformer(calibration)

    @staticmethod
    def _pixel_position(
        detection: Dict[str, Any]
    ) -> Tuple[float, float]:
        pos = detection.get("pos")

        if (
            isinstance(pos, list)
            and len(pos) >= 2
        ):
            return (
                float(pos[0]),
                float(pos[1]),
            )

        bbox = detection.get("bbox")

        if (
            isinstance(bbox, list)
            and len(bbox) == 4
        ):
            x1, y1, x2, y2 = bbox

            # Fallback configuration to use object bottom-center for runway ground line estimation
            # If your distance estimator specifically requires exact center box, switch y to: (y1 + y2) / 2.0
            return (
                (x1 + x2) / 2.0,
                float(y2),
            )

        return 960.0, 540.0

    def parse_live_detection(
        self,
        index: int,
        raw_detection: Dict[str, Any],
        frame_number: int,
        fps: float,
    ) -> Dict[str, Any]:
        """
        Parses a single dynamic in-memory detection packet straight from the processing
        loop without touching or reading from the storage disk.
        """
        confidence = self._confidence(raw_detection)
        pixel_x, pixel_y = self._pixel_position(raw_detection)

        distance = None
        coord_x = None
        coord_y = None

        try:
            estimate = self.distance_estimator.estimate(
                (pixel_x, pixel_y)
            )

            distance = round(estimate.distance_m, 2)
            coord_x = round(estimate.ground_x_m, 2)
            coord_y = round(estimate.ground_y_m, 2)

        except Exception as e:
            print(
                f"[DistanceEstimator] Live Detection "
                f"{index} parsing failed: {e}"
            )

        return {
            "id": f"FOD-{index:03d}",
            "frame": frame_number,
            "timestamp": self._format_timestamp(
                frame_number,
                fps,
            ),
            "distance_m": distance,
            "coordinates": {
                "x": coord_x,
                "y": coord_y,
            },
            "confidence": confidence,
        }

    def parse(
        self,
        detections_json_path: Path,
        fps: float,
    ) -> List[Dict[str, Any]]:
        with detections_json_path.open(
            "r",
            encoding="utf-8",
        ) as handle:
            payload = json.load(handle)

        raw_detections = payload.get(
            "detections",
            [],
        )

        results: List[Dict[str, Any]] = []

        for index, detection in enumerate(
            raw_detections,
            start=1,
        ):
            frame_number = self._frame_number(detection)
            confidence = self._confidence(detection)
            pixel_x, pixel_y = self._pixel_position(detection)

            distance = None
            coord_x = None
            coord_y = None

            try:
                estimate = self.distance_estimator.estimate(
                    (pixel_x, pixel_y)
                )

                distance = round(estimate.distance_m, 2)
                coord_x = round(estimate.ground_x_m, 2)
                coord_y = round(estimate.ground_y_m, 2)

            except Exception as e:
                print(
                    f"[DistanceEstimator] Detection "
                    f"{index} failed: {e}"
                )

            results.append(
                {
                    "id": f"FOD-{index:03d}",
                    "frame": frame_number,
                    "timestamp": self._format_timestamp(
                        frame_number,
                        fps,
                    ),
                    "distance_m": distance,
                    "coordinates": {
                        "x": coord_x,
                        "y": coord_y,
                    },
                    "confidence": confidence,
                }
            )

        return results

    @staticmethod
    def _frame_number(
        detection: Dict[str, Any]
    ) -> int:
        for key in (
            "confirm_idx",
            "frame",
            "first_idx",
        ):
            value = detection.get(key)
            if value is not None:
                try:
                    return int(value)
                except (TypeError, ValueError):
                    continue
        return 0

    @staticmethod
    def _confidence(
        detection: Dict[str, Any]
    ) -> float:
        for key in (
            "yolo_conf",
            "cls_prob",
            "confidence",
        ):
            value = detection.get(key)
            if value is not None:
                try:
                    return round(
                        float(value),
                        2,
                    )
                except (TypeError, ValueError):
                    continue
        return 0.0

    @staticmethod
    def _format_timestamp(
        frame_number: int,
        fps: float,
    ) -> str:
        total_seconds = (
            int(frame_number / fps)
            if fps
            else 0
        )

        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        seconds = total_seconds % 60

        return (
            f"{hours:02d}:"
            f"{minutes:02d}:"
            f"{seconds:02d}"
        )