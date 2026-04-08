# routers/fvg.py

from fastapi import APIRouter, HTTPException, Query
from services.fvg_service import detect_fvgs

router = APIRouter(prefix="/fvg", tags=["Smart Money Concepts"])


@router.get("/")
def get_fvgs(
    symbol: str = Query(
        default="^NSEI",
        description="^NSEI for Nifty 50, ^BSESN for Sensex"
    ),
    period: str = Query(
        default="3mo",
        description="How far back to look: 1mo, 3mo, 6mo, 1y"
    ),
    interval: str = Query(
        default="1d",
        description="Candle size: 1d, 1wk"
    ),
    min_gap_size: float = Query(
        default=0.0,
        ge=0.0,
        description="Minimum gap size in price points. Use 50 to filter tiny gaps."
    ),
    only_open: bool = Query(
        default=False,
        description="If true, return only unfilled FVGs"
    ),
):
    """
    Detect Fair Value Gaps (Smart Money Concepts) in market data.
    Returns all bullish and bearish FVGs with fill status and strength rating.
    The 'nearest_open_fvg' field shows the most actionable gap near current price.
    """
    try:
        return detect_fvgs(
            symbol=symbol,
            period=period,
            interval=interval,
            min_gap_size=min_gap_size,
            only_open=only_open,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"FVG detection failed: {str(e)}")


@router.get("/open")
def get_open_fvgs(
    symbol: str = Query(default="^NSEI"),
    period: str = Query(default="3mo"),
    min_gap_size: float = Query(default=0.0, ge=0.0),
):
    """
    Shortcut endpoint — returns only unfilled FVGs.
    Used by the dashboard's 'Active FVG Zones' panel.
    """
    try:
        return detect_fvgs(
            symbol=symbol,
            period=period,
            only_open=True,
            min_gap_size=min_gap_size,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))