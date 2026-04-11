# main.py

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from core.cache import get_cache_stats
from core.config import settings
from core.error_handlers import register_error_handlers
from core.logging_config import setup_logging
from core.middleware import RequestLoggingMiddleware
from core.scheduler import get_scheduler_status
from core.scheduler import start_scheduler
from core.scheduler import stop_scheduler
from routers import auth_upstox
from routers import cache
from routers import fvg
from routers import indicators
from routers import live
from routers import market
from routers import predict
from services.websocket_manager import start_websocket_feed
from services.websocket_manager import stop_websocket_feed

setup_logging(debug=settings.debug)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info(f"Starting {settings.app_name}")
    start_scheduler()

    # Only start WebSocket feed if Upstox token is configured
    if settings.upstox_access_token:
        await start_websocket_feed()
        logger.info("Upstox WebSocket feed started")
    else:
        logger.info(
            "No Upstox token — WebSocket feed skipped (set UPSTOX_ACCESS_TOKEN)"
        )

    yield

    await stop_websocket_feed()
    stop_scheduler()
    logger.info("Shutdown complete")


app = FastAPI(
    title=settings.app_name,
    description="AI-powered trading analytics for Indian markets",
    version="0.7.0",
    lifespan=lifespan,
)

register_error_handlers(app)

app.add_middleware(RequestLoggingMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(market.router)
app.include_router(indicators.router)
app.include_router(fvg.router)
app.include_router(auth_upstox.router)
app.include_router(live.router)
app.include_router(cache.router)
app.include_router(predict.router)


@app.get("/", tags=["Health"])
def root():
    return {
        "app": settings.app_name,
        "status": "running",
        "version": "0.7.0",
        "provider": settings.data_provider,
        "docs": "/docs",
    }


@app.get("/health", tags=["Health"])
def health():
    from services.websocket_manager import is_connected

    return {
        "status": "healthy",
        "data_provider": settings.data_provider,
        "ws_connected": is_connected(),
        "cache": get_cache_stats(),
        "scheduler": get_scheduler_status(),
    }