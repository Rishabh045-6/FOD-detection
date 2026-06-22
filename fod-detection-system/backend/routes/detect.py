import asyncio
import shutil
from time import perf_counter
from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, File, HTTPException, Request, UploadFile, status
import cv2

from models.schemas import DetectResponse
from services.detector_runner import HawkeyeRunner
from services.result_parser import HawkeyeResultParser
from services.video_locator import locate_annotated_video


router = APIRouter(tags=["detection"])
SUPPORTED_EXTENSIONS = {".mp4", ".avi", ".mov"}


@router.post("/detect", response_model=DetectResponse)
async def detect_fod(request: Request, video: UploadFile = File(...)) -> dict:
    if not video.filename:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Missing file name")

    job_id = uuid4().hex
    start_time = perf_counter()
    suffix = Path(video.filename).suffix.lower()

    if suffix not in SUPPORTED_EXTENSIONS:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unsupported format. Use MP4, AVI, or MOV")

    upload_path = request.app.state.upload_dir / f"{job_id}{suffix}"
    output_dir = request.app.state.output_dir / job_id
    processed_path = request.app.state.processed_dir / f"{job_id}.mp4"
    runner = HawkeyeRunner(
        hawkeye_dir=request.app.state.hawkeye_dir,
        yolo_weights=request.app.state.hawkeye_weights,
    )
    parser = HawkeyeResultParser()

    try:
        await _save_upload(video, upload_path)
        total_frames, fps = _read_video_metadata(upload_path)
        await asyncio.to_thread(runner.run, upload_path, output_dir)

        detections_json = output_dir / "detections.json"
        detections = parser.parse(detections_json_path=detections_json, fps=fps)

        annotated_video = locate_annotated_video(output_dir)
        shutil.copy2(annotated_video, processed_path)

        result = {
            "status": "success",
            "processed_video_url": f"/processed/{processed_path.name}",
            "total_frames": total_frames,
            "fod_detected": bool(detections),
            "detections": detections,
        }
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc)) from exc
    finally:
        await video.close()

    result["processing_time"] = round(perf_counter() - start_time, 2)
    return result


async def _save_upload(video: UploadFile, destination: Path) -> None:
    content = await video.read()
    if not content:
        raise ValueError("Uploaded file is empty")
    destination.write_bytes(content)


def _read_video_metadata(video_path: Path) -> tuple[int, float]:
    capture = cv2.VideoCapture(str(video_path))
    if not capture.isOpened():
        raise ValueError("Invalid video file")

    try:
        total_frames = int(capture.get(cv2.CAP_PROP_FRAME_COUNT))
        fps = float(capture.get(cv2.CAP_PROP_FPS) or 0.0)
    finally:
        capture.release()

    return total_frames, fps
