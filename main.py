# main.py

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from core.cache import get_cache_stats
from core.config import settings
from core.database import init_db
from core.error_handlers import register_error_handlers
from core.logging_config import setup_logging
from core.middleware import RequestLoggingMiddleware
from core.scheduler import get_scheduler_status, start_scheduler, stop_scheduler
from routers import auth_upstox, backtest, cache, fii_dii, fvg, indicators, live, market, news, predict, risk
from services.websocket_manager import is_connected, start_websocket_feed, stop_websocket_feed

# Set up logging first — before anything else
setup_logging(debug=settings.debug)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # ── Startup ───────────────────────────────────────────────────────────
    logger.info(f"Starting {settings.app_name} v0.12.0")
    
    # Initialize database tables on startup
    try:
        init_db()
        logger.info("Database tables initialized successfully")
    except Exception as e:
        logger.warning(f"Database initialization warning: {e}")
    
    start_scheduler()

    if settings.upstox_access_token:
        await start_websocket_feed()
        logger.info("Upstox WebSocket feed started")
    else:
        logger.info("No Upstox token — WebSocket feed skipped (set UPSTOX_ACCESS_TOKEN)")

    yield

    # ── Shutdown ──────────────────────────────────────────────────────────
    await stop_websocket_feed()
    stop_scheduler()
    logger.info("Shutdown complete")


app = FastAPI(
    title=settings.app_name,
    description="AI-powered trading analytics for Indian markets (Nifty 50 & Sensex)",
    version="0.12.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# ── Middleware + error handlers ───────────────────────────────────────────────
# Order matters — register these before routers
register_error_handlers(app)

app.add_middleware(RequestLoggingMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routers ───────────────────────────────────────────────────────────────────
app.include_router(market.router)       # /market/
app.include_router(indicators.router)   # /indicators/
app.include_router(fvg.router)          # /fvg/
app.include_router(predict.router)      # /predict/
app.include_router(risk.router)         # /risk/
app.include_router(backtest.router)     # /backtest/
app.include_router(cache.router)        # /cache/
app.include_router(news.router)         # /news/
app.include_router(fii_dii.router)      # /fii-dii/
app.include_router(live.router)         # /live/
app.include_router(auth_upstox.router)  # /auth/upstox/


# ── Core endpoints ────────────────────────────────────────────────────────────

@app.get("/", tags=["Health"])
def root():
    return {
        "app":      settings.app_name,
        "status":   "running",
        "version":  "0.12.0",
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