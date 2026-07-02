import cv2
import time
import logging
from typing import Optional, Any, Union

# Robust wrapper for optional Raspberry Pi environmental architectures
try:
    from picam2 import Picamera2
    HAS_PICAM = True
except ImportError:
    HAS_PICAM = False

logger = logging.getLogger("CameraManager")

class CameraManager:
    def __init__(self):
        self.cap: Optional[Any] = None
        self.current_source: Optional[str] = None
        self.source_type: Optional[str] = None
        
        # Connection resiliency attributes
        self.last_retry_time: float = 0.0
        self.retry_interval_seconds: float = 5.0

    def open(self, source: Union[str, int]) -> bool:
        """
        Deduces the type of camera line, opens the connection channel, 
        and configures optimization flags.
        """
        self.close()  # Clean down hanging file-descriptors
        
        # Cast input value configurations safely
        str_source = str(source).strip()
        self.current_source = str_source

        try:
            # Type 1 & 2: Local Hardwired Assets (Laptop Webcams, USB Devices)
            if str_source.isdigit():
                dev_index = int(str_source)
                self.cap = cv2.VideoCapture(dev_index)
                self.source_type = "cv2_local"
                
                # Fast connection timeout properties for native devices
                self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1920)
                self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 1080)

            # Type 3: Native Raspberry Pi CSI Camera Assemblies
            elif str_source.lower() == "rpi":
                if not HAS_PICAM:
                    raise ImportError("picam2 library bindings missing from server build landscape.")
                self.cap = Picamera2()
                self.cap.start()
                self.source_type = "rpi_native"

            # Type 4, 5 & 6: Network Streams (RTSP Security Nodes, Phone IP Cams, HTTP streams)
            elif str_source.startswith(("rtsp://", "http://", "https://")):
                # Inject FFmpeg network transport configurations to drop buffering latency
                self.cap = cv2.VideoCapture(str_source, cv2.CAP_FFMPEG)
                self.source_type = "cv2_network"
                
                # Direct optimization parameters to prevent frame storage buildup
                self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
            
            else:
                # Catch-all generic path handler
                self.cap = cv2.VideoCapture(str_source)
                self.source_type = "cv2_generic"

            # Evaluate system activation hooks
            if self.source_type != "rpi_native":
                if not self.cap or not self.cap.isOpened():
                    raise ConnectionError(f"OpenCV device channel refused handshakes for path: {str_source}")
            
            logger.info(f"[{self.source_type.upper()}] Stream link securely fastened onto target: {str_source}")
            return True

        except Exception as e:
            logger.error(f"Failed to securely bind target stream endpoint: {e}")
            self.close()
            return False

    def read(self) -> Optional[Any]:
        """
        The unified, high-level frame extractor. 
        Automatically monitors stream health and self-heals dropped connections.
        """
        if not self.current_source:
            return None

        # Self-healing logic hook for disconnected hardware
        if not self._is_channel_healthy():
            self._attempt_reconnect()
            return None

        try:
            if self.source_type == "rpi_native":
                return self.cap.capture_array()
            
            # Standard OpenCV capture branch
            ret, frame = self.cap.read()
            if not ret:
                logger.warning(f"Blank frame dropped on interface source: {self.current_source}")
                return None
                
            return frame

        except Exception as e:
            logger.error(f"In-flight read error caught on interface connection matrix: {e}")
            return None

    def close(self):
        """
        Tears down data links and flushes system device registers.
        """
        if self.cap:
            try:
                if self.source_type == "rpi_native" and hasattr(self.cap, 'stop'):
                    self.cap.stop()
                elif hasattr(self.cap, 'release'):
                    self.cap.release()
            except Exception as e:
                logger.error(f"Errors occurred during internal hardware teardown execution lines: {e}")
            
        self.cap = None
        self.source_type = None
        logger.info("Camera communication registers released and reset.")

    def _is_channel_healthy(self) -> bool:
        """Runs validation routines against operational resource drivers."""
        if self.cap is None:
            return False
        if self.source_type == "rpi_native":
            return True
        return bool(self.cap.isOpened())

    def _attempt_reconnect(self):
        """
        Throttled reconnect handler to prevent loop hammering 
        when network paths fail.
        """
        current_time = time.time()
        if current_time - self.last_retry_time < self.retry_interval_seconds:
            return

        self.last_retry_time = current_time
        logger.warning(f"Connection lost on target '{self.current_source}'. Initiating recovery handshake now...")
        
        # Attempt to run re-initialization pipeline step
        self.open(self.current_source)