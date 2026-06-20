# 🎯 START HERE - FOD Detection System

## What You Have

✅ **Frontend: COMPLETE**
- React + TypeScript web app
- Fully functional UI with all pages
- Ready to receive video results
- Waiting for backend API

✅ **Backend: COMPLETE**
- FastAPI server with modular architecture
- YOLO model integration ready
- Professional camera calibration
- Advanced 3D distance calculation
- Video annotation and encoding

---

## 🚀 Quick Start (10 minutes)

### 1. Verify Frontend Works
```bash
cd fod-detection-system
npm install
npm run dev
```
Open http://localhost:5173 - You should see upload page

### 2. Create Backend (Choose One)

#### Option A: FastAPI (RECOMMENDED) - 5 minutes
```bash
# Create backend folder
mkdir backend
cd backend

# Copy template
cp ../MINIMAL_BACKEND.py main.py

# Install dependencies
pip install fastapi uvicorn python-multipart opencv-python torch

# Edit main.py:
# 1. Replace DummyModel with your model loading code
# 2. Update pixel_to_world() with your camera parameters
# 3. Save your model file to: models/your_model.pt

# Run backend
python main.py
```

#### Option B: Use Full Example
```bash
# See BACKEND_EXAMPLE.md for complete implementation
# with config.py, calibration.py, model_loader.py, etc.
```

### 3. Connect Frontend to Backend
Update `.env` in frontend:
```env
VITE_API_BASE_URL=http://localhost:5000
```

### 4. Test End-to-End
- Go to http://localhost:5173
- Upload a test video
- Click "Run Detection"
- See results!

---

## 📚 Documentation Map

### Frontend Setup & Configuration
- **[SETUP_GUIDE.md](./SETUP_GUIDE.md)** - Detailed installation steps
- **[QUICK_REFERENCE.md](./QUICK_REFERENCE.md)** - Component API reference

### Understanding the System
- **[API_ARCHITECTURE.md](./API_ARCHITECTURE.md)** - How frontend-backend communicate
- **[PROJECT_COMPLETE.md](./PROJECT_COMPLETE.md)** - What's built and verified

### Backend Implementation (YOUR ML MODEL)
1. **[MODEL_INTEGRATION_GUIDE.md](./MODEL_INTEGRATION_GUIDE.md)** ⭐ **START HERE**
   - 5-minute overview of what backend needs to do
   - Simple code examples
   - Explains pixel-to-world conversion

2. **[MINIMAL_BACKEND.py](./MINIMAL_BACKEND.py)** - Starter template
   - Copy this file to get started
   - Only 60 lines
   - Update model loading + camera parameters

3. **[BACKEND_EXAMPLE.md](./BACKEND_EXAMPLE.md)** - Complete working example
   - All modules organized (config, calibration, model_loader, etc.)
   - Production-ready structure
   - Multiple backend options (FastAPI, Flask, Node.js)

4. **[BACKEND_IMPLEMENTATION_GUIDE.md](./BACKEND_IMPLEMENTATION_GUIDE.md)** - Deep dive
   - Detailed explanations
   - Camera calibration methodology
   - Multiple deployment options

### Getting Started Checklist
- **[IMPLEMENTATION_CHECKLIST.md](./IMPLEMENTATION_CHECKLIST.md)** - Step-by-step checklist
  - What's done (frontend)
  - What needs doing (backend)
  - QA verification steps

---

## Your ML Model

### What Your Model Should Do
```python
def model.predict(frame):
    """
    Input:  numpy array (Height, Width, 3) BGR image from video
    Output: List of detected objects
    [
        {
            'x': int,          # left edge pixel
            'y': int,          # top edge pixel  
            'w': int,          # width in pixels
            'h': int,          # height in pixels
            'confidence': float # 0.0 to 1.0
        },
        ...
    ]
    """
```

### Where to Put Model File
```
your-backend/
├── models/
│   └── fod_detection_model.pt  ← YOUR MODEL HERE
├── main.py
└── ...
```

### Update Model Loading Code
In your backend (main.py or similar):
```python
# Load your model
model = torch.load('models/fod_detection_model.pt')
model.eval()

# Make it match the interface above
def predict_frame(frame):
    # Your model inference
    output = model(frame)
    # Convert to required format
    return [{'x': ..., 'y': ..., 'w': ..., 'h': ..., 'confidence': ...}, ...]
```

---

## Key Task: Pixel-to-Real-World Conversion

The backend must convert pixel coordinates to real-world distance.

### Simple Example
```python
def pixel_to_world(pixel_x, pixel_y, frame_width, frame_height):
    """Convert pixel position to runway distance"""
    
    # YOUR CAMERA PARAMETERS (ADJUST THESE!)
    camera_height_m = 3.5      # How high is camera above runway? (meters)
    camera_fov_x = 60          # Horizontal field of view (degrees)
    camera_fov_y = 45          # Vertical field of view (degrees)
    camera_tilt = 30           # Angle looking down (degrees)
    
    # Normalize pixel to angle
    norm_x = (pixel_x - frame_width/2) / (frame_width/2)
    norm_y = (pixel_y - frame_height/2) / (frame_height/2)
    
    angle_x = norm_x * (camera_fov_x / 2)
    angle_y = norm_y * (camera_fov_y / 2)
    
    # Project to runway plane using trigonometry
    import math
    angle_to_ground = math.radians(camera_tilt + angle_y)
    distance_m = camera_height_m / math.tan(angle_to_ground)
    
    return {
        'distance_m': distance_m,
        'x': distance_m * math.tan(math.radians(angle_x)),
        'y': distance_m
    }
```

**CRITICAL**: Adjust these values for YOUR specific camera:
- `camera_height_m` - Measure actual distance above runway
- `camera_fov_x` / `camera_fov_y` - Check camera specs
- `camera_tilt` - Measure angle camera is pointed

---

## Project Structure

### Frontend (React)
```
fod-detection-system/
├── src/
│   ├── components/          # 6 reusable React components
│   ├── pages/              # 3 pages (Upload, Processing, Results)
│   ├── services/           # api.ts - calls backend
│   ├── types/              # TypeScript interfaces
│   └── styles/             # Material-UI theme
├── .env                    # Backend URL configuration
└── package.json
```

### Backend (Your Implementation)
```
backend/
├── models/
│   └── fod_detection_model.pt  ← YOUR MODEL
├── uploads/                    # Processed video output
├── temp/                       # Temporary files
├── main.py                     # Main server (FastAPI/Flask/etc)
├── requirements.txt            # Python dependencies
└── [optional] config.py, model_loader.py, etc.
```

---

## 🎯 Implementation Steps

### Step 1: Verify Frontend (5 min)
```bash
cd fod-detection-system
npm install
npm run dev
# See it running at http://localhost:5173
```

### Step 2: Set Up Backend (5 min)
```bash
mkdir backend
cd backend
cp ../MINIMAL_BACKEND.py main.py
pip install fastapi uvicorn python-multipart opencv-python torch
```

### Step 3: Integrate Your Model (10 min)
Edit `main.py`:
1. Find `class DummyModel:` and replace with your model loading
2. Find `pixel_to_world()` and adjust camera parameters
3. Save model to `models/fod_detection_model.pt`

### Step 4: Test Backend (5 min)
```bash
python main.py
# Should see: "🚀 Starting FOD Detection API..."
```

### Step 5: Connect Frontend (2 min)
Update `.env`:
```env
VITE_API_BASE_URL=http://localhost:5000
```

### Step 6: End-to-End Test (5 min)
- Open http://localhost:5173
- Upload video
- See results!

---

## 💾 Files You Need to Edit

### Frontend
- ✅ `.env` - Update `VITE_API_BASE_URL`

### Backend (YOUR RESPONSIBILITY)
- `models/` - Place your model file here
- `main.py` - Add model loading code
- `main.py` - Update `pixel_to_world()` with camera parameters

---

## 🔍 What Goes Wrong & How to Fix

### "Cannot find module '@mui/material'"
```bash
npm install
```

### "Backend not responding"
1. Is backend running? `python main.py`
2. Is `.env` URL correct? `VITE_API_BASE_URL=http://localhost:5000`
3. Check backend logs for errors

### "No detections found"
1. Is model file in correct location? `models/fod_detection_model.pt`
2. Does model.predict() return correct format?
3. Add debug print to check model output

### "Distances look wrong"
1. Camera parameters in `pixel_to_world()` wrong
2. Adjust `camera_height_m`, `camera_fov_x`, `camera_tilt`
3. Test with known objects to calibrate

---

## ✨ Summary

| What | Status | Your Action |
|------|--------|-------------|
| Frontend React app | ✅ DONE | Just run `npm run dev` |
| UI components | ✅ DONE | No changes needed |
| Routes & pages | ✅ DONE | No changes needed |
| Backend framework | ⏳ TODO | Use MINIMAL_BACKEND.py |
| ML model loading | ⏳ TODO | Add your model loading |
| Coordinate conversion | ⏳ TODO | Update camera parameters |
| Video processing | ⏳ TODO | Implement frame loop |
| API endpoint | ⏳ TODO | Use template provided |

---

## 🎓 Learning Path

1. **5 min**: Read [MODEL_INTEGRATION_GUIDE.md](./MODEL_INTEGRATION_GUIDE.md)
2. **10 min**: Copy [MINIMAL_BACKEND.py](./MINIMAL_BACKEND.py)
3. **15 min**: Edit with your model + camera params
4. **5 min**: Test

**Total: ~35 minutes to working system**

---

## 📞 Need Help?

- **Questions about frontend?** See [API_ARCHITECTURE.md](./API_ARCHITECTURE.md)
- **Questions about backend?** See [BACKEND_IMPLEMENTATION_GUIDE.md](./BACKEND_IMPLEMENTATION_GUIDE.md)
- **Want complete example?** See [BACKEND_EXAMPLE.md](./BACKEND_EXAMPLE.md)
- **Step-by-step checklist?** See [IMPLEMENTATION_CHECKLIST.md](./IMPLEMENTATION_CHECKLIST.md)

---

**Ready? Start with [MODEL_INTEGRATION_GUIDE.md](./MODEL_INTEGRATION_GUIDE.md)** ⭐

Then use [MINIMAL_BACKEND.py](./MINIMAL_BACKEND.py) as your template. Good luck! 🚀
