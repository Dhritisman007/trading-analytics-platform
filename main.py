# main.py
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from core.config import settings
from core.logging_config import setup_logging
from core.error_handlers import register_error_handlers
from core.middleware import RequestLoggingMiddleware
from core.scheduler import start_scheduler, stop_scheduler, get_scheduler_status
from core.cache import get_cache_stats
from routers import market, indicators, fvg, cache

# Set up logging first — before anything else
setup_logging(debug=settings.debug)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info(f"Starting {settings.app_name} v0.6.0")
    start_scheduler()
    yield
    stop_scheduler()
    logger.info("App shut down cleanly")


app = FastAPI(
    title=settings.app_name,
    description="AI-powered trading analytics for Indian markets",
    version="0.6.0",
    lifespan=lifespan,
)

# Order matters: register middleware and error handlers before routers
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
app.include_router(cache.router)


@app.get("/", tags=["Health"])
def root():
    return {
        "app":     settings.app_name,
        "status":  "running",
        "version": "0.6.0",
        "docs":    "/docs",
    }


@app.get("/health", tags=["Health"])
def health():
    return {
        "status":    "healthy",
        "cache":     get_cache_stats(),
        "scheduler": get_scheduler_status(),
    }