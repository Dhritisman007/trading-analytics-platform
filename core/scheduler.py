# core/scheduler.py

import logging
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger

logger = logging.getLogger(__name__)

scheduler = BackgroundScheduler(
    job_defaults={
        "coalesce":           True,
        "max_instances":      1,
        "misfire_grace_time": 60,
    }
)


def _refresh_market_data():
    """Refresh Nifty + Sensex OHLC data every 5 minutes."""
    from services.market_service import fetch_market_data
    from core.cache import set_cache

    symbols = [
        ("^NSEI",  "3mo", "1d"),
        ("^BSESN", "3mo", "1d"),
        ("^NSEI",  "1y",  "1d"),
    ]
    for symbol, period, interval in symbols:
        try:
            data = fetch_market_data(symbol=symbol, period=period, interval=interval)
            cache_key = f"market:{symbol}:{period}:{interval}"
            set_cache(cache_key, data, ttl_seconds=360)
            logger.info(f"Refreshed market data: {cache_key}")
        except Exception as e:
            logger.error(f"Failed to refresh market data for {symbol}: {e}")


def _refresh_indicators():
    """Refresh indicators for Nifty 50 every 15 minutes."""
    from services.indicator_calculator import get_indicators
    from core.cache import set_cache

    configs = [
        ("^NSEI",  "3mo", "1d", 14, 20, 14),
        ("^BSESN", "3mo", "1d", 14, 20, 14),
    ]
    for symbol, period, interval, rsi_w, ema_w, atr_w in configs:
        try:
            data = get_indicators(
                symbol=symbol, period=period, interval=interval,
                rsi_window=rsi_w, ema_window=ema_w, atr_window=atr_w,
            )
            cache_key = f"indicators:{symbol}:{period}:{interval}:{rsi_w}:{ema_w}:{atr_w}"
            set_cache(cache_key, data, ttl_seconds=960)
            logger.info(f"Refreshed indicators: {cache_key}")
        except Exception as e:
            logger.error(f"Failed to refresh indicators for {symbol}: {e}")


def _refresh_fvgs():
    """Refresh FVG detection every 30 minutes."""
    from services.fvg_service import detect_fvgs
    from core.cache import set_cache

    try:
        data = detect_fvgs(symbol="^NSEI", period="3mo", interval="1d")
        cache_key = "fvg:^NSEI:3mo:1d"
        set_cache(cache_key, data, ttl_seconds=1860)
        logger.info(f"Refreshed FVGs: {cache_key}")
    except Exception as e:
        logger.error(f"Failed to refresh FVGs: {e}")


def _refresh_news():
    """Refresh news cache every 15 minutes."""                    # ← NEW (Day 12)
    from services.news.news_service import refresh_news
    try:
        result = refresh_news()
        logger.info(f"Refreshed news: {result['sources']['total']} articles")
    except Exception as e:
        logger.error(f"Failed to refresh news: {e}")


def start_scheduler():
    """Register all jobs and start the scheduler."""
    scheduler.add_job(
        _refresh_market_data,
        trigger=IntervalTrigger(minutes=5),
        id="refresh_market",
        name="Refresh market data",
        replace_existing=True,
    )
    scheduler.add_job(
        _refresh_indicators,
        trigger=IntervalTrigger(minutes=15),
        id="refresh_indicators",
        name="Refresh indicators",
        replace_existing=True,
    )
    scheduler.add_job(
        _refresh_fvgs,
        trigger=IntervalTrigger(minutes=30),
        id="refresh_fvgs",
        name="Refresh FVGs",
        replace_existing=True,
    )
    scheduler.add_job(                                            # ← NEW (Day 12)
        _refresh_news,
        trigger=IntervalTrigger(minutes=15),
        id="refresh_news",
        name="Refresh financial news",
        replace_existing=True,
    )

    scheduler.start()
    logger.info(
        "Scheduler started — "
        "market:5min · indicators:15min · fvgs:30min · news:15min"
    )


def stop_scheduler():
    """Gracefully stop the scheduler on app shutdown."""
    if scheduler.running:
        scheduler.shutdown(wait=False)
        logger.info("Scheduler stopped")


def get_scheduler_status() -> dict:
    """Returns current job status — used by /health endpoint."""
    if not scheduler.running:
        return {"running": False, "jobs": []}

    jobs = []
    for job in scheduler.get_jobs():
        jobs.append({
            "id":       job.id,
            "name":     job.name,
            "next_run": str(job.next_run_time) if job.next_run_time else None,
        })
    return {"running": True, "jobs": jobs}