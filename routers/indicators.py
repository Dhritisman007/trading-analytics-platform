# routers/indicators.py

from fastapi import APIRouter, Query
from services.indicator_calculator import get_indicators

router = APIRouter(prefix="/indicators", tags=["Technical Indicators"])


@router.get("/")
def get_indicator_data(
    symbol: str = Query(
        default="^NSEI",
        description="^NSEI for Nifty 50, ^BSESN for Sensex"
    ),
    period: str = Query(
        default="3mo",
        description="Data period: 1mo, 3mo, 6mo, 1y"
    ),
    interval: str = Query(
        default="1d",
        description="Candle interval: 1d (daily), 1wk (weekly)"
    ),
    rsi_window: int = Query(
        default=14, ge=2, le=50,
        description="RSI period (default 14)"
    ),
    ema_window: int = Query(
        default=20, ge=2, le=200,
        description="EMA period (default 20, try 50 or 200 for long-term)"
    ),
    atr_window: int = Query(
        default=14, ge=2, le=50,
        description="ATR period (default 14)"
    ),
):
    """
    Returns OHLC + RSI, EMA, MACD, ATR for the given symbol.
    Includes a 'latest' snapshot with plain-English signals for the dashboard.
    All indicator windows are configurable via query params.
    Errors are handled globally by the exception handler.
    """
    return get_indicators(
        symbol=symbol,
        period=period,
        interval=interval,
        rsi_window=rsi_window,
        ema_window=ema_window,
        atr_window=atr_window,
    )


@router.get("/latest")
def get_latest_signals(
    symbol: str = Query(default="^NSEI"),
    period: str = Query(default="3mo"),
):
    """
    Returns only the latest signals snapshot — no full data array.
    Faster for dashboard header cards that just need the current reading.
    """
    result = get_indicators(symbol=symbol, period=period)
    return {
        "symbol":  result["symbol"],
        "name":    result["name"],
        "latest":  result["latest"],
        "windows": result["windows"],
    }
