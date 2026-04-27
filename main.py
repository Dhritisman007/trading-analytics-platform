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
from core.database import init_db
from routers import auth_upstox, backtest, cache, fii_dii, fvg, indicators, live, market, news, predict, risk
from services.websocket_manager import is_connected, start_websocket_feed, stop_websocket_feed

setup_logging(debug=settings.debug)
logger = logging.getLogger(__name__)

# Check if running in test mode
TESTING = os.environ.get("TESTING") == "1"


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info(f"Starting {settings.app_name} v0.16.0")

    # Initialize database tables on startup
    try:
        init_db()
        logger.info("Database tables initialized successfully")
    except Exception as e:
        logger.warning(f"Database initialization warning: {e}")

    # Skip scheduler and WebSocket in test mode
    if not TESTING:
        start_scheduler()

        if settings.upstox_access_token:
            await start_websocket_feed()
            logger.info("Upstox WebSocket feed started")
        else:
            logger.info("No Upstox token — WebSocket feed skipped")
    else:
        logger.info("Running in TEST mode — scheduler and WebSocket skipped")

    yield

    if not TESTING:
        await stop_websocket_feed()
        stop_scheduler()
    logger.info("Shutdown complete")


app = FastAPI(
    title=settings.app_name,
    description="AI-powered trading analytics for Indian markets",
    version="0.16.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

register_error_handlers(app)

app.add_middleware(RequestLoggingMiddleware)
# Allow all origins in production (Railway, Vercel, etc.)
# Restrict this to specific domains once your frontend URL is known
CORS_ORIGINS = [
    "http://localhost:3000",
    "http://localhost:5173",
    "http://127.0.0.1:3000",
    "http://127.0.0.1:5173",
    os.environ.get("FRONTEND_URL", ""),
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=[o for o in CORS_ORIGINS if o] or ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(market.router)
app.include_router(indicators.router)
app.include_router(fvg.router)
app.include_router(predict.router)
app.include_router(risk.router)
app.include_router(backtest.router)
app.include_router(news.router)
app.include_router(fii_dii.router)
app.include_router(live.router)
app.include_router(auth_upstox.router)
app.include_router(cache.router)


@app.get("/ping", tags=["Health"])
def ping():
    """Lightweight health check for Railway — never fails."""
    return {"status": "ok"}


@app.get("/", tags=["Health"])
def root():
    return {
        "app":      settings.app_name,
        "status":   "running",
        "version":  "0.16.0",
        "provider": settings.data_provider,
        "docs":     "/docs",
    }


@app.get("/health", tags=["Health"])
def health():
    return {
        "status":        "healthy",
        "data_provider": settings.data_provider,
        "ws_connected":  is_connected(),
        "cache":         get_cache_stats(),
        "scheduler":     get_scheduler_status(),
    }