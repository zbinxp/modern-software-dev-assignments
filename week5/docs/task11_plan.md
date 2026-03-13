# Task 11: Deployable on Vercel (Medium-Complex)

## Overview

Deploy the React frontend on Vercel and the FastAPI backend on an external service (Fly.io).

---

## Recommended Approach: Option B (API on External Service)

### Why Option B?

1. **SQLite Persistence**: Vercel's serverless functions have ephemeral filesystem - SQLite data would be lost on each request
2. **Cold Start Performance**: FastAPI on Vercel's Python runtime has significant cold start latency
3. **Fly.io Benefits**:
   - Native Python support with persistent volumes
   - Can run SQLite with proper persistence
   - Single platform for backend + database
4. **Frontend Optimization**: Vercel excels at static frontend delivery with edge caching

---

## Files to Create/Modify

### 1. Frontend Configuration

**File**: `/home/dd/lab/modern-software-dev-assignments/week5/frontend/vite.config.js` (MODIFY)
- Add `base` configuration for Vercel deployment
- Configure environment variable injection

**File**: `/home/dd/lab/modern-software-dev-assignments/week5/frontend/package.json` (MODIFY - optional)
- Already has build/preview scripts
- Add `vercel` dev dependency if needed

### 2. Vercel Configuration

**File**: `/home/dd/lab/modern-software-dev-assignments/week5/vercel.json` (CREATE)
```json
{
  "framework": "vite",
  "buildCommand": "npm run build",
  "outputDirectory": "dist",
  "rewrites": [
    { "source": "/api/(.*)", "destination": "https://YOUR-BACKEND.fly.dev/$1" },
    { "source": "/(.*)", "destination": "/index.html" }
  ],
  "env": {
    "VITE_API_BASE_URL": "@api-base-url"
  }
}
```

### 3. Backend Configuration for Fly.io

**File**: `/home/dd/lab/modern-software-dev-assignments/week5/Dockerfile` (CREATE)
- Multi-stage build for Python/FastAPI
- Install dependencies from requirements.txt

**File**: `/home/dd/lab/modern-software-dev-assignments/week5/fly.toml` (CREATE)
- Fly.io configuration
- Volume mount for SQLite persistence

**File**: `/home/dd/lab/modern-software-dev-assignments/week5/requirements.txt` (CREATE)
- Python dependencies for FastAPI deployment
- Used by both local development and Fly.io

### 4. CORS Configuration

**File**: `/home/dd/lab/modern-software-dev-assignments/week5/backend/app/main.py` (MODIFY)
- Update CORS settings to allow Vercel frontend origin
- Example: `allow_origins=["https://your-project.vercel.app"]`

### 5. Documentation

**File**: `/home/dd/lab/modern-software-dev-assignments/week5/README.md` (MODIFY)
- Add deployment guide section

---

## Vercel Configuration Details

### Project Structure for Vercel

The Vercel deployment will be configured with:
- **Project Root**: `/home/dd/lab/modern-software-dev-assignments/week5` (root of repo)
- **Framework Preset**: Vite
- **Build Command**: `npm run build` (runs in frontend directory via package.json scripts)
- **Output Directory**: `frontend/dist`

### vercel.json Structure

```json
{
  "buildCommand": "cd frontend && npm run build",
  "outputDirectory": "frontend/dist",
  "framework": "vite",
  "rewrites": [
    {
      "source": "/api/:path*",
      "destination": "https://backend-app.fly.io/:path*"
    }
  ],
  "env": {
    "VITE_API_BASE_URL": "@api-base-url"
  }
}
```

### Alternative: Frontend-Only vercel.json

If frontend is in a separate Vercel project:

```json
{
  "buildCommand": "cd frontend && npm run build",
  "outputDirectory": "frontend/dist",
  "framework": "vite",
  "env": {
    "VITE_API_BASE_URL": "@api-base-url"
  }
}
```

---

## Environment Variables

### Vercel (Frontend)

| Variable | Description | Example |
|----------|-------------|---------|
| `VITE_API_BASE_URL` | Backend API URL | `https://myapp.fly.io` |
| `VITE_API_BASE_URL` (in Vite) | Injected at build time | Set in Vercel dashboard |

### Fly.io (Backend)

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_PATH` | SQLite file path | `./data/app.db` |
| `PYTHON_ENV` | Environment | `production` |

---

## Build Configuration Changes

### Vite Configuration (frontend/vite.config.js)

```javascript
import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()],
  base: './',  // Required for static deployment
  build: {
    outDir: 'dist',  // Output to frontend/dist relative to package.json location
    emptyOutDir: true,
  },
  // Environment variable injection
  define: {
    'import.meta.env.VITE_API_BASE_URL': JSON.stringify(
      process.env.VITE_API_BASE_URL || 'http://localhost:8000'
    ),
  },
  server: {
    proxy: {
      '/notes': 'http://localhost:8000',
      '/action-items': 'http://localhost:8000',
      '/tags': 'http://localhost:8000',
    },
  },
});
```

### Package.json Scripts (frontend/package.json)

Ensure these scripts exist (already present):
```json
{
  "scripts": {
    "dev": "vite",
    "build": "vite build",
    "preview": "vite preview"
  }
}
```

---

## Deploy Guide Outline

### Prerequisites
- Vercel account
- Fly.io account
- Node.js 18+
- Python 3.11+

### Step 1: Deploy Backend to Fly.io

1. Install Fly CLI: `npm install -g flyctl`
2. Authenticate: `flyctl auth login`
3. Create app: `flyctl apps create my-backend-app`
4. Deploy: `flyctl deploy`
5. Note the URL (e.g., `https://my-backend-app.fly.dev`)

### Step 2: Configure CORS

Update `backend/app/main.py` to allow Vercel origin:
```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://your-frontend.vercel.app"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### Step 3: Deploy Frontend to Vercel

1. Connect repository to Vercel
2. Configure settings:
   - Framework: Vite
   - Build Command: `npm run build` (runs in frontend directory)
   - Output Directory: `frontend/dist`
3. Add environment variables:
   - `VITE_API_BASE_URL`: Your Fly.io backend URL
4. Deploy

### Step 4: Verify

1. Visit Vercel deployment URL
2. Test API calls work (create note, view action items, etc.)

### Rollback

- **Vercel**: Use dashboard to redeploy previous commit
- **Fly.io**: Use `flyctl releases` and `flyctl deploy --image-tag <tag>`

---

## Implementation Order

1. **Phase 1**: Create `requirements.txt` for backend dependencies
2. **Phase 2**: Update CORS in `backend/app/main.py`
3. **Phase 3**: Configure Vite (`vite.config.js`) for build output
4. **Phase 4**: Create `vercel.json` configuration
5. **Phase 5**: Create Fly.io config (`Dockerfile`, `fly.toml`)
6. **Phase 6**: Update `README.md` with deploy guide
7. **Phase 7**: Test deployment

---

## Dependencies Required

### Python (requirements.txt)

```
fastapi==0.109.0
uvicorn[standard]==0.27.0
sqlalchemy==2.0.25
pydantic==2.5.3
python-dotenv==1.0.0
```

### Node (frontend/package.json - already present)

- vite
- @vitejs/plugin-react
- react, react-dom
