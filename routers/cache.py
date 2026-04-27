# routers/cache.py
from fastapi import APIRouter
from core.cache import get_cache_stats, clear_all

router = APIRouter(prefix="/cache", tags=["Cache"])


@router.get("/stats")
def cache_stats():
    """Return current cache statistics."""
    return get_cache_stats()


@router.delete("/clear")
def clear_cache():
    """Wipe all cached entries."""
    clear_all()
    return {"status": "cleared"}