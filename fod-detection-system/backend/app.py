from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from routes.detect import router as detect_router
from services.detector import FODDetector


BASE_DIR = Path(__file__).resolve().parent
UPLOAD_DIR = BASE_DIR / "uploads"
PROCESSED_DIR = BASE_DIR / "processed"
MODEL_PATH = BASE_DIR / "models" / "fod_model.pt"
CALIBRATION_PATH = BASE_DIR / "config" / "camera_calibration.json"


@asynccontextmanager
async def lifespan(app: FastAPI):
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

    detector = FODDetector(model_path=MODEL_PATH)
    detector.load()

    app.state.detector = detector
    app.state.calibration_path = CALIBRATION_PATH
    app.state.upload_dir = UPLOAD_DIR
    app.state.processed_dir = PROCESSED_DIR
    yield


app = FastAPI(
    title="IAF FOD Detection Backend",
    version="1.0.0",
    description="Camera-only FOD detection backend using FastAPI, OpenCV, and YOLO.",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/processed", StaticFiles(directory=PROCESSED_DIR), name="processed")

app.include_router(detect_router, prefix="/api")


@app.get("/health")
async def health_check() -> dict:
    return {"status": "ok"}
