# core/scheduler.py

import logging
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger

logger = logging.getLogger(__name__)

# Symbols to keep warm in cache — add more here as your platform grows
WATCHED_SYMBOLS = [
    {"symbol": "^NSEI",   "name": "Nifty 50"},
    {"symbol": "^BSESN",  "name": "Sensex"},
    {"symbol": "^NSEBANK","name": "Bank Nifty"},
]

# How long cached data stays valid (seconds)
MARKET_DATA_TTL   = 300   # 5 minutes
INDICATOR_TTL     = 300   # 5 minutes
FVG_TTL           = 600   # 10 minutes — FVGs change less frequently


def refresh_market_data():
    """
    Fetch fresh market data for all watched symbols and store in cache.
    Called by the scheduler every 5 minutes.
    APScheduler runs this in a background thread — never blocks the API.
    """
    # Import here to avoid circular imports at module load time
    from services.market_service import fetch_market_data
    from core.cache import cache

    for item in WATCHED_SYMBOLS:
        symbol = item["symbol"]
        try:
            data = fetch_market_data(symbol=symbol, period="3mo", interval="1d")
            cache.set(f"market:{symbol}:3mo:1d", data, ttl_seconds=MARKET_DATA_TTL)
            logger.info(f"Refreshed market data: {symbol}")
        except Exception as e:
            # Never let one failure crash the whole refresh job
            logger.error(f"Failed to refresh market data for {symbol}: {e}")


def refresh_indicators():
    """Refresh indicator data for all watched symbols."""
    from services.indicator_calculator import get_indicators
    from core.cache import cache

    for item in WATCHED_SYMBOLS:
        symbol = item["symbol"]
        try:
            data = get_indicators(symbol=symbol, period="3mo", interval="1d")
            cache.set(f"indicators:{symbol}:3mo:1d:14:20:14", data, ttl_seconds=INDICATOR_TTL)
            logger.info(f"Refreshed indicators: {symbol}")
        except Exception as e:
            logger.error(f"Failed to refresh indicators for {symbol}: {e}")


def refresh_fvgs():
    """Refresh FVG data — runs less frequently since FVGs are slower to change."""
    from services.fvg_service import detect_fvgs
    from core.cache import cache

    for item in WATCHED_SYMBOLS:
        symbol = item["symbol"]
        try:
            data = detect_fvgs(symbol=symbol, period="3mo", interval="1d")
            cache.set(f"fvg:{symbol}:3mo:1d", data, ttl_seconds=FVG_TTL)
            logger.info(f"Refreshed FVGs: {symbol}")
        except Exception as e:
            logger.error(f"Failed to refresh FVGs for {symbol}: {e}")


def run_initial_warmup():
    """
    On startup, immediately populate the cache for all symbols.
    This means the first real user request hits cache, not yfinance.
    Runs once when the server starts.
    """
    logger.info("Starting cache warmup...")
    refresh_market_data()
    refresh_indicators()
    refresh_fvgs()
    logger.info("Cache warmup complete")


def create_scheduler() -> BackgroundScheduler:
    """
    Build and return a configured scheduler.
    Called once from main.py on startup.
    """
    scheduler = BackgroundScheduler(
        job_defaults={
            "coalesce":        True,   # if a job is missed, run it once not multiple times
            "max_instances":   1,      # never run the same job twice simultaneously
            "misfire_grace_time": 60,  # if delayed by up to 60s, still run it
        }
    )

    # Market data: every 5 minutes
    scheduler.add_job(
        refresh_market_data,
        trigger=IntervalTrigger(minutes=5),
        id="refresh_market",
        name="Refresh market data",
    )

    # Indicators: every 5 minutes, offset by 30 seconds
    # (so it runs after market data is already fresh)
    scheduler.add_job(
        refresh_indicators,
        trigger=IntervalTrigger(minutes=5, seconds=30),
        id="refresh_indicators",
        name="Refresh indicators",
    )

    # FVGs: every 10 minutes
    scheduler.add_job(
        refresh_fvgs,
        trigger=IntervalTrigger(minutes=10),
        id="refresh_fvgs",
        name="Refresh FVGs",
    )

    return scheduler


# Global scheduler instance
_scheduler: BackgroundScheduler | None = None


def start_scheduler():
    """Start the background scheduler on app startup."""
    global _scheduler
    _scheduler = create_scheduler()
    run_initial_warmup()
    _scheduler.start()
    logger.info("Scheduler started successfully")


def stop_scheduler():
    """Stop the background scheduler on app shutdown."""
    global _scheduler
    if _scheduler:
        _scheduler.shutdown()
        logger.info("Scheduler shut down cleanly")


def get_scheduler_status() -> dict:
    """Return current scheduler status for health check."""
    global _scheduler
    if _scheduler is None:
        return {"status": "not_initialized"}
    return {
        "status": "running" if _scheduler.running else "stopped",
        "jobs": len(_scheduler.get_jobs()),
    }