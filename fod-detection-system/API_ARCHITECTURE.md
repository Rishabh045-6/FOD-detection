# Airport FOD Detection System - Architecture and API

## Architecture Overview

The system is split into two layers:

1. A React frontend that uploads video and presents results.
2. A FastAPI backend that processes the upload and returns detections.

## Frontend Structure

### Routes

- `/` - upload page
- `/processing` - upload and processing state
- `/results` - processed video and detection results

### Main Frontend Modules

- `src/components/VideoUploader.tsx`
- `src/components/ProcessingStatus.tsx`
- `src/components/VideoPlayer.tsx`
- `src/components/DetectionSummary.tsx`
- `src/components/AlertBanner.tsx`
- `src/components/FODTable.tsx`
- `src/services/api.ts`
- `src/types/detection.ts`

## Backend Structure

### Main Backend Modules

- `backend/app.py` - FastAPI app, CORS, lifespan setup, static mount
- `backend/routes/detect.py` - `/api/detect` endpoint
- `backend/models/schemas.py` - response models
- `backend/services/detector.py` - model loading and inference
- `backend/services/video_processor.py` - upload-to-result workflow
- `backend/services/annotation.py` - draw detections
- `backend/services/calibration.py`
- `backend/services/coordinate_transform.py`
- `backend/services/distance_estimator.py`

## Request Flow

1. The user selects a video on the upload page.
2. The frontend stores the file and navigates to `/processing`.
3. `src/services/api.ts` posts the file to `/api/detect`.
4. The backend saves the upload, runs detection, annotates frames, and writes a processed video.
5. The backend returns summary fields plus a `detections` array.
6. The frontend navigates to `/results` and renders the returned data.

## API Base URL

The frontend uses:

- `VITE_API_BASE_URL` when set
- Otherwise `http://localhost:5000` as a fallback in code

If you start the included FastAPI backend with `uvicorn`, its default local URL is usually:

```text
http://localhost:8000
```

## Endpoint

### `POST /api/detect`

Uploads one video file for analysis.

### Request

- Content type: `multipart/form-data`
- Field name: `video`

### Successful Response

```json
{
  "status": "success",
  "processed_video_url": "/processed/job123.mp4",
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
        "x": 123.5,
        "y": 88.1
      },
      "confidence": 0.96
    }
  ]
}
```

## Shared Data Shape

The frontend and backend align on these fields:

### Detection result

```ts
{
  id: string;
  frame: number;
  timestamp: string;
  distance_m: number;
  coordinates: {
    x: number;
    y: number;
  };
  confidence: number;
}
```

### Detection response

```ts
{
  status: string;
  processed_video_url: string;
  total_frames: number;
  processing_time: number;
  fod_detected: boolean;
  detections: DetectionResult[];
}
```

## Other Backend Endpoints

### `GET /health`

Returns:

```json
{
  "status": "ok"
}
```

## Error Handling Notes

The route currently raises:

- `400` for invalid upload data or validation errors
- `500` for runtime processing failures

The frontend converts Axios errors into readable messages before surfacing them in the UI.

## Operational Notes

- Processed videos are exposed from `/processed`
- Uploaded files are stored under `backend/uploads`
- Generated output files are stored under `backend/processed`
- The detector expects a model file at `backend/models/fod_model.pt`

## Current Mismatch To Be Aware Of

One configuration detail still requires attention during local setup:

- Frontend fallback URL in code: `http://localhost:5000`
- Default `uvicorn` backend URL: `http://localhost:8000`

Set `VITE_API_BASE_URL` explicitly to avoid that mismatch.
