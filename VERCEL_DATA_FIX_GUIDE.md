# Why Data Wasn't Showing on Vercel - Complete Guide

## The Problem

When you deployed the frontend to Vercel, the data wasn't showing because:

### 1. **Frontend was still pointing to localhost:8000**
```javascript
// ❌ WRONG - This only works locally
const API_BASE_URL = 'http://localhost:8000'
```

When Vercel frontend tried to call `http://localhost:8000`, it was calling:
- **From user's browser** → tries to reach their local machine (fails!)
- **From Vercel server** → tries to reach Vercel's internal localhost (doesn't exist!)

### 2. **Backend wasn't deployed or had a different URL**
Even if frontend knew the backend URL, if the backend wasn't running on Vercel/Railway, there was nothing to call.

### 3. **CORS might have been blocking requests**
- Frontend: `https://your-app.vercel.app`
- Backend: `http://localhost:8000` (or wrong URL)
- CORS rejected the cross-origin request

### 4. **API endpoints weren't properly configured**
The backend didn't know about the frontend's domain, so it rejected requests.

---

## The Solution

### Step 1: Deploy Backend to Railway ✅
**Your setup:**
- Backend runs on Railway: `https://trading-analytics-production.railway.app`
- Frontend runs on Vercel: `https://your-app.vercel.app`

### Step 2: Update Frontend Environment Variables

**For Local Development** (`.env.local`):
```env
VITE_API_BASE_URL=/api
```
This uses Vite's proxy to forward requests to localhost:8000

**For Production** (`.env.production`):
```env
VITE_API_BASE_URL=https://trading-analytics-production.railway.app
```
This points to your actual backend URL

### Step 3: Set Environment Variables in Vercel

In Vercel dashboard → Project Settings → Environment Variables:

```
Name: VITE_API_BASE_URL
Value: https://trading-analytics-production.railway.app
Environments: Production
```

### Step 4: Update Backend CORS Configuration

In `main.py`, add Vercel URLs to allowed origins:

```python
ALLOWED_ORIGINS = [
    "http://localhost:3000",        # Local dev
    "http://127.0.0.1:3000",        # Local dev
    "https://your-app.vercel.app",  # Vercel production
    "https://*.vercel.app",         # Vercel preview deployments
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_origin_regex=r"https://.*\.vercel\.app",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

The backend is already configured with this! ✅

### Step 5: Deploy in Order

**Never deploy frontend before backend!**

1. **First:** Deploy backend to Railway
   - Wait for it to be healthy
   - Get the URL: `https://trading-analytics-production.railway.app`
   
2. **Then:** Update `VITE_API_BASE_URL` in Vercel env vars
   
3. **Finally:** Deploy frontend to Vercel
   - Frontend will use the correct backend URL

---

## How to Fix It Now

### If data still isn't showing:

1. **Check backend is running:**
   ```bash
   curl https://trading-analytics-production.railway.app/health
   # Should return: {"status": "healthy", ...}
   ```

2. **Check frontend is using correct URL:**
   - Open browser DevTools → Console
   - Check network requests → should go to `trading-analytics-production.railway.app`
   - Not to `localhost:8000` or `127.0.0.1:8000`

3. **Check CORS is working:**
   - Network tab → look for `Access-Control-Allow-Origin` header
   - Should include your Vercel URL

4. **Check backend logs:**
   - Railway dashboard → Logs
   - Should see requests from Vercel URL

---

## Environment Variable Setup

### Vercel `.env` Files

**`.env.local`** (local development):
```env
VITE_API_BASE_URL=/api
```

**`.env.production`** (Vercel production):
```env
VITE_API_BASE_URL=https://trading-analytics-production.railway.app
```

### Vercel Dashboard Settings

Go to: **Settings → Environment Variables**

Add:
```
VITE_API_BASE_URL = https://trading-analytics-production.railway.app
```

---

## Testing Checklist

- [ ] Backend is running on Railway
- [ ] Backend health check works: `curl /health`
- [ ] Frontend env var points to backend URL
- [ ] Vercel has `VITE_API_BASE_URL` set
- [ ] CORS allows Vercel domain
- [ ] Deploy backend first, then frontend
- [ ] Check browser console for API errors
- [ ] Check Network tab to see actual requests
- [ ] Check Railway logs for incoming requests

---

## Quick Reference

| Environment | Frontend URL | Backend URL | Method |
|-------------|--------------|------------|---------|
| **Local Dev** | `http://localhost:3000` | `http://localhost:8000` | Vite proxy (/api) |
| **Railway Backend** | N/A | `https://trading-analytics-production.railway.app` | Deployed |
| **Vercel Frontend** | `https://your-app.vercel.app` | `https://trading-analytics-production.railway.app` | Direct API calls |
| **Vercel Preview** | `https://your-app-pr-*.vercel.app` | `https://trading-analytics-production.railway.app` | Direct API calls |

---

## Summary

**Why data wasn't showing:**
1. Frontend was pointing to localhost (doesn't work from Vercel)
2. Backend wasn't deployed (or on different URL)
3. CORS was rejecting requests
4. Environment variables weren't set

**How to fix it:**
1. Deploy backend to Railway
2. Set `VITE_API_BASE_URL` to backend URL
3. Update Vercel env vars
4. Ensure CORS allows Vercel domain
5. Redeploy frontend

**Result:** ✅ Data will show up!
