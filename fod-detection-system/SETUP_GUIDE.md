# Setup Guide

## Prerequisites

### Frontend

- Node.js 16 or newer
- npm 7 or newer

### Backend

- Python 3.8 or newer
- FFmpeg available on the machine

## Frontend Setup

```bash
cd E:\IAF\fod-detection-system
npm install
```

Create or update `.env`:

```env
VITE_API_BASE_URL=http://localhost:8000
VITE_DEBUG=false
```

Start the frontend:

```bash
npm run dev
```

Open `http://localhost:5173`.

## Backend Setup

```bash
cd E:\IAF\fod-detection-system\backend
pip install -r requirements.txt
```

Place your trained model here:

```text
backend/models/fod_model.pt
```

Start the backend:

```bash
uvicorn app:app --reload
```

The backend will typically be available at `http://localhost:8000`.

## Backend Requirements

The included backend requirements file currently contains:

- `fastapi`
- `uvicorn[standard]`
- `python-multipart`
- `opencv-python`
- `ultralytics`
- `numpy`
- `pydantic`
- `ffmpeg-python`

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

### The frontend still calls port 5000

- Restart the Vite dev server after editing `.env`
- Check `src/services/api.ts`, which falls back to `http://localhost:5000` only when `VITE_API_BASE_URL` is missing

### Build passes but the backend fails later

- Check Python dependencies
- Check FFmpeg installation
- Check model file availability
- Check camera calibration contents
