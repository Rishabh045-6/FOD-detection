from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

# Route & WebSocket Core Imports
from routes.detect import router as detect_router
from routes.live import router as live_router
from websocket.live_stream import router as ws_router

# Core Hardware Abstraction & Analytics Drivers
from services.camera_manager import CameraManager
from services.live_detector import LiveDetector

BASE_DIR = Path(__file__).resolve().parent
UPLOAD_DIR = BASE_DIR / "uploads"
OUTPUT_DIR = BASE_DIR / "outputs"
PROCESSED_DIR = BASE_DIR / "processed"
HAWKEYE_DIR = BASE_DIR / "hawkeye"
HAWKEYE_WEIGHTS = HAWKEYE_DIR / "detection" / "runs" / "fod_train" / "v5_spd_both" / "weights" / "best.pt"


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Ensure system operational data directories are cleanly mapped
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

    # Attach static asset target configurations to app state
    app.state.upload_dir = UPLOAD_DIR
    app.state.output_dir = OUTPUT_DIR
    app.state.processed_dir = PROCESSED_DIR
    app.state.hawkeye_dir = HAWKEYE_DIR
    app.state.hawkeye_weights = HAWKEYE_WEIGHTS

    # --- Live System Global Singleton Initialization ---
    # Instantiate engine structures exactly once on server initialization
    app.state.camera_manager = CameraManager()
    
    # Passing our specialized Hawkeye target weights directly to the inference agent
    app.state.live_detector = LiveDetector(model_path=str(HAWKEYE_WEIGHTS))

    yield
    
    # --- System Tear-Down Lifecycle Management ---
    # Ensure camera resource lines are properly released on application shutdown
    if hasattr(app.state, "camera_manager"):
        app.state.camera_manager.close()


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

# Expose static analytics processed data tracks to the UI
app.mount("/processed", StaticFiles(directory=PROCESSED_DIR), name="processed")

# --- Register Modular Routing Endpoints ---
app.include_router(detect_router, prefix="/api") # Legacy static file uploading router
app.include_router(live_router)                  # HTTP control pipeline router for live mode
app.include_router(ws_router)                    # Real-time WebSocket analytics broadcast system


@app.get("/health")
async def health_check() -> dict:
    return {"status": "ok"}