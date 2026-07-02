# Start Here

## Fastest Path

1. Install frontend dependencies.
2. Set the frontend API URL.
3. Install backend dependencies.
4. Add the YOLO model file.
5. Run both services.
6. Upload a test video.

## Commands

### Frontend

```bash
cd E:\IAF\fod-detection-system
npm install
npm run dev
```

### Backend

```bash
cd E:\IAF\fod-detection-system\backend
pip install -r hawkeye/requirements.txt
uvicorn app:app --reload
```

If the backend port differs, start uvicorn with `--port <port>`.

## Required Environment Setting

Create or update `.env` with:

```env
VITE_API_BASE_URL=http://localhost:8000
```

If your backend runs on another port, adjust the URL accordingly.

## What Is Already In The Repo

### Frontend

- Upload page
- Processing page
- Results page
- Detection summary UI
- Alert banner
- Video player
- Results table

### Backend

- FastAPI app
- `/api/detect` route
- `/api/live` control routes
- WebSocket live stream scaffolding
- Detector service
- Video processor
- Calibration config
- Health endpoint

## What You Still Need

- A working Python environment
- FFmpeg installed
- A trained YOLO model at `backend/models/fod_model.pt`
- A valid `.env` value for `VITE_API_BASE_URL`

## First Checks To Run

### Frontend build

```bash
npm run build
```

### Backend health

```bash
curl http://localhost:8000/health
```

## If Something Fails

- Read [SETUP_GUIDE.md](./SETUP_GUIDE.md) for setup details
- Read [API_ARCHITECTURE.md](./API_ARCHITECTURE.md) for request and response flow
- Read [IMPLEMENTATION_CHECKLIST.md](./IMPLEMENTATION_CHECKLIST.md) for verification steps
- Read [backend/README.md](./backend/README.md) for backend-specific notes
