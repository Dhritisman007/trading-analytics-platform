# routers/cache.py

from fastapi import APIRouter
from core.cache import cache

router = APIRouter(prefix="/cache", tags=["Admin"])


@router.get("/stats")
def get_cache_stats():
    """
    Shows what's currently in the cache.
    Useful for debugging — tells you if warmup ran and what keys are live.
    """
    return cache.stats()


@router.delete("/clear")
def clear_cache():
    """
    Manually wipe the entire cache.
    Useful during development when you want fresh data immediately.
    """
    cache.clear()
    return {"message": "Cache cleared successfully"}