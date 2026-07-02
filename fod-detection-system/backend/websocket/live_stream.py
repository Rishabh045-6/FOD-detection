import asyncio
import base64
import logging
import time
import cv2
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query

router = APIRouter(tags=["Live Analytics Stream"])
logger = logging.getLogger("LiveStreamWebSocket")


class StreamSessionWorker:

    def __init__(self, websocket: WebSocket, camera_manager, result_parser):
        self.websocket = websocket
        self.camera = camera_manager
        self.parser = result_parser
        self.is_running = False
        self.frame_counter = 0

    async def run_pipeline_loop(self, target_fps: float = 30.0):
        """
        Runs the continuous high-speed extraction and push pipeline:
        Frame -> Base64 Image Encode -> Telemetry Parse -> WebSocket Send.
        """
        self.frame_counter = 0
        frame_delay = 1.0 / target_fps
        
        # Pull initial reference configurations out of the active hardware stream
        camera_info = {
            "source_type": getattr(self.camera, "source_type", "unknown"),
            "target_source": getattr(self.camera, "current_source", "0"),
        }

        while self.is_running:
            loop_start = time.perf_counter()
            self.frame_counter += 1

            # 1. Capture Raw Image Array
            # Executed in an executor thread to preserve async responsiveness
            loop = asyncio.get_running_loop()
            frame = await loop.run_in_executor(None, self.camera.read)

            if frame is None:
                # Mirror system status update back to frontend if line stutters
                try:
                    await self.websocket.send_json({
                        "frame": self.frame_counter,
                        "status": "reconnecting",
                        "camera_info": camera_info,
                        "fod_detected": False,
                        "detections": [],
                        "image": "",
                        "fps": 0
                    })
                except Exception:
                    break
                await asyncio.sleep(0.1)
                continue

            # 2. Performance Metric Tracking
            loop_end = time.perf_counter()
            elapsed = loop_end - loop_start
            actual_fps = round(1.0 / elapsed, 1) if elapsed > 0 else target_fps

            # 3. Dynamic Inference Processing Layer
            # Diverting work onto the singleton live_detector inside app state
            # (In a production flow, pass frame directly through the runner)
            detector = self.websocket.app.state.live_detector
            annotated_frame, raw_detections, fod_detected = await loop.run_in_executor(
                None, detector.process_frame, frame, self.frame_counter
            )

            # 4. Telemetry Extraction and Structural Parsing
            parsed_detections = []
            for idx, det in enumerate(raw_detections):
                # Map raw predictive lists onto unified tracking layouts
                clean_det = self.parser.parse_live_detection(
                    index=idx,
                    raw_detection=det,
                    frame_number=self.frame_counter,
                    fps=actual_fps
                )
                parsed_detections.append(clean_det)

            # 5. JPEG Array Compression & Base64 Text Transformation
            # High quality value matching balanced compression constraints
            success, jpeg_buffer = cv2.imencode(".jpg", annotated_frame, [int(cv2.IMWRITE_JPEG_QUALITY), 80])
            if not success:
                continue

            base64_string = base64.b64encode(jpeg_buffer).decode("utf-8")
            image_data_url = f"data:image/jpeg;base64,{base64_string}"

            # 6. Dispatch Payload Pack to Frontend
            payload = {
                "frame": self.frame_counter,
                "timestamp": parsed_detections[0]["timestamp"] if fod_detected else self.parser._format_timestamp(self.frame_counter, actual_fps),
                "status": "active",
                "fps": actual_fps,
                "camera_info": camera_info,
                "fod_detected": fod_detected,
                "detections": parsed_detections,
                "image": image_data_url,
            }

            try:
                await self.websocket.send_json(payload)
            except Exception as exc:
                logger.error(f"WebSocket socket write error dropped packet: {exc}")
                break

            # 7. Adaptive Pacing Frame Governor
            compute_time = time.perf_counter() - loop_start
            sleep_time = max(0.0, frame_delay - compute_time)
            await asyncio.sleep(sleep_time)


@router.websocket("/ws/live")
async def live_analytic_websocket_endpoint(
    websocket: WebSocket,
    source: str = Query("0", description="Target hardware address index or remote RTSP pipeline line string")
):
    """
    Accepts low-latency, streaming WebSocket pipes from control towers.
    Coordinates device attachments cleanly via shared singletons.
    """
    await websocket.accept()
    logger.info("Control tower connection bound to live stream network socket.")

    # Safely pull our singletons straight out of the shared application instance space
    camera_manager = websocket.app.state.camera_manager
    
    # Initialize the parser using your custom class
    from services.result_parser import HawkeyeResultParser
    result_parser = HawkeyeResultParser()

    # Dynamically mount the video track requested by the query string parameters
    connection_success = camera_manager.open(source)
    if not connection_success:
        await websocket.send_json({
            "status": "error",
            "message": f"Hardware rejection. Failed opening channel location parameters: {source}"
        })
        await websocket.close(code=1011)
        return

    worker = StreamSessionWorker(websocket, camera_manager, result_parser)
    
    try:
        worker.is_running = True
        await worker.run_pipeline_loop()
    except WebSocketDisconnect:
        logger.info("Live data consumer cleanly disconnected from endpoint pipeline.")
    except Exception as e:
        logger.error(f"Internal processing stream exception caught: {e}")
    finally:
        worker.is_running = False
        camera_manager.close()
        try:
            await websocket.close()
        except Exception:
            pass  # Socket connection killed