# routers/market.py
from fastapi import APIRouter, Query

from services.market_service import fetch_market_data

router = APIRouter(prefix="/market", tags=["Market Data"])

# Available symbols
AVAILABLE_SYMBOLS = [
    {"symbol": "^NSEI", "name": "Nifty 50 Index"},
    {"symbol": "^BSESN", "name": "BSE Sensex Index"},
    {"symbol": "^NSEBANK", "name": "Nifty Bank Index"},
]


@router.get("/")
def get_market_data(
    symbol: str = Query(
        default="^NSEI", description="^NSEI for Nifty, ^BSESN for Sensex"
    ),
    period: str = Query(default="3mo", description="1mo, 3mo, 6mo, 1y"),
    interval: str = Query(default="1d", description="1d, 1wk"),
):
    """
    Fetch OHLC market data for Nifty 50 or Sensex.
    Errors are handled globally by the exception handler.
    """
    return fetch_market_data(
        symbol=symbol,
        period=period,
        interval=interval,
    )


@router.get("/price")
def get_price():
    """Quick price snapshot for a single symbol."""
    return {
        "symbol": "BTCUSD",
        "price": 60000,
    }


@router.get("/symbols")
def get_available_symbols():
    """
    Get list of available symbols.
    """
    return {"symbols": AVAILABLE_SYMBOLS, "count": len(AVAILABLE_SYMBOLS)}
