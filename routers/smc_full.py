# routers/smc_full.py

import pandas as pd
from fastapi import APIRouter, HTTPException, Query
from services.market_service import fetch_market_data

router = APIRouter(prefix="/smc-full", tags=["Smart Money Concepts — Full"])


@router.get("/")
def get_smc_analysis(
    symbol: str = Query(default="^NSEI"),
    period: str = Query(default="3mo"),
    interval: str = Query(default="1d"),
):
    """Full SMC analysis — Order Blocks, Sweeps, BOS/CHoCH, Kill Zones."""
    try:
        from services.smc.smc_service import get_full_smc_analysis
        return get_full_smc_analysis(
            symbol=symbol,
            period=period,
            interval=interval,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/volume-profile")
def get_volume_profile(
    symbol: str = Query(default="^NSEI"),
    period: str = Query(default="3mo"),
    bins:   int = Query(default=30, ge=10, le=100),
):
    """Volume Profile — POC, VAH, VAL, histogram."""
    try:
        from services.indicators.volume_profile import calculate_volume_profile
        market = fetch_market_data(symbol=symbol, period=period)
        df     = pd.DataFrame(market["data"])
        df["date"] = pd.to_datetime(df["date"])
        df.set_index("date", inplace=True)
        return calculate_volume_profile(df, num_bins=bins)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/vwap")
def get_vwap(
    symbol: str = Query(default="^NSEI"),
    period: str = Query(default="1mo"),
):
    """VWAP with standard deviation bands."""
    try:
        from services.indicators.volume_profile import calculate_vwap
        market = fetch_market_data(symbol=symbol, period=period)
        df     = pd.DataFrame(market["data"])
        df["date"] = pd.to_datetime(df["date"])
        df.set_index("date", inplace=True)
        return calculate_vwap(df)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/kill-zones")
def get_kill_zones():
    """Current ICT Kill Zones for Indian markets."""
    try:
        from services.smc.smc_service import get_kill_zones
        return {"kill_zones": get_kill_zones()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))