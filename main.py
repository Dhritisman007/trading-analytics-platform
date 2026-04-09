# main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from core.config import settings
from routers import market, indicators, fvg

app = FastAPI(
    title=settings.app_name,
    description="AI-powered trading analytics for Indian markets (Nifty 50 & Sensex)",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS — allows your React frontend to call this API later
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # React dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(market.router)
app.include_router(indicators.router)
app.include_router(fvg.router)

@app.get("/", tags=["Health"])
def root():
    return {
        "app": settings.app_name,
        "status": "running",
        "docs": "/docs",
        "version": "0.1.0",
    }

@app.get("/health", tags=["Health"])
def health_check():
    return {"status": "healthy"}
# main.py

import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from core.config import settings
from core.scheduler import create_scheduler, run_initial_warmup
from routers import market, indicators, fvg, cache as cache_router

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

# APScheduler instance — created once, lives for the app's lifetime
scheduler = create_scheduler()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager — runs startup logic before yield,
    shutdown logic after. This is FastAPI's modern replacement
    for @app.on_event("startup") / ("shutdown").
    """
    # ── Startup ───────────────────────────────────────────────────────────
    logger.info(f"Starting {settings.app_name}")

    # Warm the cache immediately so first requests don't hit yfinance
    run_initial_warmup()

    # Start the background scheduler
    scheduler.start()
    logger.info("Scheduler started — market data will refresh every 5 minutes")

    yield  # App runs here — everything between yield and the end is shutdown

    # ── Shutdown ──────────────────────────────────────────────────────────
    scheduler.shutdown(wait=False)
    logger.info("Scheduler stopped")


app = FastAPI(
    title=settings.app_name,
    description="AI-powered trading analytics for Indian markets",
    version="0.3.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(market.router)
app.include_router(indicators.router)
app.include_router(fvg.router)
app.include_router(cache_router.router)


@app.get("/", tags=["Health"])
def root():
    return {"app": settings.app_name, "status": "running", "docs": "/docs"}


@app.get("/health", tags=["Health"])
def health():
    return {"status": "healthy"}