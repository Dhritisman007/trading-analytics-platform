# Deploy to Vercel — Step-by-Step Guide

## Option 1: Deploy Frontend to Vercel (Recommended)

Your Vercel is already logged in with GitHub. Follow these steps:

### Step 1: Push to GitHub

```bash
cd /Users/dhritismansarma/Desktop/Trade\ Analytics\ Platform

# Initialize git (if not done)
git init
git add .
git commit -m "Trade Analytics Platform v0.16.0"

# Add remote (replace with your GitHub repo)
git remote add origin https://github.com/YOUR_USERNAME/trade-analytics-platform.git

# Push to GitHub
git push -u origin main
```

### Step 2: Deploy to Vercel

**Option A: Using Vercel Dashboard**
1. Go to https://vercel.com/dashboard
2. Click "New Project"
3. Select your GitHub repo `trade-analytics-platform`
4. Configure:
   - Framework: **Vite**
   - Root Directory: `./frontend`
   - Build Command: `npm run build`
   - Output Directory: `dist`
5. Click "Deploy"

**Option B: Using Vercel CLI**
```bash
npm install -g vercel
cd /Users/dhritismansarma/Desktop/Trade\ Analytics\ Platform/frontend
vercel --prod
```

### Step 3: Set Environment Variables

Add to Vercel project settings:
```
VITE_API_URL=https://your-backend-domain.com
```

---

## Option 2: Deploy Backend to Heroku or AWS

### Backend Deployment Requirement
The backend needs a server to run on. Vercel doesn't support long-running processes like FastAPI.

**Choose one:**

#### Option A: Deploy Backend to Heroku (Free tier available)
```bash
# Install Heroku CLI
brew tap heroku/brew && brew install heroku

# Login
heroku login

# Create app
heroku create trade-analytics-api

# Deploy
git push heroku main

# View logs
heroku logs -t -a trade-analytics-api
```

#### Option B: Deploy Backend to AWS (EC2, Lambda, or ECS)
See DEPLOYMENT.md for detailed instructions.

#### Option C: Deploy Backend to Railway.app
```bash
# Simple Docker deployment
# Visit https://railway.app
# Connect GitHub repo
# Select Dockerfile
# Deploy
```

---

## Full Architecture After Deployment

```
Frontend (Vercel)
  ↓
  API calls to backend
  ↓
Backend (Heroku/AWS/Railway)
  ↓
PostgreSQL (AWS RDS or Railway)
Redis (AWS ElastiCache or Railway)
```

---

## Current Status

✅ **Frontend ready to deploy** (Vite React app)
✅ **Backend ready to deploy** (FastAPI + Docker)
✅ **All tests passing** (326/326)
✅ **GitHub connected to Vercel** (just need to push)

---

## Quick Vercel Deploy (Frontend Only)

```bash
# 1. Ensure you're in frontend directory
cd /Users/dhritismansarma/Desktop/Trade\ Analytics\ Platform/frontend

# 2. Build production version
npm run build

# 3. Verify dist folder exists
ls -la dist/

# 4. Install Vercel CLI (if needed)
npm install -g vercel

# 5. Deploy
vercel --prod
```

**Result**: Frontend deployed to `https://your-project.vercel.app`

---

## Connecting Frontend to Backend

After deploying backend, update frontend API URL:

### Method 1: Environment Variable
```bash
# In Vercel dashboard → Settings → Environment Variables
VITE_API_URL=https://your-backend-api.com
```

### Method 2: Update vite.config.js
```javascript
proxy: {
  '/api': {
    target: 'https://your-backend-api.com',
    changeOrigin: true,
  }
}
```

---

## Next Steps

1. ✅ **Push frontend to GitHub** (already logged in with Vercel)
2. ✅ **Deploy frontend to Vercel** (auto-deploy on push)
3. ⚠️ **Deploy backend separately** (Heroku/AWS/Railway)
4. ✅ **Connect frontend to backend API**
5. ✅ **Test all features end-to-end**

---

## Recommended Setup

**For MVP** (Quick & Easy):
- Frontend: Vercel ✅
- Backend: Railway.app or Heroku
- Database: Railway or AWS RDS

**For Production** (Scalable):
- Frontend: Vercel
- Backend: AWS EC2 or ECS
- Database: AWS RDS
- Cache: AWS ElastiCache

---

## Commands to Get Started

```bash
# 1. Go to project
cd /Users/dhritismansarma/Desktop/Trade\ Analytics\ Platform

# 2. Initialize git
git init
git add .
git commit -m "Initial commit"

# 3. Add GitHub remote
git remote add origin https://github.com/YOUR_USERNAME/trade-analytics-platform.git

# 4. Push to GitHub
git branch -M main
git push -u origin main

# 5. Open Vercel dashboard and connect the repo
# https://vercel.com/new

# Done! Vercel auto-deploys on every push to main
```

---

**Status**: Ready for Vercel deployment
**Frontend**: Ready ✅
**Backend**: Ready (needs separate deployment)
**Time to Deploy**: 5 minutes (frontend) + 10 minutes (backend)
