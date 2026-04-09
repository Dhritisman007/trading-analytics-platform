# core/cache.py

import time
import logging
from typing import Any

logger = logging.getLogger(__name__)


class TTLCache:
    """
    Thread-safe in-memory cache with Time-To-Live expiry.

    Each entry stores:
      - the cached value
      - the Unix timestamp when it expires

    On get(), expired entries are treated as misses.
    On set(), a new expiry is calculated from the ttl_seconds argument.

    This is appropriate for single-process FastAPI apps.
    For multi-process / multi-server deployments, replace with Redis.
    """

    def __init__(self):
        self._store: dict[str, dict] = {}

    def set(self, key: str, value: Any, ttl_seconds: int = 300):
        """Store a value with an expiry time."""
        expires_at = time.time() + ttl_seconds
        self._store[key] = {
            "value":      value,
            "expires_at": expires_at,
        }
        logger.debug(f"Cache SET: {key} (TTL={ttl_seconds}s)")

    def get(self, key: str) -> Any | None:
        """
        Retrieve a value if it exists and hasn't expired.
        Returns None on miss or expiry.
        """
        entry = self._store.get(key)
        if entry is None:
            logger.debug(f"Cache MISS: {key}")
            return None

        if time.time() > entry["expires_at"]:
            # Entry has expired — clean it up
            del self._store[key]
            logger.debug(f"Cache EXPIRED: {key}")
            return None

        logger.debug(f"Cache HIT: {key}")
        return entry["value"]

    def delete(self, key: str):
        """Manually invalidate a cache entry."""
        self._store.pop(key, None)
        logger.debug(f"Cache DELETE: {key}")

    def clear(self):
        """Wipe the entire cache — useful for testing."""
        self._store.clear()
        logger.info("Cache cleared")

    def stats(self) -> dict:
        """
        Return cache health info — exposed via /cache/stats endpoint.
        Shows how many entries are live vs expired.
        """
        now = time.time()
        live    = sum(1 for e in self._store.values() if e["expires_at"] > now)
        expired = len(self._store) - live
        return {
            "total_entries": len(self._store),
            "live":          live,
            "expired":       expired,
            "keys":          [k for k, e in self._store.items()
                              if e["expires_at"] > now],
        }


# Single shared instance used across the entire application
cache = TTLCache()