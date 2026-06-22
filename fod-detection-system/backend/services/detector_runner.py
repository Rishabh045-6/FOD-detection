import subprocess
import sys
from pathlib import Path


class HawkeyeRunner:
    def __init__(self, hawkeye_dir: Path, yolo_weights: Path):
        self.hawkeye_dir = hawkeye_dir
        self.yolo_weights = yolo_weights

    def run(self, video_path: Path, output_dir: Path) -> None:
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
                cwd=self.hawkeye_dir,
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
