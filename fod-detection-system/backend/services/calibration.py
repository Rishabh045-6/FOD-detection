import json
from dataclasses import dataclass
from pathlib import Path

import numpy as np


@dataclass(frozen=True)
class CameraCalibration:
    camera_matrix: np.ndarray
    distortion_coefficients: np.ndarray
    camera_height_m: float
    camera_pitch_deg: float
    image_width: int
    image_height: int
    runway_origin_x_m: float
    runway_origin_y_m: float

    @property
    def pitch_rad(self) -> float:
        return np.deg2rad(self.camera_pitch_deg)


def load_calibration(calibration_path: Path) -> CameraCalibration:
    if not calibration_path.exists():
        raise RuntimeError(f"Calibration file not found: {calibration_path}")

    with calibration_path.open("r", encoding="utf-8") as file:
        data = json.load(file)

    try:
        return CameraCalibration(
            camera_matrix=np.asarray(data["camera_matrix"], dtype=float),
            distortion_coefficients=np.asarray(data.get("distortion_coefficients", [0, 0, 0, 0, 0]), dtype=float),
            camera_height_m=float(data["camera_height_m"]),
            camera_pitch_deg=float(data["camera_pitch_deg"]),
            image_width=int(data["image_width"]),
            image_height=int(data["image_height"]),
            runway_origin_x_m=float(data.get("runway_origin_x_m", 0.0)),
            runway_origin_y_m=float(data.get("runway_origin_y_m", 0.0)),
        )
    except KeyError as exc:
        raise RuntimeError(f"Missing calibration key: {exc.args[0]}") from exc
