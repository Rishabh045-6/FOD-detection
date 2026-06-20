from time import perf_counter
from uuid import uuid4

from fastapi import APIRouter, File, HTTPException, Request, UploadFile, status

from models.schemas import DetectResponse
from services.video_processor import VideoProcessor


router = APIRouter(tags=["detection"])


@router.post("/detect", response_model=DetectResponse)
async def detect_fod(request: Request, video: UploadFile = File(...)) -> dict:
    if not video.filename:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Missing file name")

    processor = VideoProcessor(
        detector=request.app.state.detector,
        calibration_path=request.app.state.calibration_path,
        upload_dir=request.app.state.upload_dir,
        processed_dir=request.app.state.processed_dir,
        public_processed_prefix="/processed",
    )

    job_id = uuid4().hex
    start_time = perf_counter()

    try:
        result = await processor.process_upload(video=video, job_id=job_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc)) from exc

    result["processing_time"] = round(perf_counter() - start_time, 2)
    return result
