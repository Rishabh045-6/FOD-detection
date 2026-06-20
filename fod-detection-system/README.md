# Airport FOD Detection System

A modern web application for detecting Foreign Object Debris (FOD) on airport runways using AI-powered video analysis.

## 🎯 Features

- **Video Upload**: Drag-and-drop or click to upload MP4, AVI, or MOV videos (up to 1GB)
- **Real-time Processing**: Live progress tracking with detailed processing steps
- **AI Detection**: Identify FOD with confidence scores and location data
- **Comprehensive Dashboard**: 
  - Processed video playback with bounding boxes
  - Detection summary cards
  - Detailed FOD table with sortable columns
  - Alert banners for critical warnings
- **Export Results**: Download detection results in JSON format
- **Responsive Design**: Optimized for desktop and tablet displays
- **Dark Theme**: Professional airport operations dashboard appearance

## 🛠️ Technology Stack

- **Frontend Framework**: React 18 + TypeScript
- **Build Tool**: Vite
- **UI Library**: Material-UI (MUI) with custom dark theme
- **HTTP Client**: Axios
- **Routing**: React Router v7
- **Notifications**: React Toastify
- **Styling**: Emotion (MUI default)

## 📦 Project Structure

```
fod-detection-system/
├── src/
│   ├── components/          # Reusable UI components
│   │   ├── VideoUploader.tsx
│   │   ├── VideoPlayer.tsx
│   │   ├── ProcessingStatus.tsx
│   │   ├── DetectionSummary.tsx
│   │   ├── AlertBanner.tsx
│   │   ├── FODTable.tsx
│   │   └── index.ts
│   ├── pages/              # Page components
│   │   ├── UploadPage.tsx
│   │   ├── ProcessingPage.tsx
│   │   ├── ResultsPage.tsx
│   │   └── index.ts
│   ├── services/           # API services
│   │   └── api.ts
│   ├── types/              # TypeScript interfaces
│   │   └── detection.ts
│   ├── styles/             # Theme configuration
│   │   └── theme.ts
│   ├── App.tsx
│   ├── main.tsx
│   └── index.css
├── .env                    # Environment variables (dev)
├── .env.example            # Example environment variables
├── vite.config.ts
├── tsconfig.json
├── index.html
└── package.json
```

## 🚀 Getting Started

### Prerequisites

- Node.js 16.x or higher
- npm 7.x or higher

### Installation

1. **Clone or navigate to the project directory**
   ```bash
   cd fod-detection-system
   ```

2. **Install dependencies**
   ```bash
   npm install
   ```

3. **Configure environment variables**
   ```bash
   cp .env.example .env
   ```
   
   Edit `.env` and set your backend API URL:
   ```env
   VITE_API_BASE_URL=http://localhost:5000
   ```

### Development

Start the development server:

```bash
npm run dev
```

The application will be available at `http://localhost:5173`

### Building for Production

```bash
npm run build
```

The optimized production build will be created in the `dist/` directory.

### Preview Production Build

```bash
npm run preview
```

## 📱 Application Flow

### 1. **Upload Page** (`/`)
- Display application title and features
- Drag-and-drop or click to upload video
- Show file details (name, size)
- Display video preview
- "Run Detection" button

### 2. **Processing Page** (`/processing`)
- Display upload progress
- Show processing status with steps:
  - Uploading Video
  - Extracting Frames
  - Running Detection
  - Calculating Distance
  - Generating Results
- Disable user interactions during processing

### 3. **Results Page** (`/results`)
- Display processed video with bounding boxes
- Show detection summary (frames, FOD count, status, time)
- Display alert banner (red for FOD, green for clear)
- Show detailed FOD table with search and pagination
- Export results button
- Analyze another video link

## 🔌 Backend API Integration

The application expects a backend API at the URL specified in `VITE_API_BASE_URL`.

### Expected API Endpoint

**POST** `/api/detect`

**Request:**
```
Content-Type: multipart/form-data
video: File
```

**Response:**
```json
{
  "status": "success",
  "processed_video_url": "https://...",
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

## 🎨 Customization

### Dark Theme

The application uses a custom dark theme suitable for airport operations. To customize colors, edit `src/styles/theme.ts`:

```typescript
palette: {
  primary: {
    main: '#00bcd4',      // Cyan
    light: '#4dd0e1',
    dark: '#0097a7',
  },
  secondary: {
    main: '#ff6f00',      // Orange
    light: '#ffb74d',
    dark: '#e65100',
  },
  // ... more colors
}
```

### Component Styling

All components use Material-UI's `sx` prop for styling. To modify component appearance, edit the respective component files in `src/components/`.

## 📊 Key Components

### VideoUploader
- File drag-and-drop support
- File validation (format, size)
- Preview thumbnail
- Progress indication

### VideoPlayer
- Play/Pause controls
- Seek bar
- Volume control
- Mute button
- Time display

### ProcessingStatus
- Step-by-step progress visualization
- Overall progress bar
- Error handling and display
- Current step indicator

### DetectionSummary
- 4 summary cards:
  - Total Frames Processed
  - Total FOD Detected
  - Detection Status
  - Processing Time

### AlertBanner
- Red banner for FOD detected (critical warning)
- Green banner for no FOD (runway clear)
- Closest object details
- Number of detections

### FODTable
- Sortable and paginated table
- Search functionality
- 7 columns: ID, Frame, Timestamp, Distance, X, Y, Confidence
- Color-coded confidence levels

## 🔐 Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `VITE_API_BASE_URL` | Backend API base URL | `http://localhost:5000` |
| `VITE_DEBUG` | Enable debug mode | `false` |

## 🧪 Error Handling

The application includes comprehensive error handling:

- **File Validation**: Format and size checking
- **Network Errors**: Graceful error messages with retry option
- **API Errors**: Detailed error notifications
- **Toast Notifications**: User-friendly feedback for all actions

## 📈 Performance Considerations

- Large video uploads (up to 1GB) use streaming
- Progress callbacks for real-time feedback
- Lazy loading of components
- Optimized re-renders using React hooks
- CSS-in-JS for dynamic styling

## 📚 Documentation

### Frontend Setup
- **[SETUP_GUIDE.md](./SETUP_GUIDE.md)** - Installation, configuration, and customization
- **[QUICK_REFERENCE.md](./QUICK_REFERENCE.md)** - Developer quick reference

### System Design & Integration
- **[API_ARCHITECTURE.md](./API_ARCHITECTURE.md)** - System design and data flow
- **[PROJECT_COMPLETE.md](./PROJECT_COMPLETE.md)** - Project completion summary
- **[BUILD_SUMMARY.md](./BUILD_SUMMARY.md)** - Build verification and next steps

### Backend Implementation (Your ML Model Integration)
- **[MODEL_INTEGRATION_GUIDE.md](./MODEL_INTEGRATION_GUIDE.md)** ⭐ **START HERE** - Quick guide for integrating your ML model
- **[MINIMAL_BACKEND.py](./MINIMAL_BACKEND.py)** - Simple working backend template (60 lines)
- **[BACKEND_IMPLEMENTATION_GUIDE.md](./BACKEND_IMPLEMENTATION_GUIDE.md)** - Complete backend guide with multiple backend options
- **[BACKEND_EXAMPLE.md](./BACKEND_EXAMPLE.md)** - Complete working backend example with all modules

## 🌐 Browser Support

- Chrome/Chromium 90+
- Firefox 88+
- Safari 14+
- Edge 90+

## 📝 License

This project is proprietary and intended for airport operations use.

## 👨‍💼 Support

For issues, questions, or feature requests, please contact the development team.

---

**Note**: This is a frontend-only application. A backend API must be deployed separately to handle video processing and FOD detection.
