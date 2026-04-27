# Railway Deployment Guide

## Quick Start

Your Trade Analytics Platform is ready to deploy on Railway! Follow these steps:

### Step 1: Create a Railway Account
1. Go to https://railway.app
2. Sign up with GitHub
3. Create a new project

### Step 2: Connect Your GitHub Repository
1. Click **"New Project"** in Railway dashboard
2. Select **"Deploy from GitHub"**
3. Find and select your repo: `trading-analytics-platform`
4. Railway will auto-detect the `railway.json` and `Dockerfile`

### Step 3: Add PostgreSQL Database
1. In your Railway project, click **"+ Add"**
2. Select **"Database"** → **"PostgreSQL"**
3. Railway automatically sets `DATABASE_URL` env var

### Step 4: Set Environment Variables
In Railway project settings, add these env vars:

```env
# Required
DATABASE_URL=<auto-set by Railway>
DEBUG=False
SECRET_KEY=your-secret-key-here

# Optional (but recommended)
DATA_PROVIDER=yfinance
UPSTOX_API_KEY=your-key
UPSTOX_API_SECRET=your-secret
UPSTOX_REDIRECT_URI=https://your-railway-url/auth/upstox/callback

# For frontend CORS
RAILWAY_PUBLIC_URL=https://your-railway-url.railway.app
```

### Step 5: Deploy
1. Click **"Deploy"**
2. Railway will:
   - Build Docker image
   - Start the app
   - Run health checks
   - Auto-retry on failures

### Step 6: Get Your Backend URL
Once deployed, Railway gives you a URL like:
```
https://trading-analytics-production.railway.app
```

Save this for the frontend configuration.

---

## What's Optimized for Railway

### ✅ Database Handling
- **Auto-detects PostgreSQL URL format** (converts `postgres://` to `postgresql://`)
- **Graceful fallback** if database isn't ready yet
- **Connection pooling** for performance

### ✅ Error Resilience
- **Routers load safely** — if one fails, app still runs
- **Services degrade gracefully** — Scheduler/WebSocket optional
- **No migration crashes** — migrations optional on startup
- **Health check always available** — `/health` endpoint works even if features fail

### ✅ Production Ready
- **CORS configured for Railway URLs**
- **PORT auto-detected from `$PORT` env var**
- **Health checks enabled** (30s interval, 10s timeout, 40s startup wait)
- **Auto-restart on failures** (up to 3 retries)
- **Optimized startup** (fast, no blocking operations)

### ✅ Configuration Files
- `railway.json` — Railway deployment settings
- `Dockerfile` — Production Docker image (Python 3.12-slim)
- `routers/Database/engine.py` — PostgreSQL URL conversion
- `main.py` — Safe router imports + graceful degradation

---

## Testing Before Deploying

Run locally to verify:

```bash
# Backend only
export DATABASE_URL="sqlite:///trading.db"
uvicorn main:app --host 0.0.0.0 --port 8000

# Check health
curl http://localhost:8000/health

# View API docs
open http://localhost:8000/docs
```

---

## Common Issues & Fixes

### Issue: App crashes on startup
**Fix:** Check Railway logs for errors. Most likely:
- Missing PostgreSQL plugin → Add it in Railway
- Wrong `SECRET_KEY` → Check env vars
- Missing dependencies → Check `requirements.txt`

### Issue: Database connection fails
**Fix:** Railway's PostgreSQL URL format is handled automatically. Just make sure:
- PostgreSQL plugin is added to your Railway project
- `DATABASE_URL` is set in env vars
- App has permission to access the database

### Issue: 502 Bad Gateway
**Fix:** Usually means the app isn't healthy. Check:
- Health check at `/health` is responding
- App startup logs for errors
- Railway memory limits (increase if needed)

### Issue: CORS errors from frontend
**Fix:** If frontend is on different Railway URL:
1. Get your Railway backend URL
2. Update `RAILWAY_PUBLIC_URL` env var
3. Frontend should auto-add it to allowed origins

---

## Monitoring & Logs

In Railway dashboard:
1. Click your service
2. Go to **"Logs"** tab
3. Watch real-time logs
4. Check for errors/warnings

Example healthy startup:
```
Starting Trading Analytics Platform
Database connected
Scheduler started
WebSocket started
Shutdown complete
```

---

## Frontend Deployment

After backend is running, deploy the frontend:

### Option 1: Vercel (Recommended)
1. Frontend is in `frontend/` directory
2. Create `frontend/vercel.json`:
   ```json
   {
     "buildCommand": "npm run build",
     "outputDirectory": "dist"
   }
   ```
3. Deploy on Vercel (auto-detects React app)
4. Set env var: `VITE_API_URL=https://your-railway-backend.railway.app`

### Option 2: Railway
Deploy frontend on same Railway project:
1. Add another service
2. Set buildCommand: `npm run build`
3. Set startCommand: `npm run preview`
4. Set `VITE_API_URL` env var

---

## Next Steps

1. **Commit changes** to GitHub
2. **Push to Railway** (auto-deploys via GitHub integration)
3. **Monitor logs** in Railway dashboard
4. **Test API endpoints** when deployment completes
5. **Deploy frontend** with backend URL

---

## File Reference

- `railway.json` - Railway deployment configuration
- `Dockerfile` - Backend Docker image
- `main.py` - FastAPI app with safe imports
- `routers/Database/engine.py` - PostgreSQL handler
- `requirements.txt` - Python dependencies
- `.env.example` - Environment variable template

---

## Questions?

Check logs in Railway dashboard or run locally first to debug.
Good luck! 🚀
