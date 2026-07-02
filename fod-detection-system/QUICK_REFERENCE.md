# Quick Reference

## Project Root

```text
E:\IAF\fod-detection-system
```

## Common Commands

### Frontend

```bash
npm install
npm run dev
npm run build
npm run preview
npm run lint
```

### Backend

```bash
cd backend
pip install -r hawkeye/requirements.txt
uvicorn app:app --reload
```

## Default Local URLs

- Frontend dev server: `http://localhost:5173`
- Backend health check: `http://localhost:8000/health`
- Processed video base path: `http://localhost:8000/processed`
- Live detection page: `http://localhost:5173/live`

## Important Env Var

```env
VITE_API_BASE_URL=http://localhost:8000
```

## Key Files

### Frontend

- `src/App.tsx`
- `src/services/api.ts`
- `src/types/detection.ts`
- `src/styles/theme.ts`
- `src/components/`
- `src/pages/`

### Backend

- `backend/app.py`
- `backend/routes/detect.py`
- `backend/models/schemas.py`
- `backend/services/video_processor.py`
- `backend/config/camera_calibration.json`

## Routes

| Route | Purpose |
|---|---|
| `/` | Video upload |
| `/processing` | Progress state |
| `/results` | Output review |
| `/live` | Live camera/WebSocket monitoring |

## API

### Request

`POST /api/detect`

- content type: `multipart/form-data`
- field: `video`

### Response fields

- `status`
- `processed_video_url`
- `total_frames`
- `processing_time`
- `fod_detected`
- `detections`

## Detection Fields

- `id`
- `frame`
- `timestamp`
- `distance_m`
- `coordinates.x`
- `coordinates.y`
- `confidence`

## Troubleshooting

### Frontend cannot reach backend

- Check `.env`
- Confirm the backend port
- Restart the frontend after changing env vars

### Build issues

```bash
npx tsc --noEmit
npm run build
```

### Backend health check

```bash
curl http://localhost:8000/health
```
