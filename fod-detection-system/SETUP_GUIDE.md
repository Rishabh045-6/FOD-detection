# Airport FOD Detection System - Setup Guide

## Quick Start

### Prerequisites
- Node.js 16.x or higher
- npm 7.x or higher
- Modern web browser (Chrome, Firefox, Safari, or Edge)

### Installation Steps

1. **Navigate to the project directory**
   ```bash
   cd e:\IAF\fod-detection-system
   ```

2. **Install dependencies** (if not already done)
   ```bash
   npm install
   ```

3. **Set up environment configuration**
   ```bash
   # Copy the example environment file
   cp .env.example .env
   ```

4. **Configure backend API URL**
   Edit `.env` and update the API base URL:
   ```env
   # Development backend
   VITE_API_BASE_URL=http://localhost:5000
   
   # Or production backend
   VITE_API_BASE_URL=https://api.yourairport.com
   ```

### Running the Application

**Development Mode:**
```bash
npm run dev
```
Open browser to `http://localhost:5173`

**Production Build:**
```bash
npm run build
npm run preview
```

## Project Structure

```
fod-detection-system/
├── src/
│   ├── components/           # Reusable React components
│   │   ├── VideoUploader.tsx      # Video file upload with drag-drop
│   │   ├── VideoPlayer.tsx        # Video playback controls
│   │   ├── ProcessingStatus.tsx   # Processing progress display
│   │   ├── DetectionSummary.tsx   # Summary cards
│   │   ├── AlertBanner.tsx        # FOD warning/clear banners
│   │   ├── FODTable.tsx           # Detection table with search/pagination
│   │   └── index.ts
│   ├── pages/                # Page-level components
│   │   ├── UploadPage.tsx        # Initial upload interface
│   │   ├── ProcessingPage.tsx    # Real-time processing status
│   │   ├── ResultsPage.tsx       # Results dashboard
│   │   └── index.ts
│   ├── services/             # API communication
│   │   └── api.ts                # Axios-based API client
│   ├── types/                # TypeScript interfaces
│   │   └── detection.ts          # Detection data types
│   ├── styles/               # Theme configuration
│   │   └── theme.ts              # Material-UI dark theme
│   ├── App.tsx               # Main app component with routing
│   ├── main.tsx              # React entry point
│   └── index.css             # Global styles
├── public/                   # Static assets
├── dist/                     # Production build output
├── .env                      # Environment variables (dev)
├── .env.example              # Environment template
├── vite.config.ts            # Vite build configuration
├── tsconfig.json             # TypeScript configuration
├── index.html                # HTML entry point
└── package.json              # Dependencies and scripts
```

## Application Features

### 1. Upload Page (`/`)
- **Drag-and-drop video upload** - Click or drag video files to upload area
- **File validation** - Accepts MP4, AVI, MOV up to 1GB
- **Video preview** - See selected video before processing
- **File information** - Displays file name and size
- **Run Detection button** - Starts processing pipeline

### 2. Processing Page (`/processing`)
- **Real-time progress** - Visual progress bar with percentage
- **Processing steps** - Shows current processing stage:
  - Uploading Video
  - Extracting Frames
  - Running Detection
  - Calculating Distance
  - Generating Results
- **Upload progress** - Live upload percentage display
- **Error handling** - Displays errors with details
- **Auto-navigation** - Automatically navigates to results on success

### 3. Results Page (`/results`)
- **Processed video playback** - Watch annotated video with detections
- **Detection summary** - 4 cards showing:
  - Total frames processed
  - FOD objects detected
  - Detection status (Critical/Normal)
  - Processing time
- **Alert banner**:
  - Red "FOD DETECTED" - if debris found
  - Green "RUNWAY CLEAR" - if no debris
- **Detailed table**:
  - Search by FOD ID or timestamp
  - Pagination (5, 10, 25, 50 items per page)
  - Sortable columns
  - Color-coded confidence levels
- **Export results** - Download JSON file with full data
- **Analyze another video** - Return to upload page

## Backend API Integration

The application communicates with a backend API for video processing.

### Expected API Endpoint

**Endpoint:** `POST /api/detect`

**Request Headers:**
```
Content-Type: multipart/form-data
```

**Request Body:**
```
FormData:
  - video: File (MP4, AVI, or MOV)
```

**Response Format:**
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
    },
    {
      "id": "FOD-002",
      "frame": 340,
      "timestamp": "00:00:12",
      "distance_m": 55.3,
      "coordinates": {
        "x": 18.7,
        "y": 22.1
      },
      "confidence": 0.88
    }
  ]
}
```

### Response Field Descriptions

| Field | Type | Description |
|-------|------|-------------|
| status | string | "success" or "error" |
| processed_video_url | string | URL of video with bounding boxes drawn |
| total_frames | number | Total frames processed |
| processing_time | number | Total time in seconds |
| fod_detected | boolean | Whether any FOD was detected |
| detections | array | Array of detected FOD objects |
| detections[].id | string | Unique FOD identifier (e.g., "FOD-001") |
| detections[].frame | number | Frame number where detected |
| detections[].timestamp | string | HH:MM:SS timestamp |
| detections[].distance_m | number | Distance from camera in meters |
| detections[].coordinates.x | number | X coordinate |
| detections[].coordinates.y | number | Y coordinate |
| detections[].confidence | number | Confidence score (0.0 - 1.0) |

## Environment Variables

Create a `.env` file in the project root:

```env
# Backend API URL
VITE_API_BASE_URL=http://localhost:5000

# Debug mode (optional)
VITE_DEBUG=false
```

### Variable Definitions

| Variable | Purpose | Default |
|----------|---------|---------|
| `VITE_API_BASE_URL` | Backend API base URL | `http://localhost:5000` |
| `VITE_DEBUG` | Enable debug logging | `false` |

## Customization

### Changing Colors

Edit `src/styles/theme.ts`:

```typescript
palette: {
  primary: {
    main: '#00bcd4',      // Primary cyan color
    light: '#4dd0e1',
    dark: '#0097a7',
  },
  secondary: {
    main: '#ff6f00',      // Secondary orange
    light: '#ffb74d',
    dark: '#e65100',
  },
  error: {
    main: '#f44336',      // Error red
  },
  success: {
    main: '#4caf50',      // Success green
  },
  warning: {
    main: '#ff9800',      // Warning orange
  },
  // ... more colors
}
```

### Modifying UI Components

Each component is self-contained in `src/components/`:

1. **VideoUploader.tsx** - Drag-drop upload area, file validation
2. **VideoPlayer.tsx** - Video controls, playback
3. **ProcessingStatus.tsx** - Progress visualization
4. **DetectionSummary.tsx** - Summary cards layout
5. **AlertBanner.tsx** - FOD warning/clear messages
6. **FODTable.tsx** - Results table with search/pagination

Edit any component to customize styling or behavior.

### Adjusting File Size Limits

In `src/components/VideoUploader.tsx`:

```typescript
const MAX_FILE_SIZE = 1024 * 1024 * 1024; // 1GB in bytes
```

Change the value to adjust maximum file size limit.

### Accepted File Formats

In `src/components/VideoUploader.tsx`:

```typescript
const ACCEPTED_FORMATS = ['video/mp4', 'video/x-msvideo', 'video/quicktime'];
```

Add or remove MIME types to change supported formats.

## npm Scripts

| Command | Purpose |
|---------|---------|
| `npm run dev` | Start dev server (http://localhost:5173) |
| `npm run build` | Build for production |
| `npm run preview` | Preview production build locally |
| `npm run lint` | Run ESLint (if configured) |

## Troubleshooting

### Dev Server Won't Start
```bash
# Clear npm cache
npm cache clean --force

# Reinstall dependencies
rm -rf node_modules package-lock.json
npm install

# Try dev server again
npm run dev
```

### Build Fails
```bash
# Check TypeScript errors
npx tsc --noEmit

# Check all files compile
npm run build
```

### API Connection Issues
1. Verify `VITE_API_BASE_URL` in `.env` is correct
2. Check backend server is running
3. Verify CORS is enabled on backend
4. Check browser console for network errors

### Video Upload Fails
1. Verify file format is MP4, AVI, or MOV
2. Check file size is under 1GB
3. Check backend can receive multipart/form-data
4. Verify enough disk space on server

## Browser Compatibility

- ✅ Chrome/Chromium 90+
- ✅ Firefox 88+
- ✅ Safari 14+
- ✅ Edge 90+

## Performance Optimization

For production deployment:

1. **Enable compression** on web server (gzip)
2. **Use CDN** for static assets
3. **Enable caching** headers for dist files
4. **Consider code splitting** for large chunks
5. **Monitor bundle size** - Currently ~610KB (193KB gzipped)

## Deployment

### Docker Example

```dockerfile
FROM node:18-alpine
WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .
RUN npm run build
EXPOSE 3000
CMD ["npm", "run", "preview"]
```

### Nginx Configuration

```nginx
server {
  listen 80;
  server_name your-domain.com;

  location / {
    root /usr/share/nginx/html;
    try_files $uri $uri/ /index.html;
    expires 1d;
    add_header Cache-Control "public, immutable";
  }

  location /api/ {
    proxy_pass http://backend:5000;
  }
}
```

## Development Workflow

1. **Start dev server**
   ```bash
   npm run dev
   ```

2. **Make code changes** - Hot Module Replacement (HMR) enabled

3. **Check TypeScript errors** - Fixed in real-time

4. **Test in browser** - Auto-refresh on save

5. **Build for production**
   ```bash
   npm run build
   ```

6. **Test production build**
   ```bash
   npm run preview
   ```

## Support & Documentation

For more information:
- Material-UI: https://mui.com
- React: https://react.dev
- Vite: https://vitejs.dev
- Axios: https://axios-http.com
- TypeScript: https://www.typescriptlang.org

---

**Version**: 1.0.0  
**Last Updated**: 2026-06-21  
**Status**: Production Ready
