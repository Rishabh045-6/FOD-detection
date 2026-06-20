from dataclasses import dataclass

from services.calibration import CameraCalibration
from services.distance_estimator import DistanceEstimate


@dataclass(frozen=True)
class RunwayCoordinate:
    runway_x: float
    runway_y: float
    distance_m: float


class CoordinateTransformer:
    def __init__(self, calibration: CameraCalibration):
        self.calibration = calibration

    def to_runway_coordinates(self, estimate: DistanceEstimate) -> RunwayCoordinate:
        return RunwayCoordinate(
            runway_x=round(self.calibration.runway_origin_x_m + estimate.ground_x_m, 2),
            runway_y=round(self.calibration.runway_origin_y_m + estimate.ground_y_m, 2),
            distance_m=estimate.distance_m,
        )
