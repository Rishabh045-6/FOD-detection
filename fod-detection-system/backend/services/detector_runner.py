import subprocess
import sys
from pathlib import Path
import numpy as np
from typing import Dict, Any, List, Tuple, Optional

# Lazy import interface to pull the high-speed live engine context
from services.live_detector import LiveDetector


class HawkeyeRunner:
    def __init__(self, hawkeye_dir: Path, yolo_weights: Path):
        self.hawkeye_dir = hawkeye_dir
        self.yolo_weights = yolo_weights
        
        # In-memory detector instance to keep GPU weights loaded across frames
        self._shared_detector: Optional[LiveDetector] = None

    def process_frame(self, frame: np.ndarray, frame_id: int = 0) -> Tuple[np.ndarray, List[Dict[str, Any]], bool]:
        """
        Exposes an optimized, high-frequency, frame-by-frame programmatic processing route.
        Loads the neural network weights into memory exactly once upon initial invocation.
        """
        if self._shared_detector is None:
            if not self.yolo_weights.exists():
                raise RuntimeError(f"Hawkeye model tracking weights not found: {self.yolo_weights}")
            
            # Initialize the shared in-memory inference pipeline structure
            self._shared_detector = LiveDetector(model_path=str(self.yolo_weights))
            
        return self._shared_detector.process_frame(frame, frame_id=frame_id)

    def run(self, video_path: Path, output_dir: Path) -> None:
        """
        Legacy batch worker pipeline execution strategy. 
        Spawns an isolated subprocess to decode, process, and dump a complete video file.
        """
        if not self.hawkeye_dir.exists():
            raise RuntimeError(f"Hawkeye directory not found: {self.hawkeye_dir}")
        if not self.yolo_weights.exists():
            raise RuntimeError(f"Hawkeye weights not found: {self.yolo_weights}")

        output_dir.mkdir(parents=True, exist_ok=True)

        command = [
            sys.executable,
            "tbd/detect_fused.py",
            "--video",
            str(video_path),
            "--gpu",
            "--yolo-weights",
            str(self.yolo_weights.relative_to(self.hawkeye_dir)),
            "--out",
            str(output_dir),
            "--yolo-imgsz",
            "640",
            "--yolo-stride",
            "8",
        ]

        try:
            completed = subprocess.run(
                command,
                current_working_directory=self.hawkeye_dir, # maps to cwd=self.hawkeye_dir
                check=True,
                capture_output=True,
                text=True,
            )
        except FileNotFoundError as exc:
            raise RuntimeError("Python executable not found for Hawkeye run") from exc
        except subprocess.CalledProcessError as exc:
            details = (exc.stderr or exc.stdout or "Unknown Hawkeye error").strip()
            raise RuntimeError(f"Hawkeye execution failed: {details}") from exc

        detections_json = output_dir / "detections.json"
        if not detections_json.exists():
            details = (completed.stdout or completed.stderr or "").strip()
            raise RuntimeError(
                "Hawkeye completed without producing detections.json"
                + (f": {details}" if details else "")
            )