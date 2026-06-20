import shutil
import subprocess
from pathlib import Path
from typing import Dict, List, Tuple

import cv2
from fastapi import UploadFile

from services.annotation import VideoAnnotator
from services.calibration import load_calibration
from services.coordinate_transform import CoordinateTransformer
from services.distance_estimator import DistanceEstimator


class VideoProcessor:
    SUPPORTED_EXTENSIONS = {".mp4", ".avi", ".mov"}

    def __init__(
        self,
        detector,
        calibration_path: Path,
        upload_dir: Path,
        processed_dir: Path,
        public_processed_prefix: str,
    ):
        self.detector = detector
        self.calibration = load_calibration(calibration_path)
        self.distance_estimator = DistanceEstimator(self.calibration)
        self.coordinate_transformer = CoordinateTransformer(self.calibration)
        self.annotator = VideoAnnotator()
        self.upload_dir = upload_dir
        self.processed_dir = processed_dir
        self.public_processed_prefix = public_processed_prefix.rstrip("/")

    async def process_upload(self, video: UploadFile, job_id: str) -> Dict:
        suffix = Path(video.filename).suffix.lower()
        if suffix not in self.SUPPORTED_EXTENSIONS:
            raise ValueError("Unsupported format. Use MP4, AVI, or MOV")

        input_path = self.upload_dir / f"{job_id}{suffix}"
        temp_output_path = self.processed_dir / f"{job_id}_raw.mp4"
        final_output_path = self.processed_dir / f"{job_id}.mp4"

        await self._save_upload(video, input_path)

        try:
            total_frames, detections = self._process_video(input_path, temp_output_path)
            self._transcode_to_mp4(temp_output_path, final_output_path)
        finally:
            await video.close()
            if temp_output_path.exists():
                temp_output_path.unlink()

        return {
            "status": "success",
            "processed_video_url": f"{self.public_processed_prefix}/{final_output_path.name}",
            "total_frames": total_frames,
            "fod_detected": bool(detections),
            "detections": detections,
        }

    async def _save_upload(self, video: UploadFile, destination: Path) -> None:
        content = await video.read()
        if not content:
            raise ValueError("Uploaded file is empty")
        destination.write_bytes(content)

    def _process_video(self, input_path: Path, output_path: Path) -> Tuple[int, List[dict]]:
        capture = cv2.VideoCapture(str(input_path))
        if not capture.isOpened():
            raise ValueError("Invalid video file")

        fps = capture.get(cv2.CAP_PROP_FPS) or 25.0
        width = int(capture.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(capture.get(cv2.CAP_PROP_FRAME_HEIGHT))
        total_frames = int(capture.get(cv2.CAP_PROP_FRAME_COUNT))

        writer = cv2.VideoWriter(
            str(output_path),
            cv2.VideoWriter_fourcc(*"mp4v"),
            fps,
            (width, height),
        )
        if not writer.isOpened():
            capture.release()
            raise RuntimeError("Failed to initialize video writer")

        detections_payload: List[dict] = []
        detection_counter = 0
        frame_number = 0

        try:
            while True:
                success, frame = capture.read()
                if not success:
                    break

                raw_detections = self.detector.predict(frame)
                frame, frame_detections, detection_counter = self._handle_frame(
                    frame=frame,
                    raw_detections=raw_detections,
                    frame_number=frame_number,
                    fps=fps,
                    detection_counter=detection_counter,
                )
                detections_payload.extend(frame_detections)
                writer.write(frame)
                frame_number += 1
        except Exception as exc:
            raise RuntimeError(f"Processing failure: {exc}") from exc
        finally:
            capture.release()
            writer.release()

        return total_frames, detections_payload

    def _handle_frame(
        self,
        frame,
        raw_detections: List[dict],
        frame_number: int,
        fps: float,
        detection_counter: int,
    ) -> Tuple[object, List[dict], int]:
        frame_detections: List[dict] = []

        for detection in raw_detections:
            x1, y1, x2, y2 = detection["bbox"]
            center_x = (x1 + x2) / 2.0
            center_y = float(y2)

            try:
                estimate = self.distance_estimator.estimate((center_x, center_y))
                runway_coordinate = self.coordinate_transformer.to_runway_coordinates(estimate)
            except ValueError:
                continue

            detection_counter += 1
            detection_id = f"FOD-{detection_counter:03d}"
            enriched_detection = {
                "id": detection_id,
                "bbox": detection["bbox"],
                "confidence": round(detection["confidence"], 4),
                "distance_m": runway_coordinate.distance_m,
                "coordinates": {
                    "x": runway_coordinate.runway_x,
                    "y": runway_coordinate.runway_y,
                },
            }
            self.annotator.annotate(frame, enriched_detection)
            frame_detections.append(
                {
                    "id": detection_id,
                    "frame": frame_number,
                    "timestamp": self._format_timestamp(frame_number, fps),
                    "distance_m": runway_coordinate.distance_m,
                    "coordinates": {
                        "x": runway_coordinate.runway_x,
                        "y": runway_coordinate.runway_y,
                    },
                    "confidence": round(detection["confidence"], 2),
                }
            )

        return frame, frame_detections, detection_counter

    @staticmethod
    def _format_timestamp(frame_number: int, fps: float) -> str:
        total_seconds = int(frame_number / fps) if fps else 0
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        seconds = total_seconds % 60
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"

    @staticmethod
    def _transcode_to_mp4(source_path: Path, destination_path: Path) -> None:
        command = [
            "ffmpeg",
            "-y",
            "-i",
            str(source_path),
            "-c:v",
            "libx264",
            "-pix_fmt",
            "yuv420p",
            str(destination_path),
        ]

        try:
            subprocess.run(command, check=True, capture_output=True, text=True)
        except FileNotFoundError:
            shutil.copyfile(source_path, destination_path)
        except subprocess.CalledProcessError as exc:
            raise RuntimeError(f"FFmpeg processing failed: {exc.stderr.strip()}") from exc
