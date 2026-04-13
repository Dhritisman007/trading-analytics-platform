# services/fii_dii/fii_dii_service.py

import logging
from datetime import datetime, timezone

from services.fii_dii.data_fetcher import fetch_fii_dii_data
from services.fii_dii.flow_analyzer import analyze_flows
from core.cache import cache

logger = logging.getLogger(__name__)

CACHE_KEY = "fii_dii:data"
CACHE_TTL = 3600  # 1 hour — data updates once per day after market close


def get_fii_dii(days: int = 30) -> dict:
    """
    Fetch FII/DII data, analyze flows, and return complete response.
    Cached for 1 hour — data only updates after market close (3:30 PM IST).
    """
    cache_key = f"{CACHE_KEY}:{days}"
    cached    = cache.get(cache_key)

    if cached:
        cached["_cache"] = "HIT"
        return cached

    raw_data = fetch_fii_dii_data(days=days)

    if not raw_data:
        raise ValueError(
            "Unable to fetch FII/DII data. "
            "NSE may be unavailable. Try again later."
        )

    analysis = analyze_flows(raw_data)

    result = {
        "fetched_at":   datetime.now(timezone.utc).isoformat(),
        "data_source":  "NSE India",
        "days_fetched": len(raw_data),
        **analysis,
        "raw_data":     raw_data,  # full daily records
    }

    cache.set(cache_key, result, ttl_seconds=CACHE_TTL)
    result["_cache"] = "MISS"
    return result


def refresh_fii_dii() -> dict:
    """Force refresh — called by scheduler after market close."""
    cache.delete(f"{CACHE_KEY}:30")
    cache.delete(f"{CACHE_KEY}:10")
    return get_fii_dii(days=30)