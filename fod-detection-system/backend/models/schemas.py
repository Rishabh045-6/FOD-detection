from typing import List

from pydantic import BaseModel


class RunwayCoordinates(BaseModel):
    x: float
    y: float


class DetectionResult(BaseModel):
    id: str
    frame: int
    timestamp: str
    distance_m: float
    coordinates: RunwayCoordinates
    confidence: float


class DetectResponse(BaseModel):
    status: str
    processed_video_url: str
    total_frames: int
    processing_time: float
    fod_detected: bool
    detections: List[DetectionResult]
