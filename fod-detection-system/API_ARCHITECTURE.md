# Airport FOD Detection System - Architecture & API Documentation

## System Architecture

### High-Level Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                     Frontend (React + TypeScript)               │
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │                    Browser (Vite Dev Server)             │  │
│  │                                                          │  │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐             │  │
│  │  │ Upload   │  │Processing│  │ Results  │             │  │
│  │  │ Page     │→ │ Page     │→ │ Page     │             │  │
│  │  └──────────┘  └──────────┘  └──────────┘             │  │
│  │                                                          │  │
│  │  ┌──────────────────────────────────────────────────┐  │  │
│  │  │         React Router                            │  │  │
│  │  │   - Route: /                                    │  │  │
│  │  │   - Route: /processing                          │  │  │
│  │  │   - Route: /results                             │  │  │
│  │  └──────────────────────────────────────────────────┘  │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │            Services Layer                            │  │
│  │                                                       │  │
│  │  ┌──────────────────────────────────────────────┐    │  │
│  │  │  api.ts - Axios HTTP Client                 │    │  │
│  │  │  - uploadVideoForDetection()                │    │  │
│  │  │  - Progress tracking callback               │    │  │
│  │  └──────────────────────────────────────────────┘    │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │            UI Components Layer                       │  │
│  │                                                       │  │
│  │  ┌─────────┐ ┌──────────┐ ┌────────────────┐        │  │
│  │  │VideoUp  │ │VideoPlay │ │ProcessingStatus│        │  │
│  │  │loader   │ │er        │ │                │        │  │
│  │  └─────────┘ └──────────┘ └────────────────┘        │  │
│  │                                                       │  │
│  │  ┌─────────┐ ┌──────────┐ ┌────────────────┐        │  │
│  │  │Detection│ │AlertBan  │ │FODTable        │        │  │
│  │  │Summary  │ │ner       │ │                │        │  │
│  │  └─────────┘ └──────────┘ └────────────────┘        │  │
│  │                                                       │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │            Types & Styling                           │  │
│  │                                                       │  │
│  │  ┌──────────────────────────────────────────────┐    │  │
│  │  │  detection.ts - TypeScript Interfaces       │    │  │
│  │  │  - DetectionResponse                        │    │  │
│  │  │  - DetectionResult                          │    │  │
│  │  │  - ProcessingState                          │    │  │
│  │  └──────────────────────────────────────────────┘    │  │
│  │                                                       │  │
│  │  ┌──────────────────────────────────────────────┐    │  │
│  │  │  theme.ts - Material-UI Dark Theme          │    │  │
│  │  │  - Custom color palette                     │    │  │
│  │  │  - Typography settings                      │    │  │
│  │  │  - Component overrides                      │    │  │
│  │  └──────────────────────────────────────────────┘    │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                              │
                              │ HTTP (Axios)
                              │
                    POST /api/detect
                    multipart/form-data
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                   Backend API (Node/Python/etc)                 │
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  /api/detect Endpoint                                   │  │
│  │  - Receive video file                                   │  │
│  │  - Process with ML model                                │  │
│  │  - Draw bounding boxes                                  │  │
│  │  - Return annotated video & detections                  │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  Processing Pipeline                                     │  │
│  │  1. Video Upload Handler                                 │  │
│  │  2. Frame Extraction                                     │  │
│  │  3. FOD Detection Model                                  │  │
│  │  4. Distance Calculation                                 │  │
│  │  5. Bounding Box Drawing                                 │  │
│  │  6. Video Re-encoding                                    │  │
│  │  7. Result Compilation                                   │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

## Data Flow

### 1. Upload to Processing
```
User Selection
     │
     ▼
VideoUploader Component
     │
     ├─ File Validation (type, size)
     │
     ├─ Preview Generation
     │
     ▼
Navigate to /processing with File
     │
     ▼
ProcessingPage Component
     │
     ├─ Upload Start (progress: 0%)
     │
     ├─ API Call: POST /api/detect
     │     └─ FormData with video file
     │     └─ Progress callback
     │
     ├─ Update Progress Bar
     │
     ├─ Simulate Processing Steps
     │     ├─ Uploading Video (progress: 20%)
     │     ├─ Extracting Frames (progress: 35%)
     │     ├─ Running Detection (progress: 55%)
     │     ├─ Calculating Distance (progress: 75%)
     │     └─ Generating Results (progress: 95%)
     │
     ▼
API Response Received
     │
     ├─ DetectionResponse parsed
     │
     └─ Navigate to /results with data
```

### 2. Results Display
```
ResultsPage Receives Data
     │
     ├─ Display Video Player
     │     └─ Stream processed_video_url
     │
     ├─ Render Alert Banner
     │     ├─ If fod_detected: Red "FOD DETECTED" banner
     │     └─ If !fod_detected: Green "RUNWAY CLEAR" banner
     │
     ├─ Show Summary Cards
     │     ├─ Total Frames Processed
     │     ├─ Total FOD Detected
     │     ├─ Detection Status
     │     └─ Processing Time
     │
     └─ Display FOD Table
           ├─ Search functionality
           ├─ Pagination
           └─ Color-coded confidence
```

## Component Communication

### Data Flow Through Components

```
App.tsx (Router)
│
├─ UploadPage
│  ├─ VideoUploader (State: selectedFile, previewUrl)
│  │   ├─ onFileSelect → navigate to /processing
│  │   └─ onPreviewReady → display preview
│  └─ Triggers: navigation to /processing
│
├─ ProcessingPage
│  ├─ State: processingState (status, progress, message, error)
│  ├─ ProcessingStatus Component
│  │   └─ Displays: progress, steps, errors
│  ├─ Effect: uploadVideoForDetection()
│  │   └─ Updates: processingState
│  └─ Triggers: navigation to /results on success
│
└─ ResultsPage (Location.state.data)
   ├─ AlertBanner
   │   ├─ Props: fodDetected, detections
   │   └─ Displays: Red/Green alert
   ├─ VideoPlayer
   │   ├─ Props: videoUrl
   │   └─ Controls: play, pause, volume, seek
   ├─ DetectionSummary
   │   ├─ Props: totalFrames, totalFODDetected, processingTime
   │   └─ Displays: 4 cards
   └─ FODTable
       ├─ Props: detections
       ├─ Features: search, pagination, sorting
       └─ Displays: detection details table
```

## API Specification

### Base URL
```
Development: http://localhost:5000
Production: https://api.yourairport.com
```

### Endpoint: POST /api/detect

**Purpose**: Upload video for FOD detection and analysis

**Headers**
```http
Content-Type: multipart/form-data
```

**Request Body**
```
FormData with key: "video"
Value: File object (MP4, AVI, or MOV)
```

**cURL Example**
```bash
curl -X POST http://localhost:5000/api/detect \
  -F "video=@runway.mp4" \
  -H "Accept: application/json"
```

**JavaScript/Axios Example**
```typescript
const formData = new FormData();
formData.append('video', fileObject);

const response = await axios.post(
  'http://localhost:5000/api/detect',
  formData,
  {
    headers: { 'Content-Type': 'multipart/form-data' },
    onUploadProgress: (progressEvent) => {
      const percent = (progressEvent.loaded / progressEvent.total) * 100;
      console.log(`Upload ${percent}% complete`);
    },
  }
);
```

**Response: 200 OK**
```json
{
  "status": "success",
  "processed_video_url": "https://storage.example.com/runway_processed_2026_06_21.mp4",
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
    },
    {
      "id": "FOD-002",
      "frame": 512,
      "timestamp": "00:00:17",
      "distance_m": 65.2,
      "coordinates": {
        "x": 245.0,
        "y": 156.3
      },
      "confidence": 0.89
    }
  ]
}
```

**Response: 400 Bad Request**
```json
{
  "status": "error",
  "message": "No video file provided",
  "code": "MISSING_FILE"
}
```

**Response: 413 Payload Too Large**
```json
{
  "status": "error",
  "message": "File size exceeds maximum limit of 1GB",
  "code": "FILE_TOO_LARGE"
}
```

**Response: 415 Unsupported Media Type**
```json
{
  "status": "error",
  "message": "Unsupported video format. Supported: MP4, AVI, MOV",
  "code": "UNSUPPORTED_FORMAT"
}
```

**Response: 500 Internal Server Error**
```json
{
  "status": "error",
  "message": "Video processing failed",
  "code": "PROCESSING_ERROR",
  "details": "Error details here"
}
```

## TypeScript Types

### detection.ts

```typescript
// Coordinate system
interface Coordinates {
  x: number;     // X pixel coordinate
  y: number;     // Y pixel coordinate
}

// Single detection result
interface DetectionResult {
  id: string;              // FOD-001, FOD-002, etc.
  frame: number;           // Frame number (0-indexed)
  timestamp: string;       // HH:MM:SS format
  distance_m: number;      // Distance in meters
  coordinates: Coordinates; // x, y in image
  confidence: number;      // 0.0 - 1.0 confidence score
}

// API response
interface DetectionResponse {
  status: string;              // "success" or "error"
  processed_video_url: string; // URL to annotated video
  total_frames: number;        // Total frames in video
  processing_time: number;     // Time in seconds
  fod_detected: boolean;       // Whether FOD detected
  detections: DetectionResult[]; // Array of detections
}

// Processing state for UI
interface ProcessingState {
  status: 'idle' | 'uploading' | 'extracting' | 'detecting' | 'calculating' | 'generating' | 'complete' | 'error';
  progress: number;    // 0-100
  message: string;     // Current status message
  error?: string;      // Error message if status === 'error'
}

// Upload progress tracking
interface UploadProgress {
  loaded: number;  // Bytes uploaded
  total: number;   // Total bytes
  percent: number; // 0-100 percentage
}
```

## State Management

### ProcessingPage State
```typescript
const [processingState, setProcessingState] = useState<ProcessingState>({
  status: 'uploading',
  progress: 0,
  message: 'Preparing to upload video...',
});

// State transitions:
// 'idle' → 'uploading' → 'extracting' → 'detecting' 
// → 'calculating' → 'generating' → 'complete'
//                                        ↓
//                                     (error)
```

### ResultsPage Props (via Location)
```typescript
interface LocationState {
  data: DetectionResponse;
}

// Accessed via:
const data = (location.state as LocationState)?.data;
```

## Error Handling Strategy

### Frontend Errors
```
File Validation Error
     ↓
VideoUploader → Display inline error
     ↓
User corrects and retries

Upload Error
     ↓
ProcessingPage → Toast notification
     ↓
Auto-redirect to upload after 3s

Network Error
     ↓
API Client catches Axios error
     ↓
Toast notification with error message
     ↓
User can retry
```

### Backend Expected Errors
1. **400 Bad Request** - Missing/invalid parameters
2. **413 Payload Too Large** - File exceeds size limit
3. **415 Unsupported Media Type** - Invalid video format
4. **422 Unprocessable Entity** - Video corrupted/unreadable
5. **500 Internal Server Error** - Processing failed
6. **504 Gateway Timeout** - Processing took too long

## Performance Considerations

### Frontend
- **Bundle Size**: ~610KB (193KB gzipped)
- **Code Splitting**: Single chunk due to Material-UI dependencies
- **Lazy Loading**: Components render on-demand
- **Memoization**: React hooks prevent unnecessary re-renders

### Backend Integration
- **Streaming Upload**: Progress tracking via `onUploadProgress`
- **Timeout**: 10 minutes (600,000ms) for large videos
- **Multipart**: Efficient multipart/form-data handling
- **Cors**: Frontend can be on different domain

### Browser
- **HMR**: Hot Module Replacement in dev mode
- **Scrollbar**: Custom styled scrollbar
- **Video Playback**: Native HTML5 video element
- **Responsive**: CSS Grid layout adapts to screen size

## Security Considerations

### Frontend
- File type validation (client-side only, not sufficient)
- File size validation (client-side only, not sufficient)
- No sensitive data in state
- No credentials stored locally

### Backend (Should Implement)
- Server-side file validation
- Virus/malware scanning
- Rate limiting
- Authentication/authorization
- HTTPS/TLS encryption
- CORS configuration
- Input sanitization

## Deployment Checklist

- [ ] Backend API running and accessible
- [ ] CORS configured on backend
- [ ] Environment variables set correctly
- [ ] Production build passes
- [ ] Tested on target browsers
- [ ] Videos stored securely
- [ ] Error logging configured
- [ ] Performance monitoring active
- [ ] Backup/disaster recovery plan
- [ ] Security audit completed

---

**Document Version**: 1.0  
**Last Updated**: 2026-06-21
