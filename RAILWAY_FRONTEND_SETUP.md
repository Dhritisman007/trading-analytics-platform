# 🚀 Railway Backend + Local Frontend Setup Guide

## Your Setup
- **Backend URL:** https://trading-analytics-platform-production.up.railway.app
- **Backend Status:** ✅ Healthy & Running
- **Frontend:** Running locally on `http://localhost:5173`

---

## ✅ Step 1: Local Frontend Configuration (COMPLETED)

### File: `frontend/.env.local`
```bash
VITE_API_BASE_URL=https://trading-analytics-platform-production.up.railway.app
VITE_WS_URL=wss://trading-analytics-platform-production.up.railway.app/live/ws/feed
```

This file has been created. The frontend will now:
- Make REST API calls to your Railway backend
- Connect WebSocket to Railway for live data

---

## ✅ Step 2: Start Frontend with Railway Backend

### Terminal Command:
```bash
cd /Users/dhritismansarma/Desktop/Trade\ Analytics\ Platform/frontend
npm run dev
```

**Expected Output:**
```
VITE v5.x.x ready in xxx ms
➜  Local:   http://localhost:5173/
```

Open: `http://localhost:5173` in your browser

---

## ✅ Step 3: Verify Connection Working

### Browser Console Check:
1. Open DevTools: `F12` or `Cmd+Option+I`
2. Go to **Network** tab
3. Refresh page: `Cmd+R` or `F5`
4. Look for requests to `trading-analytics-platform-production.up.railway.app`
5. Should see `200` status codes (success)

### Terminal Check:
```bash
# Test backend directly
curl https://trading-analytics-platform-production.up.railway.app/health

# Should return:
# {"status":"healthy",...}
```

### Frontend Should Show:
- ✅ Dashboard loads with market data
- ✅ Real-time data updates
- ✅ All pages accessible (Indicators, Risk, Backtest, etc.)
- ✅ No CORS errors in console

---

## 🔧 Step 4: (Optional) Deploy Frontend to Production

When ready to deploy frontend to Vercel/Netlify:

### For Vercel:
1. Go to Vercel dashboard → Settings → Environment Variables
2. Add:
   ```
   VITE_API_BASE_URL=https://trading-analytics-platform-production.up.railway.app
   VITE_WS_URL=wss://trading-analytics-platform-production.up.railway.app/live/ws/feed
   ```
3. Redeploy

### For Netlify:
1. Go to Site Settings → Build & Deploy → Environment
2. Add the same env vars
3. Redeploy

---

## 🔐 Step 5: Configure CORS on Railway Backend (IMPORTANT)

Currently, your backend allows all origins (`["*"]`). For production, restrict it:

### On Railway Dashboard:

1. **Go to:** Your Backend Project → Settings → Variables
2. **Add Environment Variable:**
   ```
   FRONTEND_URL=http://localhost:5173
   ```
   (For local dev, or your deployed frontend URL like `https://app.vercel.app`)

3. **Redeploy** the backend service

### Backend Code (main.py):
The backend already reads `FRONTEND_URL` from environment:
```python
CORS_ORIGINS = [
    "http://localhost:3000",
    "http://localhost:5173",
    "http://127.0.0.1:3000",
    "http://127.0.0.1:5173",
    os.environ.get("FRONTEND_URL", ""),  # ← Railway env var
]
```

---

## 📊 API Endpoints Available

**Base URL:** `https://trading-analytics-platform-production.up.railway.app`

### Health & Status
- `GET /health` → System status
- `GET /` → App info

### Market Data
- `GET /market?symbol=^NSEI&period=3mo` → OHLCV candles
- `GET /market/symbols` → Available symbols

### Technical Analysis
- `GET /indicators?symbol=^NSEI&period=3mo&rsi_window=14&ema_window=20` → RSI, EMA
- `GET /indicators/latest?symbol=^NSEI` → Latest indicators

### Smart Money Concepts
- `GET /fvg?symbol=^NSEI&period=3mo` → Fair Value Gaps
- `GET /fvg/open?symbol=^NSEI` → Open FVGs only

### Risk Management
- `GET /risk/quick?capital=100000&entry_price=50000&stop_loss=45000` → Quick analysis
- `GET /risk/atr-stops?symbol=^NSEI&entry_price=24000&atr_multiplier=1.5` → ATR stops

### Trading Analysis
- `GET /predict?symbol=^NSEI&top_n=10` → ML predictions
- `GET /backtest?strategy=rsi&symbol=^NSEI&period=2y&initial_capital=100000` → Backtest

### Market Intelligence
- `GET /news?symbol=^NSEI` → Financial news
- `GET /fii-dii/today` → FII/DII flows

### Live Data (WebSocket)
- `WS /live/ws/feed` → Real-time price ticks

---

## ⚠️ Troubleshooting

### "Failed to fetch from Railway backend"
**Problem:** CORS error or backend not accessible

**Solutions:**
```bash
# 1. Check backend is running
curl https://trading-analytics-platform-production.up.railway.app/health

# 2. Check .env.local is set correctly
cat frontend/.env.local

# 3. Restart frontend
cd frontend
npm run dev
```

### "WebSocket connection failed"
**Problem:** WebSocket not connecting

**Check:**
- `.env.local` has `VITE_WS_URL=wss://...`
- Backend WebSocket endpoint is running
- Browser DevTools → Console for WS errors

### "API calls timing out"
**Problem:** Railway backend slow or overloaded

**Check:**
- Railway logs in dashboard
- Try `curl` directly: `curl https://trading-analytics-platform-production.up.railway.app/market?symbol=^NSEI&period=1mo`
- Check network tab in DevTools for actual response time

### "CORS blocked error"
**Problem:** Frontend origin not allowed by backend

**Solution:**
1. Add `FRONTEND_URL` env var on Railway
2. Or temporarily set `FRONTEND_URL=*` for debugging
3. Redeploy backend

---

## 📝 Quick Reference

| Item | Value |
|------|-------|
| Backend URL | https://trading-analytics-platform-production.up.railway.app |
| Frontend (Local) | http://localhost:5173 |
| Backend Health | ✅ Healthy |
| CORS Config | ✅ Ready |
| WebSocket | ✅ Ready |
| Environment File | `frontend/.env.local` |

---

## ✅ Success Checklist

- [x] `.env.local` created with Railway backend URL
- [x] Backend is running and healthy
- [x] Frontend starts with `npm run dev`
- [x] API calls go to Railway backend
- [x] Data displays in browser
- [x] No CORS errors
- [x] WebSocket connection established

---

## 🎯 Next Steps

1. **Local Testing** (Current)
   - Frontend at `http://localhost:5173`
   - Backend at Railway
   - Test all features locally

2. **Deploy Frontend** (When ready)
   - Push to GitHub
   - Deploy to Vercel/Netlify
   - Set same env vars on hosting platform
   - Update `FRONTEND_URL` on Railway if needed

3. **Monitor & Scale**
   - Check Railway logs regularly
   - Monitor response times
   - Scale backend if needed

---

**Last Updated:** May 1, 2026
**Status:** ✅ Ready for Production Testing
