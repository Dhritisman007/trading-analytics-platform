# routers/risk.py

from fastapi import APIRouter, HTTPException, Query
from services.risk_service import (
    full_risk_analysis,
    calculate_atr_stops,
    calculate_position_size,
    calculate_risk_reward,
)
from services.indicator_calculator import get_indicators

router = APIRouter(prefix="/risk", tags=["Risk Management"])

@router.get("/")
def get_risk_analysis(
    capital: float = Query(
        ...,
        description="Your total trading capital in ₹ (e.g. 500000)"
    ),
    entry_price: float = Query(
        ...,
        description="Price at which you plan to enter the trade"
    ),
    stop_loss: float = Query(
        ...,
        description="Stop loss price — where you exit if wrong"
    ),
    target_price: float = Query(
        ...,
        description="Target price — where you take profit"
    ),
    risk_pct: float = Query(
        default=1.0,
        ge=0.1, le=5.0,
        description="% of capital to risk on this trade (default 1%)"
    ),
    signal_confidence: float | None = Query(
        default=None,
        ge=0, le=100,
        description="ML model confidence % from /predict (optional)"
    ),
    rsi_value: float | None = Query(
        default=None,
        ge=0, le=100,
        description="Current RSI value from /indicators (optional)"
    ),
    signal: str | None = Query(
        default=None,
        description="BUY or SELL signal from /predict (optional)"
    ),
    brokerage_pct: float = Query(
        default=0.03,
        description="Total brokerage + STT as % (default 0.03%)"
    ),
):
    """
    Full risk analysis for a trade.

    Combines position sizing, R:R calculation, breakeven analysis,
    and optional ML signal scoring into one comprehensive response.

    Tip: Call /predict first to get signal_confidence and signal,
    then call /indicators to get rsi_value and atr,
    then call this endpoint with all values combined.
    """
    try:
        return full_risk_analysis(
            capital=capital,
            risk_pct=risk_pct,
            entry_price=entry_price,
            stop_loss=stop_loss,
            target_price=target_price,
            signal_confidence=signal_confidence,
            rsi_value=rsi_value,
            signal=signal,
            brokerage_pct=brokerage_pct,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/quick")
def quick_position_size(
    capital: float = Query(..., description="Capital in ₹"),
    entry_price: float = Query(..., description="Entry price"),
    stop_loss: float = Query(..., description="Stop loss price"),
    risk_pct: float = Query(default=1.0, ge=0.1, le=5.0),
):
    """
    Quick position size calculator — just the essentials.
    No need for target price.
    """
    try:
        result = calculate_position_size(capital, risk_pct, entry_price, stop_loss)
        return {
            "units":            result["units"],
            "risk_amount":      result["risk_amount"],
            "risk_pct_actual":  result["risk_pct_actual"],
            "total_cost":       result["total_cost"],
            "capital_used_pct": result["capital_used_pct"],
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/atr-stops")
def get_atr_stops(
    symbol: str = Query(default="^NSEI"),
    entry_price: float = Query(..., description="Your entry price"),
    atr_multiplier: float = Query(
        default=1.5, ge=0.5, le=5.0,
        description="ATR multiplier for stop loss (default 1.5)"
    ),
    rr_ratio: float = Query(
        default=2.0, ge=1.0, le=10.0,
        description="Desired R:R ratio (default 2.0)"
    ),
):
    """
    Auto-calculate stop loss and target using live ATR from the market.
    Fetches current ATR for the symbol and computes volatility-adjusted levels.
    """
    try:
        # Fetch live ATR from indicators
        indicators = get_indicators(symbol=symbol, period="3mo")
        latest_atr = indicators["data"][-1]["atr"]

        atr_result = calculate_atr_stops(
            entry_price=entry_price,
            atr=latest_atr,
            atr_multiplier=atr_multiplier,
            rr_ratio=rr_ratio,
        )

        return {
            "symbol":          symbol,
            "entry_price":     entry_price,
            "latest_atr":      latest_atr,
            **atr_result,
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))