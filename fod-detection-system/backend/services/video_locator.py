from pathlib import Path


VIDEO_SUFFIXES = (".mp4", ".avi", ".mov", ".mkv")


def locate_annotated_video(output_dir: Path) -> Path:
    preferred = sorted(
        path for path in output_dir.iterdir() if path.is_file() and path.suffix.lower() in VIDEO_SUFFIXES and "_fused" in path.stem
    )
    if preferred:
        return preferred[0]

    fallback = sorted(
        path for path in output_dir.iterdir() if path.is_file() and path.suffix.lower() in VIDEO_SUFFIXES
    )
    if fallback:
        return fallback[0]

    raise RuntimeError("Hawkeye completed without producing an annotated video")
