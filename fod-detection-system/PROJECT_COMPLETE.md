# Airport FOD Detection System - Project Status

## Current State

This repository contains a working frontend and a structured backend implementation for runway FOD detection.

### Frontend

- Complete React application with routing
- Upload, processing, and results pages
- Detection summary and searchable results table
- Production build verified

### Backend

- FastAPI server scaffolded and wired
- Detection route implemented
- Detector, calibration, annotation, and video processing services present
- Health endpoint available

## Project Inventory

### Frontend

- React 19
- TypeScript 6
- Vite 8
- Material UI 9
- 6 reusable components
- 3 application pages

### Backend

- FastAPI app entry point in `backend/app.py`
- Route module in `backend/routes/detect.py`
- Response schemas in `backend/models/schemas.py`
- Processing services in `backend/services/`
- Camera calibration file in `backend/config/camera_calibration.json`

## Verified Behavior

- `npm run build` passes
- Frontend routes are defined for `/`, `/processing`, `/results`, and `/live`
- Backend serves `/health`
- Backend mounts `/processed` static output
- Backend has `/api/live` control routes and WebSocket scaffolding
- Frontend and backend share the same response shape for detections

## Remaining Integration Dependencies

The main operational dependency is external model/runtime setup:

- Install backend Python dependencies from `backend/hawkeye/requirements.txt`
- Ensure FFmpeg is available on the machine
- Place the trained model at `backend/models/fod_model.pt`
- Point the frontend to the correct backend base URL

## Important Configuration Note

The backend typically runs on `http://localhost:8000` when started with:

```bash
uvicorn app:app --reload
```

The frontend API base URL is resolved in `src/services/api.ts` using `import.meta.env.VITE_API_BASE_URL`. When unset, the code defaults to `http://localhost:8000`.
## Recommended Next Steps

1. Update `.env` to match your backend port.
2. Install backend requirements from `backend/hawkeye/requirements.txt`.
3. Run both services locally.
4. Upload a test runway video.
5. Validate output video, detections, and distances.

## Documentation Map

- [README.md](./README.md)
- [START_HERE.md](./START_HERE.md)
- [SETUP_GUIDE.md](./SETUP_GUIDE.md)
- [QUICK_REFERENCE.md](./QUICK_REFERENCE.md)
- [API_ARCHITECTURE.md](./API_ARCHITECTURE.md)
- [IMPLEMENTATION_CHECKLIST.md](./IMPLEMENTATION_CHECKLIST.md)
- [BUILD_SUMMARY.md](./BUILD_SUMMARY.md)
- [backend/README.md](./backend/README.md)
