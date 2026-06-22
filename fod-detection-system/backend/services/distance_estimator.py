from dataclasses import dataclass
from typing import Tuple

import math
import numpy as np

from services.calibration import CameraCalibration


@dataclass(frozen=True)
class DistanceEstimate:
    distance_m: float
    ground_x_m: float
    ground_y_m: float


class DistanceEstimator:
    def __init__(self, calibration: CameraCalibration):
        self.calibration = calibration
        self.inverse_camera_matrix = np.linalg.inv(calibration.camera_matrix)

    @staticmethod
    def _pixel_position(detection):

        pos = detection.get("pos")

        if pos and len(pos) >= 2:
            return float(pos[0]), float(pos[1])

        bbox = detection.get("bbox")

        if bbox and len(bbox) == 4:
            x1, y1, x2, y2 = bbox

            return (
                (x1 + x2) / 2,
                (y1 + y2) / 2,
            )

        raise ValueError(
            "Detection missing position"
        )

    def estimate(self, bbox_center: Tuple[float, float]) -> DistanceEstimate:
        pixel = np.array([bbox_center[0], bbox_center[1], 1.0], dtype=float)
        ray_camera = self.inverse_camera_matrix @ pixel
        ray_camera = ray_camera / np.linalg.norm(ray_camera)

        rotation = self._rotation_matrix_x(self.calibration.pitch_rad)
        ray_world = rotation @ ray_camera

        if ray_world[1] >= 0:
            raise ValueError("Bounding box center does not intersect the runway plane")

        scale = self.calibration.camera_height_m / -ray_world[1]
        ground_x = float(ray_world[0] * scale)
        ground_y = float(ray_world[2] * scale)
        distance = math.sqrt((ground_x ** 2) + (ground_y ** 2))

        return DistanceEstimate(
            distance_m=round(distance, 2),
            ground_x_m=round(ground_x, 2),
            ground_y_m=round(ground_y, 2),
        )

    @staticmethod
    def _rotation_matrix_x(angle_rad: float) -> np.ndarray:
        cosine = math.cos(angle_rad)
        sine = math.sin(angle_rad)
        return np.array(
            [
                [1.0, 0.0, 0.0],
                [0.0, cosine, -sine],
                [0.0, sine, cosine],
            ],
            dtype=float,
        )
