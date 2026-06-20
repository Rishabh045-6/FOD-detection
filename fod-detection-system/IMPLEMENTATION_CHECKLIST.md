# Implementation Checklist

## Documentation Cleanup Status

- [x] Remove broken character encoding from project docs
- [x] Align Markdown with the current repo structure
- [x] Remove references to missing template docs and starter files
- [x] Keep changes limited to existing Markdown files

## Frontend Checklist

- [x] React application present
- [x] TypeScript types defined for detection data
- [x] Upload, processing, and results routes implemented
- [x] API client posts multipart video uploads
- [x] Production build passes

## Backend Checklist

- [x] FastAPI app present
- [x] `/api/detect` route present
- [x] Response schema defined
- [x] Processing services organized under `backend/services/`
- [x] Static processed-video mount configured
- [x] Health endpoint present

## Local Setup Checklist

- [ ] Install frontend dependencies with `npm install`
- [ ] Install backend dependencies with `pip install -r backend/requirements.txt`
- [ ] Ensure FFmpeg is installed
- [ ] Add trained model to `backend/models/fod_model.pt`
- [ ] Set `VITE_API_BASE_URL` in `.env`
- [ ] Start backend from `backend/`
- [ ] Start frontend from the project root

## End-to-End Verification Checklist

- [ ] Open `http://localhost:5173`
- [ ] Upload a supported video file
- [ ] Confirm progress appears on `/processing`
- [ ] Confirm the backend returns a response without error
- [ ] Confirm `/results` shows the processed video
- [ ] Confirm summary cards render correctly
- [ ] Confirm detections appear in the table
- [ ] Confirm JSON export works

## Configuration Checks

- [ ] `.env` points to the correct backend host and port
- [ ] Backend CORS configuration is acceptable for the target environment
- [ ] Camera calibration file is valid for the deployment camera
- [ ] YOLO model path is correct

## Build and Release Checks

- [x] `npm run build` succeeds
- [ ] Review large bundle warning and optimize if needed
- [ ] Validate production environment variables
- [ ] Verify processed video hosting path in deployment

## Known Caveats

- The frontend code falls back to `http://localhost:5000` if `VITE_API_BASE_URL` is not set.
- The included FastAPI backend usually runs on `http://localhost:8000` when started with `uvicorn`.
- Set the environment variable explicitly to avoid local connection issues.
