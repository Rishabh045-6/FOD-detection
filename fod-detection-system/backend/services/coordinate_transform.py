from dataclasses import dataclass
import math
from services.calibration import CameraCalibration
from services.distance_estimator import DistanceEstimate


@dataclass(frozen=True)
class RunwayCoordinate:
    runway_x: float
    runway_y: float
    distance_m: float


import math


class CoordinateTransformer:
    def __init__(self, calibration: CameraCalibration):
        self.calibration = calibration
        
    def to_runway_coordinates(
        self,
        estimate,
        vehicle_x: float,
        vehicle_y: float,
        vehicle_yaw_deg: float,
    ):

        yaw = math.radians(vehicle_yaw_deg)

        static_x = (
            estimate.ground_x_m * math.cos(yaw)
            - estimate.ground_y_m * math.sin(yaw)
            + vehicle_x
        )

        static_y = (
            estimate.ground_x_m * math.sin(yaw)
            + estimate.ground_y_m * math.cos(yaw)
            + vehicle_y
        )

        return {
            "runway_x": static_x,
            "runway_y": static_y,
            "distance_m": estimate.distance_m,
        }