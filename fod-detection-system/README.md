# Airport FOD Detection System

A full-stack runway inspection application for detecting Foreign Object Debris (FOD) from uploaded video.

## Overview

The project includes:

- A React + TypeScript frontend for uploading videos, tracking processing progress, and reviewing detections
- A FastAPI backend for video processing, object detection, annotation, and result delivery
- A live hardware stream page for future real-time FOD monitoring

## Tech Stack

### Frontend

- React 19
- TypeScript 6
- Vite 8
- Material UI 9
- React Router 7
- Axios
- React Toastify

### Backend

- FastAPI
- Ultralytics YOLO
- OpenCV
- Pydantic
- FFmpeg
- Python services organized under `backend/services/`

## Project Structure

```text
fod-detection-system/
|-- src/
|   |-- assets/
|   |-- components/
|   |-- pages/
|   |-- services/
|   |-- styles/
|   |-- types/
|   |-- App.css
|   |-- App.tsx
|   |-- index.css
|   `-- main.tsx
|-- backend/
|   |-- app.py
|   |-- config/
|   |-- hawkeye/
|   |   |-- requirements.txt
|   |-- models/
|   |-- routes/
|   |-- services/
|   |-- processed/
|   |-- uploads/
|   |-- README.md
|-- public/
|-- dist/
|-- .env
|-- .env.example
|-- API_ARCHITECTURE.md
|-- BUILD_SUMMARY.md
|-- IMPLEMENTATION_CHECKLIST.md
|-- PROJECT_COMPLETE.md
|-- QUICK_REFERENCE.md
|-- SETUP_GUIDE.md
|-- START_HERE.md
`-- package.json
```

## Frontend Flow

### `/`

- Upload MP4, AVI, or MOV video
- Preview the selected file
- Start FOD detection

### `/processing`

- Show upload progress
- Display staged processing states
- Redirect to results on success

### `/results`

- Play processed video
- Review detection summary
- Inspect detailed FOD table
- Export detection data as JSON

### `/live`

- Connect to a live camera stream
- View live detection status
- Monitor nearest detected object in real time

## Quick Start

### 1. Install frontend dependencies

```bash
cd fod-detection-system
npm install
```

### 2. Configure the frontend API URL

Set `VITE_API_BASE_URL` in `.env`.

If you run the included FastAPI backend with `uvicorn app:app --reload`, use:

```env
VITE_API_BASE_URL=http://localhost:8000
```

### 3. Start the frontend

```bash
npm run dev
```

The Vite dev server is available at `http://localhost:5173`.

### 4. Start the backend

```bash
cd backend
pip install -r hawkeye/requirements.txt
uvicorn app:app --reload
```

The backend runs at `http://localhost:8000`.

## Expected API Contract

### Request

`POST /api/detect`

- Content type: `multipart/form-data`
- Field: `video`

### Response

```json
{
  "status": "success",
  "processed_video_url": "/processed/example.mp4",
  "total_frames": 5000,
  "processing_time": 32.5,
  "fod_detected": true,
  "detections": [
    {
      "id": "FOD-001",
      "frame": 250,
      "timestamp": "00:00:08",
      "distance_m": 42.6,
      "coordinates": {
        "x": 12.4,
        "y": 5.8
      },
      "confidence": 0.96
    }
  ]
}
```

## Scripts

```bash
npm run dev
npm run build
npm run preview
npm run lint
```

## Documentation

- [START_HERE.md](./START_HERE.md) - fastest path through the repo
- [SETUP_GUIDE.md](./SETUP_GUIDE.md) - setup and configuration details
- [QUICK_REFERENCE.md](./QUICK_REFERENCE.md) - command and file cheat sheet
- [API_ARCHITECTURE.md](./API_ARCHITECTURE.md) - system flow and API contract
- [IMPLEMENTATION_CHECKLIST.md](./IMPLEMENTATION_CHECKLIST.md) - verification checklist
- [PROJECT_COMPLETE.md](./PROJECT_COMPLETE.md) - current project status
- [BUILD_SUMMARY.md](./BUILD_SUMMARY.md) - latest build validation summary
- [backend/README.md](./backend/README.md) - backend-specific setup
- [API_ARCHITECTURE.md](./API_ARCHITECTURE.md) - API and architecture details

## Notes

- The frontend base URL is configured with `VITE_API_BASE_URL` in `.env`; defaults to `http://localhost:8000` when not set.
- The current production build succeeds, but Vite reports a large client bundle warning for the main JavaScript chunk.
