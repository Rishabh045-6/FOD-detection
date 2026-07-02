# Setup Guide

## Prerequisites

### Frontend

- Node.js 18 or newer
- npm 8 or newer

### Backend

- Python 3.8 or newer
- FFmpeg available on the machine

## Frontend Setup

```bash
cd E:\IAF\fod-detection-system
npm install
```

Create or update `.env` in the repo root:

```env
VITE_API_BASE_URL=http://localhost:8000
```

If the backend runs on a different port, update the URL accordingly.

Start the frontend:

```bash
npm run dev
```

Open `http://localhost:5173`.

## Backend Setup

```bash
cd E:\IAF\fod-detection-system\backend
pip install -r hawkeye/requirements.txt
```

Place your trained model here:

```text
backend/models/fod_model.pt
```

If the repo currently includes a placeholder model, ensure the filename matches the backend loader.

Start the backend:

```bash
uvicorn app:app --reload
```

The backend will typically be available at `http://localhost:8000`.

## Backend Requirements

The included backend requirements file currently contains:

- `torch==2.6.0+cu128`
- `torchvision==0.21.0+cu128`
- `ultralytics==8.3.145`
- `sahi==0.11.20`
- `pyyaml==6.0.2`
- `python-dotenv==1.0.1`
- `faiss-cpu==1.9.0`

Install these from `backend/hawkeye/requirements.txt` after installing a compatible PyTorch wheel.

Confirm the package list in `backend/hawkeye/requirements.txt` matches the installed backend environment.

## What the Frontend Expects

The frontend sends a single multipart upload:

- Endpoint: `POST /api/detect`
- Form field: `video`

The frontend expects these response fields:

- `status`
- `processed_video_url`
- `total_frames`
- `processing_time`
- `fod_detected`
- `detections`

## Project Layout

```text
src/
|-- assets/
|-- components/
|-- pages/
|-- services/
|-- styles/
`-- types/

backend/
|-- app.py
|-- config/
|-- models/
|-- routes/
|-- services/
|-- processed/
`-- uploads/
```

## Verification

### Frontend

```bash
npm run build
```

### Backend

```bash
curl http://localhost:8000/health
```

Expected response:

```json
{
  "status": "ok"
}
```

## Troubleshooting

### The upload page opens but processing fails

- Confirm `VITE_API_BASE_URL` matches the backend URL
- Confirm the backend is running
- Confirm the model file exists at `backend/models/fod_model.pt`

### The frontend still calls a mismatched backend port

- Restart the Vite dev server after editing `.env`
- Check `src/services/api.ts` and ensure `VITE_API_BASE_URL` points to the backend host and port

### Build passes but the backend fails later

- Check Python dependencies
- Check FFmpeg installation
- Check model file availability
- Check camera calibration contents
