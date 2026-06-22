from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from routes.detect import router as detect_router


BASE_DIR = Path(__file__).resolve().parent
UPLOAD_DIR = BASE_DIR / "uploads"
OUTPUT_DIR = BASE_DIR / "outputs"
PROCESSED_DIR = BASE_DIR / "processed"
HAWKEYE_DIR = BASE_DIR / "hawkeye"
HAWKEYE_WEIGHTS = HAWKEYE_DIR / "detection" / "runs" / "fod_train" / "v5_spd_both" / "weights" / "best.pt"


@asynccontextmanager
async def lifespan(app: FastAPI):
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

    app.state.upload_dir = UPLOAD_DIR
    app.state.output_dir = OUTPUT_DIR
    app.state.processed_dir = PROCESSED_DIR
    app.state.hawkeye_dir = HAWKEYE_DIR
    app.state.hawkeye_weights = HAWKEYE_WEIGHTS
    yield


app = FastAPI(
    title="IAF FOD Detection Backend",
    version="1.0.0",
    description="Camera-only FOD detection backend using FastAPI and the Hawkeye detector.",
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
