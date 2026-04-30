# routers/options.py

from fastapi import APIRouter, HTTPException, Query
from services.options.options_service import get_option_chain

router = APIRouter(prefix="/options", tags=["Options — PCR, OI, Max Pain"])

VALID_SYMBOLS = ["NIFTY", "BANKNIFTY", "FINNIFTY"]


@router.get("/")
def get_options_analysis(
    symbol: str = Query(
        default="NIFTY",
        description="NIFTY, BANKNIFTY, or FINNIFTY"
    ),
    expiry_index: int = Query(
        default=0,
        ge=0, le=5,
        description="0 = nearest expiry, 1 = next, etc."
    ),
):
    """
    Full options chain analysis.

    Returns:
    - PCR (Put/Call Ratio) with sentiment label
    - Max Pain strike price
    - OI distribution — support and resistance levels
    - IV (Implied Volatility) summary
    - OI buildup — where institutions are adding positions
    - Chart-ready data arrays
    """
    symbol = symbol.upper()
    if symbol not in VALID_SYMBOLS:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid symbol. Use: {VALID_SYMBOLS}"
        )
    try:
        return get_option_chain(symbol=symbol, expiry_index=expiry_index)
    except ValueError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Options fetch failed: {str(e)}")


@router.get("/pcr")
def get_pcr(
    symbol: str = Query(default="NIFTY"),
):
    """Quick PCR snapshot — used by dashboard header."""
    try:
        result = get_option_chain(symbol=symbol.upper())
        return {
            "symbol":   symbol,
            "pcr":      result["pcr"],
            "max_pain": result["max_pain"]["max_pain"],
            "summary":  result["summary"],
        }
    except Exception as e:
        raise HTTPException(status_code=503, detail=str(e))


@router.get("/oi-chart")
def get_oi_chart(
    symbol: str = Query(default="NIFTY"),
):
    """OI chart data only — optimised for the React chart component."""
    try:
        result = get_option_chain(symbol=symbol.upper())
        return {
            "symbol":     symbol,
            "spot_price": result["spot_price"],
            "chart_data": result["chart_data"],
            "expiry":     result["selected_expiry"],
        }
    except Exception as e:
        raise HTTPException(status_code=503, detail=str(e))


@router.get("/max-pain")
def get_max_pain(
    symbol: str = Query(default="NIFTY"),
):
    """Max Pain analysis with strike-by-strike pain distribution."""
    try:
        result = get_option_chain(symbol=symbol.upper())
        return {
            "symbol":    symbol,
            "spot":      result["spot_price"],
            "max_pain":  result["max_pain"],
            "expiry":    result["selected_expiry"],
        }
    except Exception as e:
        raise HTTPException(status_code=503, detail=str(e))
