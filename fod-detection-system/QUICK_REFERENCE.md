# ⚡ Quick Reference Card

## 🎯 Project Location
```
📁 e:\IAF\fod-detection-system\
```

## 🚀 Getting Started (3 Steps)

### Step 1: Navigate
```bash
cd e:\IAF\fod-detection-system
```

### Step 2: Configure (if needed)
```bash
copy .env.example .env
# Edit .env and set backend URL
```

### Step 3: Run
```bash
npm install      # First time only
npm run dev      # Start dev server
```

**Open Browser**: `http://localhost:5173`

## 📝 npm Commands

| Command | Purpose | Output |
|---------|---------|--------|
| `npm run dev` | Start dev server | http://localhost:5173 |
| `npm run build` | Production build | `./dist/` folder |
| `npm run preview` | Test prod build | http://localhost:4173 |
| `npm install` | Install dependencies | `node_modules/` folder |

## 🗂️ Key Files

### Configuration
- `.env` - Environment variables
- `vite.config.ts` - Build configuration
- `tsconfig.json` - TypeScript settings
- `index.html` - HTML entry point

### Source Code Structure
```
src/
├── components/     6 reusable UI components
├── pages/         3 main pages
├── services/      API client
├── types/         TypeScript interfaces
├── styles/        Theme configuration
└── App.tsx        Router setup
```

### Documentation
- `README.md` - Project overview
- `SETUP_GUIDE.md` - Setup instructions
- `API_ARCHITECTURE.md` - API spec
- `PROJECT_COMPLETE.md` - Completion summary

## 🔌 Backend API Expected

**Endpoint**: `POST /api/detect`

**Environment Variable**:
```env
VITE_API_BASE_URL=http://localhost:5000
```

**Request**: Upload MP4/AVI/MOV file

**Response**: JSON with detections data

## 🎨 Main Pages

| Route | Purpose | Features |
|-------|---------|----------|
| `/` | Upload | Drag-drop, preview |
| `/processing` | Processing | Progress bar, steps |
| `/results` | Results | Video, table, export |

## 📊 Main Components

| Component | Purpose | Location |
|-----------|---------|----------|
| VideoUploader | File upload | `/components` |
| VideoPlayer | Video controls | `/components` |
| ProcessingStatus | Progress | `/components` |
| DetectionSummary | Summary cards | `/components` |
| AlertBanner | FOD warning | `/components` |
| FODTable | Results table | `/components` |

## 🛠️ Customization Locations

| What | Where |
|-----|-------|
| **Colors** | `src/styles/theme.ts` |
| **Text** | Component files (search/replace) |
| **Layout** | Component `sx` props |
| **API URL** | `.env` file |
| **File limits** | `src/components/VideoUploader.tsx` |

## 🔧 Troubleshooting

### Dev Server Won't Start
```bash
npm cache clean --force
npm install
npm run dev
```

### Build Errors
```bash
npx tsc --noEmit    # Check TypeScript
npm run build       # Full build test
```

### API Connection Issues
1. Check `.env` has correct API URL
2. Verify backend server running
3. Check CORS enabled on backend
4. Check browser console for errors

## 📦 Deployment

### Quick Build
```bash
npm run build
# Output: ./dist/ folder (ready for hosting)
```

### Docker
```dockerfile
FROM node:18-alpine
WORKDIR /app
COPY . .
RUN npm install && npm run build
EXPOSE 3000
```

### Nginx
```nginx
server {
  listen 80;
  root /usr/share/nginx/html;
  try_files $uri /index.html;
}
```

## 🌐 Supported Browsers

- Chrome 90+
- Firefox 88+
- Safari 14+
- Edge 90+

## 📱 Responsive Breakpoints

- **Mobile**: 0-600px (xs, sm)
- **Tablet**: 600-960px (md)
- **Desktop**: 960px+ (lg, xl)

## 🎯 Development Workflow

1. **Start dev server**
   ```bash
   npm run dev
   ```

2. **Edit files** - HMR auto-refreshes

3. **Build for production**
   ```bash
   npm run build
   ```

4. **Test build**
   ```bash
   npm run preview
   ```

## 📊 Project Stats

- **Components**: 6 custom
- **Pages**: 3 main
- **TypeScript**: Full coverage
- **Bundle**: 610KB (193KB gzipped)
- **Build Time**: ~2 seconds
- **Dependencies**: 31 packages

## 🔑 Environment Variables

```env
# Required
VITE_API_BASE_URL=http://localhost:5000

# Optional
VITE_DEBUG=false
```

## 📚 Documentation Files

1. **README.md** (5 min read)
   - Features overview
   - Project structure
   - Getting started

2. **SETUP_GUIDE.md** (10 min read)
   - Installation steps
   - Customization guide
   - Troubleshooting

3. **API_ARCHITECTURE.md** (15 min read)
   - System architecture
   - Data flow
   - API specification

4. **PROJECT_COMPLETE.md** (5 min read)
   - Completion summary
   - Project statistics
   - Next steps

## ✨ Features Summary

✅ Drag-and-drop video upload
✅ Real-time processing status
✅ AI-powered FOD detection
✅ Comprehensive results dashboard
✅ Searchable detection table
✅ Export results to JSON
✅ Dark theme for airport ops
✅ Responsive design
✅ Professional UI
✅ Full TypeScript support

## 🎉 Ready to Use!

The application is production-ready and can be:
- Deployed immediately
- Customized for your airport
- Integrated with any backend
- Extended with additional features

---

**Quick Start**: `npm run dev`  
**Build**: `npm run build`  
**Docs**: See README.md, SETUP_GUIDE.md, API_ARCHITECTURE.md
