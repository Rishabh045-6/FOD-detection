import asyncio
import logging
from datetime import datetime
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from fastapi.encoders import jsonable_encoder
from services.camera_manager import CameraManager
from services.live_detector import LiveDetector
from services.result_parser import HawkeyeResultParser
import cv2
import base64

router = APIRouter(tags=["Live WebSocket Stream"])
logger = logging.getLogger("LiveWebSocket")

class LiveStreamManager:
    def __init__(self, detector: LiveDetector):
        self.camera = CameraManager()
        self.detector = detector
        self.result_parser = HawkeyeResultParser()
        self.is_running = False
        self.frame_count = 0

    async def broadcast_loop(self, websocket: WebSocket, source: str):
        """
        Continuously captures camera frames, runs the Hawkeye inference pipeline,
        and pipes the real-time telemetry payload down the WebSocket pipe.
        """
        self.frame_count = 0
        
        while self.is_running:
            loop = asyncio.get_running_loop()
            ret, frame = await loop.run_in_executor(None, self.camera.read_frame)

            if not ret or frame is None:
                logger.warning("Camera stream returned an empty frame. Retrying...")
                await asyncio.sleep(0.033)
                continue

            self.frame_count += 1
            try:
                annotated_frame, raw_detections, detected = await loop.run_in_executor(
                    None,
                    self.detector.process_frame,
                    frame,
                )

                if annotated_frame is None:
                    raise RuntimeError("Detector returned no annotated frame")

                parsed_detections = []
                for index, detection in enumerate(raw_detections, start=1):
                    try:
                        parsed_detections.append(
                            self.result_parser.parse_live_detection(
                                index,
                                detection,
                                self.frame_count,
                                fps=30.0,
                            )
                        )
                    except Exception as exc:
                        logger.warning(
                            "Failed to parse detection %s for frame %s: %s",
                            index,
                            self.frame_count,
                            exc,
                        )

                success, buffer = cv2.imencode('.jpg', annotated_frame)
                if not success or buffer is None:
                    raise RuntimeError("Failed to encode annotated frame as JPEG")

                jpg_as_text = base64.b64encode(buffer).decode('utf-8')
                timestamp = datetime.utcnow().strftime("%H:%M:%S")

                payload = {
                    "frame": self.frame_count,
                    "timestamp": timestamp,
                    "status": "active",
                    "fps": 0,
                    "fod_detected": len(parsed_detections) > 0,
                    "detections": parsed_detections,
                    "image": f"data:image/jpeg;base64,{jpg_as_text}",
                    "camera_info": {
                        "hardware_type": self.camera.source_type,
                        "target_source": str(source),
                    },
                }

                safe_payload = jsonable_encoder(payload)
                await websocket.send_json(safe_payload)

            except WebSocketDisconnect:
                logger.info(
                    "Live WebSocket client disconnected during frame %s.",
                    self.frame_count,
                )
                break

            except Exception as e:
                logger.exception(
                    "Live WebSocket frame processing failed on frame %s: %s",
                    self.frame_count,
                    e,
                )
                break

            # Enforce execution spacing to match standard camera hardware feed pacing (~30 FPS)
            await asyncio.sleep(0.01)

@router.websocket("/ws/live")
async def websocket_endpoint(websocket: WebSocket, source: str = "0"):
    """
    WebSocket route for real-time runway streaming. Accepts an optional query
    parameter to choose the active camera source.
    """
    await websocket.accept()
    logger.info("Frontend connected to live analytics stream via WebSocket.")
    
    detector = websocket.app.state.live_detector
    stream_manager = LiveStreamManager(detector)
    
    # Open the camera stream source
    success = stream_manager.camera.open(source)
    if not success:
        await websocket.send_json({"status": "error", "message": f"Could not connect to camera source: {source}"})
        await websocket.close(code=1011)
        return

    try:
        stream_manager.is_running = True
        # Run the broadcasting handler task
        await stream_manager.broadcast_loop(websocket, source)
        
    except WebSocketDisconnect:
        logger.info("Frontend client disconnected normally from live WebSocket stream.")
        
    except Exception as e:
        logger.error(f"Unexpected crash inside the live stream processing context: {e}")
        
    finally:
        # Resource cleanup guarantees hardware devices are freed
        stream_manager.is_running = False
        stream_manager.camera.close()
        try:
            await websocket.close()
        except Exception:
            pass # Connection already destroyed cleanly