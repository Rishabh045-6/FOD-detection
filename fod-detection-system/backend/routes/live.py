from fastapi import APIRouter, Request, HTTPException, status, Query
from pydantic import BaseModel, Field
from typing import Optional

router = APIRouter(
    prefix="/api/live",
    tags=["Live Control Operations"]
)

# --- Pydantic Data Verification Models ---

class CameraConfigRequest(BaseModel):
    source: str = Field(
        ..., 
        description="Target camera identifier. Can be an index like '0', a file path, or network stream string (e.g., 'rtsp://...')"
    )

class LiveStatusResponse(BaseModel):
    is_active: bool = Field(..., description="Fast flag showing whether camera loop thread is active")
    current_source: Optional[str] = Field(None, description="The configured device interface string location")
    hardware_type: Optional[str] = Field(None, description="Internal hardware processing profile used")

class StandardActionResponse(BaseModel):
    status: str = Field(default="success")
    message: str


# --- API Routes Control Infrastructure ---

@router.post("/start", response_model=StandardActionResponse, status_code=status.HTTP_200_OK)
async def start_live_camera(
    request: Request, 
    config: Optional[CameraConfigRequest] = None
):
    """
    Initializes and unlocks the targeted physical or network video stream matrix line.
    """
    camera_manager = request.app.state.camera_manager
    
    # Fallback to standard webcam index '0' if no explicit payload path was sent
    target_source = config.source if config else "0"

    # Attempt hardware initialization line handshake 
    success = camera_manager.open(target_source)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Hardware initialization failed. Unable to open camera target source: {target_source}"
        )

    return StandardActionResponse(
        message=f"Camera framework initialized successfully. Source path assigned: {target_source}"
    )


@router.post("/stop", response_model=StandardActionResponse, status_code=status.HTTP_200_OK)
async def stop_live_camera(request: Request):
    """
    Safely tears down active camera tracking, unlinks open frame buffers, 
    and frees hardware lines.
    """
    camera_manager = request.app.state.camera_manager
    
    if not camera_manager.cap:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot terminate camera loop; stream pipeline is already closed."
        )

    camera_manager.close()
    return StandardActionResponse(message="Camera stream hardware interface links closed cleanly.")


@router.get("/status", response_model=LiveStatusResponse, status_code=status.HTTP_200_OK)
async def get_camera_status(request: Request):
    """
    Polls the runtime telemetry tracking state of the target camera system structure.
    """
    camera_manager = request.app.state.camera_manager
    
    # Verify active connectivity structure flags
    is_active = (
        camera_manager.cap is not None and 
        hasattr(camera_manager.cap, 'isOpened') and 
        camera_manager.cap.isOpened()
    ) if camera_manager.source_type != "rpi_native" else (camera_manager.cap is not None)

    return LiveStatusResponse(
        is_active=is_active,
        current_source=getattr(camera_manager, 'cap', None) if is_active else None,
        hardware_type=camera_manager.source_type if is_active else "None"
    )