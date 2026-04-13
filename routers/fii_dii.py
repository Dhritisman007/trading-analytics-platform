# routers/fii_dii.py

from fastapi import APIRouter, HTTPException, Query
from services.fii_dii.fii_dii_service import get_fii_dii, refresh_fii_dii

router = APIRouter(prefix="/fii-dii", tags=["FII/DII Institutional Flows"])


@router.get("/")
def get_institutional_flows(
    days: int = Query(
        default=30,
        ge=5, le=90,
        description="Number of trading days to fetch (default 30)"
    ),
):
    """
    Fetch FII/DII institutional flow data with analysis.

    Returns:
    - Today's FII and DII gross buy/sell and net flows (in ₹ crore)
    - Combined market signal (BULLISH/BEARISH/CAUTIOUS)
    - Buy/sell pressure score (-100 to +100)
    - Consecutive buying/selling streaks
    - 5/10/30 day moving averages
    - Chart-ready arrays for React dashboard
    - Period summary (buy days vs sell days)

    Data source: NSE India (updated after market close ~3:30 PM IST)
    Cached for 1 hour. Updated daily via scheduler.
    """
    try:
        return get_fii_dii(days=days)
    except ValueError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/today")
def get_todays_flows():
    """
    Quick snapshot of today's FII/DII activity only.
    No historical data — just today's numbers and signal.
    Used by dashboard header cards.
    """
    try:
        result = get_fii_dii(days=10)
        return {
            "date":         result["latest_date"],
            "fii":          result["today"]["fii"],
            "dii":          result["today"]["dii"],
            "combined_net": result["today"]["combined_net"],
            "signal":       result["signal"],
            "pressure":     result["pressure"],
            "streaks":      result["streaks"],
            "_cache":       result.get("_cache"),
        }
    except ValueError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/chart")
def get_chart_data(
    days: int = Query(default=30, ge=5, le=90),
):
    """
    Returns only chart-ready arrays — no heavy analysis data.
    Optimised for the React chart component.
    """
    try:
        result = get_fii_dii(days=days)
        return {
            "symbol":     "FII/DII",
            "days":       days,
            "chart_data": result["chart_data"],
            "fetched_at": result["fetched_at"],
        }
    except ValueError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/summary")
def get_flow_summary():
    """
    Period summary — buy days vs sell days, total net flows.
    Powers the statistics cards on the dashboard.
    """
    try:
        result = get_fii_dii(days=30)
        return {
            "period_summary":  result["period_summary"],
            "moving_averages": result["moving_averages"],
            "signal":          result["signal"],
            "pressure":        result["pressure"],
        }
    except ValueError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/refresh")
def force_refresh():
    """Force refresh FII/DII data. Normally auto-refreshes at 4:30 PM IST."""
    try:
        result = refresh_fii_dii()
        return {
            "status":      "refreshed",
            "days_fetched": result.get("days_fetched"),
            "fetched_at":  result.get("fetched_at"),
            "signal":      result.get("signal", {}).get("signal"),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))