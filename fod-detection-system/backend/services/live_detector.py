import cv2
import time
import numpy as np
from typing import Dict, Any, List, Tuple
from ultralytics import YOLO

class LiveDetector:
    def __init__(self, model_path: str):
        """
        Initializes the shared frame-by-frame inference engine.
        Loads the Hawkeye YOLO model exactly once into memory.
        """
        self.model = YOLO(model_path)
        
        # Camera Calibration Constants (Geometric Ground-Plane Back-Projection)
        # Assumes a calibrated mounting orientation for runway scanning vectors
        self.camera_height_m = 3.5          # Mounting height above runway ground level
        self.camera_pitch_rad = np.radians(12.5)  # Downward tilt angle of the lens axis
        self.focal_length_px = 1250.0       # Pixel-calibrated scale focal length
        self.principal_point = (960, 540)   # Optical frame center (assuming 1080p stream matrix)

    def process_frame(self, frame: np.ndarray, frame_id: int = 0) -> Tuple[np.ndarray, List[Dict[str, Any]], bool]:
        """
        Executes the exact linear analysis pipeline on an individual frame.
        
        Steps: Frame -> Run Hawkeye -> Distance -> Coordinates -> Draw Boxes -> Return
        
        Returns:
            annotated_frame (np.ndarray): The BGR frame array with visual overlays.
            detections (list): Structured telemetry list tracking current visible hazards.
            fod_detected (bool): Quick flag showing if any threats exist inside this frame window.
        """
        # 1. Run Hawkeye (YOLO Single Frame Inference)
        # stream=True utilizes generator memory buffers, vital for endless streaming loops
        results = self.model.predict(frame, conf=0.25, verbose=False, stream=True)
        
        detections_list = []
        annotated_frame = frame.copy()
        fod_detected = False

        for result in results:
            boxes = result.boxes
            if len(boxes) > 0:
                fod_detected = True

            for idx, box in enumerate(boxes):
                # Isolate target bounding coordinates
                x1, y1, x2, y2 = map(int, box.xyxy[0].tolist())
                confidence = float(box.conf[0])
                
                # Determine object contact point with runway ground line (bottom center of box)
                base_x = (x1 + x2) // 2
                base_y = y2

                # 2 & 3. Distance & Coordinate Estimation Engine
                distance_m, coords = self._calculate_spatial_telemetry(base_x, base_y)

                # Assemble tracking structure matching frontend payload specifications
                detection_data = {
                    "id": f"FOD-{idx + 1:03d}",
                    "confidence": round(confidence, 2),
                    "distance_m": round(distance_m, 2),
                    "coordinates": {
                        "x": round(coords[0], 2),
                        "y": round(coords[1], 2)
                    }
                }
                detections_list.append(detection_data)

                # 4. Draw Boxes & Labels (Annotations Layer)
                self._apply_render_layer(annotated_frame, (x1, y1, x2, y2), detection_data)

        return annotated_frame, detections_list, fod_detected

    def _calculate_spatial_telemetry(self, px_x: int, px_y: int) -> Tuple[float, Tuple[float, float]]:
        """
        Projects raw image space pixel coordinates directly out onto runway spatial meters.
        """
        cx, cy = self.principal_point
        
        # Determine ray angular displacement offsets relative to optical centerlines
        alpha_y = (cy - px_y) / self.focal_length_px
        alpha_x = (px_x - cx) / self.focal_length_px
        
        total_angle_y = self.camera_pitch_rad + alpha_y
        
        # Safeguard logic: If point hits horizon boundary line, push infinity mask
        if total_angle_y <= 0:
            return 999.0, (0.0, 0.0)
            
        # Standard trigonometric ground mapping equations
        distance_y = self.camera_height_m / np.tan(total_angle_y)
        distance_x = distance_y * alpha_x
        
        # Absolute range vector hypotenuse calculation
        absolute_distance = np.sqrt(distance_x**2 + distance_y**2)
        
        return absolute_distance, (distance_x, distance_y)

    def _apply_render_layer(self, image: np.ndarray, bbox: Tuple[int, int, int, int], data: Dict[str, Any]):
        """
        Draws specialized target box brackets and text cards over detections.
        """
        x1, y1, x2, y2 = bbox
        
        # Render high-visibility warning perimeter box (Solid Crimson Red)
        cv2.rectangle(image, (x1, y1), (x2, y2), (0, 0, 255), 2)
        
        # Build analytical data string card overlay
        label = f"{data['id']} ({int(data['confidence']*100)}%) | D:{data['distance_m']}m"
        (w, h), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.45, 1)
        
        # Render dynamic solid tag block container directly above hazard target bounding line
        cv2.rectangle(image, (x1, y1 - h - 10), (x1 + w, y1), (0, 0, 255), -1)
        cv2.putText(image, label, (x1, y1 - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (255, 255, 255), 1, cv2.LINE_AA)