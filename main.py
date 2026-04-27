# main.py

import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from core.cache import get_cache_stats
from core.config import settings
from core.error_handlers import register_error_handlers
from core.logging_config import setup_logging
from core.middleware import RequestLoggingMiddleware
from core.scheduler import get_scheduler_status, start_scheduler, stop_scheduler
from routers.Database.engine import check_connection
from services.websocket_manager import (
    is_connected,
    start_websocket_feed,
    stop_websocket_feed,
)

# ── Logging setup — must be first ─────────────────────────────────────────────
setup_logging(debug=settings.debug)
logger = logging.getLogger(__name__)

# ── Router imports — wrapped safely so one bad router doesn't kill the app ────
try:
    from routers import (
        auth_upstox,
        backtest,
        cache,
        fii_dii,
        fvg,
        indicators,
        live,
        market,
        news,
        predict,
        risk,
    )
    ROUTERS_LOADED = True
    logger.info("All routers imported successfully")
except Exception as e:
    logger.error(f"Router import failed: {e}")
    ROUTERS_LOADED = False

# ── Optional SMC full router (may not exist yet) ───────────────────────────────
try:
    from routers import smc_full
    SMC_FULL_LOADED = True
except Exception:
    SMC_FULL_LOADED = False


# ── Lifespan — startup and shutdown ───────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info(f"Starting {settings.app_name} v0.22.0")

    # Database — optional, skip gracefully if not configured
    try:
        db_url = settings.database_url or os.environ.get("DATABASE_URL", "")
        if db_url:
            if check_connection():
                logger.info("Database connected successfully")
            else:
                logger.warning("Database connection failed — running without DB")
        else:
            logger.warning("No DATABASE_URL configured — running without DB")
    except Exception as e:
        logger.warning(f"Database check skipped: {e}")

    # Scheduler — skip if it fails
    try:
        start_scheduler()
        logger.info("Scheduler started")
    except Exception as e:
        logger.warning(f"Scheduler failed to start: {e}")

    # Upstox WebSocket — only if token is configured
    if settings.upstox_access_token:
        try:
            await start_websocket_feed()
            logger.info("Upstox WebSocket feed started")
        except Exception as e:
            logger.warning(f"WebSocket feed failed to start: {e}")
    else:
        logger.info("No Upstox token — WebSocket feed skipped")

    yield

    # ── Shutdown ───────────────────────────────────────────────────────────────
    try:
        await stop_websocket_feed()
    except Exception:
        pass

    try:
        stop_scheduler()
    except Exception:
        pass

    logger.info("Shutdown complete")


# ── FastAPI app ────────────────────────────────────────────────────────────────

app = FastAPI(
    title=settings.app_name,
    description="AI-powered trading analytics for Indian markets (Nifty 50 & Sensex)",
    version="0.22.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# ── Error handlers — register before middleware and routers ───────────────────
register_error_handlers(app)

# ── CORS — allow Vercel frontend and local dev ────────────────────────────────
ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]

# Add Vercel production URL if configured
vercel_url = os.environ.get("VERCEL_URL", "")
if vercel_url:
    ALLOWED_ORIGINS.append(f"https://{vercel_url}")

# Add any manually configured frontend URL
frontend_url = os.environ.get("FRONTEND_URL", "")
if frontend_url:
    ALLOWED_ORIGINS.append(frontend_url)

# In development/staging allow all Vercel preview URLs
ALLOWED_ORIGINS.append("https://*.vercel.app")

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_origin_regex=r"https://.*\.vercel\.app",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(RequestLoggingMiddleware)

# ── Routers ───────────────────────────────────────────────────────────────────
if ROUTERS_LOADED:
    app.include_router(market.router)       # GET /market/
    app.include_router(indicators.router)   # GET /indicators/
    app.include_router(fvg.router)          # GET /fvg/
    app.include_router(predict.router)      # GET /predict/
    app.include_router(risk.router)         # GET /risk/
    app.include_router(backtest.router)     # GET /backtest/
    app.include_router(news.router)         # GET /news/
    app.include_router(fii_dii.router)      # GET /fii-dii/
    app.include_router(live.router)         # GET /live/ + WS /live/ws/feed
    app.include_router(auth_upstox.router)  # GET /auth/upstox/
    app.include_router(cache.router)        # GET /cache/stats  DELETE /cache/clear
    logger.info("All routers registered")
else:
    logger.error("Routers failed to load — API endpoints unavailable")

if SMC_FULL_LOADED:
    app.include_router(smc_full.router)     # GET /smc-full/
    logger.info("SMC full router registered")


# ── Core endpoints ────────────────────────────────────────────────────────────

@app.get("/", tags=["Health"])
def root():
    return {
        "app":      settings.app_name,
        "status":   "running",
        "version":  "0.22.0",
        "provider": settings.data_provider,
        "docs":     "/docs",
        "routers":  ROUTERS_LOADED,
    }


@app.get("/health", tags=["Health"])
def health():
    """
    Health check endpoint — used by Railway healthcheck.
    Always returns 200 even if optional services are down.
    """
    db_ok  = False
    ws_ok  = False
    sched  = {"running": False, "jobs": []}

    try:
        db_ok = check_connection()
    except Exception:
        pass

    try:
        ws_ok = is_connected()
    except Exception:
        pass

    try:
        sched = get_scheduler_status()
    except Exception:
        pass

    cache = {}
    try:
        cache = get_cache_stats()
    except Exception:
        pass

    return {
        "status":        "healthy",
        "version":       "0.22.0",
        "data_provider": settings.data_provider,
        "database":      db_ok,
        "ws_connected":  ws_ok,
        "scheduler":     sched,
        "cache":         cache,
    }