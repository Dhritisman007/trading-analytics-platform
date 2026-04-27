# routers/cache.py
from fastapi import APIRouter
from core.cache import get_cache_stats, clear_all

router = APIRouter(prefix="/cache", tags=["Cache"])

@router.get("/")
def cache_status():
    return get_cache_stats()

@router.post("/clear")
def clear_cache():
    clear_all()
    return {"status": "cleared"}