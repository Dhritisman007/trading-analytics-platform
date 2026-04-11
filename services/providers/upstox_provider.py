# services/providers/upstox_provider.py

from datetime import datetime, timedelta

import pandas as pd
import upstox_client
from upstox_client.rest import ApiException

from core.config import settings
from core.exceptions import DataFetchError, SymbolNotFoundError
from utils.formatters import format_number

# Map your symbols to Upstox instrument keys
SYMBOL_MAP = {
    "^NSEI": "NSE_INDEX|Nifty 50",
    "^BSESN": "BSE_INDEX|SENSEX",
    "^NSEBANK": "NSE_INDEX|Nifty Bank",
    "^CNXMIDCAP": "NSE_INDEX|NIFTY MIDCAP 100",
}

KNOWN_NAMES = {
    "^NSEI": "Nifty 50",
    "^BSESN": "BSE Sensex",
    "^NSEBANK": "Bank Nifty",
    "^CNXMIDCAP": "Nifty Midcap 100",
}

PERIOD_TO_DAYS = {
    "1mo": 30,
    "3mo": 90,
    "6mo": 180,
    "1y": 365,
    "2y": 730,
    "5y": 1825,
}

INTERVAL_MAP = {
    "1d": "day",
    "1wk": "week",
    "1mo": "month",
}


def _get_api_client() -> upstox_client.HistoryApi:
    if not settings.upstox_access_token:
        raise DataFetchError(
            "Upstox",
            "UPSTOX_ACCESS_TOKEN is empty. "
            "Visit /auth/upstox/login to generate a token.",
        )
    configuration = upstox_client.Configuration()
    configuration.access_token = settings.upstox_access_token
    return upstox_client.HistoryApi(upstox_client.ApiClient(configuration))


def fetch_ohlc(symbol: str, period: str, interval: str) -> dict:
    """
    Fetch historical OHLC candles from Upstox.
    Returns same shape as yfinance_provider — drop-in replacement.
    """
    instrument_key = SYMBOL_MAP.get(symbol)
    if not instrument_key:
        raise SymbolNotFoundError(symbol)

    days = PERIOD_TO_DAYS.get(period, 90)
    to_date = datetime.today().strftime("%Y-%m-%d")
    from_date = (datetime.today() - timedelta(days=days)).strftime("%Y-%m-%d")
    upstox_interval = INTERVAL_MAP.get(interval, "day")

    try:
        api = _get_api_client()
        response = api.get_historical_candle_data1(
            instrument_key=instrument_key,
            interval=upstox_interval,
            to_date=to_date,
            from_date=from_date,
            api_version="2.0",
        )
    except ApiException as e:
        raise DataFetchError("Upstox Historical API", reason=str(e))

    if not response or not response.data or not response.data.candles:
        raise SymbolNotFoundError(symbol)

    # Upstox candle: [timestamp, open, high, low, close, volume, oi]
    ohlc = []
    for candle in response.data.candles:
        ohlc.append(
            {
                "date": str(pd.to_datetime(candle[0]).date()),
                "open": format_number(candle[1]),
                "high": format_number(candle[2]),
                "low": format_number(candle[3]),
                "close": format_number(candle[4]),
                "volume": int(candle[5]),
            }
        )

    # Upstox returns newest first — reverse to oldest first
    ohlc.sort(key=lambda x: x["date"])

    closes = [r["close"] for r in ohlc]
    latest = closes[-1]
    prev = closes[-2] if len(closes) > 1 else latest

    return {
        "symbol": symbol,
        "name": KNOWN_NAMES.get(symbol, symbol),
        "period": period,
        "interval": interval,
        "count": len(ohlc),
        "source": "upstox_historical",
        "summary": {
            "latest_close": latest,
            "prev_close": prev,
            "change": format_number(latest - prev),
            "change_pct": format_number((latest - prev) / prev * 100),
            "period_high": max(r["high"] for r in ohlc),
            "period_low": min(r["low"] for r in ohlc),
        },
        "data": ohlc,
    }
