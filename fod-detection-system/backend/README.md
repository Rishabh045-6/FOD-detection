# IAF FOD Detection Backend

## Prerequisites

- Python 3.8+
- FFmpeg (for video processing)

### Install FFmpeg

**Windows**: `choco install ffmpeg`  
**Linux**: `sudo apt-get install ffmpeg`  
**macOS**: `brew install ffmpeg`

## Setup

```bash
pip install -r requirements.txt
```

## Run

```bash
uvicorn app:app --reload
```

Run from the `backend` directory. Server runs at `http://localhost:8000`

## Configuration

- **Model**: Place YOLO model at `backend/models/fod_model.pt`
- **Camera Calibration**: Update `backend/config/camera_calibration.json` with your camera intrinsics and pose
- **Output**: Processed videos served from `/processed/<file>.mp4`

## Health Check

```bash
curl http://localhost:8000/health
```

## API

- **POST** `/api/detect` - Upload video for FOD detection
  - Body: multipart form with `video` file (MP4, AVI, MOV)
  - Returns: JSON with detections, processed video URL, processing time
