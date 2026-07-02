# IAF FOD Detection Backend

## Prerequisites

- Python 3.8+
- Hawkeye dependencies available in the backend environment

## Setup

From the repository root, run:

```bash
cd backend
pip install -r hawkeye/requirements.txt
```

Or install directly from the path:

```bash
pip install -r backend/hawkeye/requirements.txt
```

## Run

```bash
uvicorn app:app --reload
```

Run from the `backend` directory. Server runs at `http://localhost:8000`

## Configuration

- **Detection Engine**: Hawkeye is the only detector used by the backend
- **YOLO Weights**: `backend/hawkeye/detection/runs/fod_train/v5_spd_both/weights/best.pt`
- **Output**: Processed videos are served from `/processed/<file>.mp4`

## Health Check

```bash
curl http://localhost:8000/health
```

## API

- **POST** `/api/detect` - Upload video for FOD detection
  - Body: multipart form with `video` file (MP4, AVI, MOV)
  - Backend workflow:
    - saves the upload to `backend/uploads/`
    - runs `python tbd/detect_fused.py --video <uploaded_video> --yolo-weights detection/runs/fod_train/v5_spd_both/weights/best.pt --out <output_dir>`
    - reads `<output_dir>/detections.json`
    - copies the annotated output video into `backend/processed/`
  - Returns: frontend-compatible JSON with `distance_m: null` and `coordinates: { "x": null, "y": null }`
