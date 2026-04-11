# services/upstox_service.py

"""
Upstox API integration for live market data.
Fetches real-time OHLC data from Upstox instead of using deterministic stubs.
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List

import requests

logger = logging.getLogger(__name__)

# Upstox API configuration
UPSTOX_BASE_URL = "https://api.upstox.com/v2"

# Symbol mapping: Upstox format → Display name
UPSTOX_SYMBOLS = {
    "NSE_INDEX|Nifty 50": {"display_name": "Nifty 50", "short_code": "^NSEI"},
    "BSE_INDEX|Sensex": {"display_name": "BSE Sensex", "short_code": "^BSESN"},
    "NSE_INDEX|Nifty Bank": {"display_name": "Bank Nifty", "short_code": "^NSEBANK"},
}

# Reverse mapping for convenience
SYMBOL_TO_UPSTOX = {v["short_code"]: k for k, v in UPSTOX_SYMBOLS.items()}


def get_upstox_headers() -> dict:
    """Build authorization headers for Upstox API requests."""
    from core.config import settings

    return {
        "Authorization": f"Bearer {settings.upstox_access_token}",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }


def validate_upstox_credentials() -> bool:
    """Verify that Upstox credentials are configured."""
    from core.config import settings

    if not settings.upstox_api_key or not settings.upstox_access_token:
        logger.error("Upstox credentials not configured. Check .env file.")
        return False
    return True


def convert_period_to_days(period: str) -> int:
    """
    Convert period string to approximate number of days.

    Args:
        period: One of "1mo", "3mo", "6mo", "1y", "2y", "5y"

    Returns:
        Number of days
    """
    mapping = {
        "1mo": 30,
        "3mo": 90,
        "6mo": 180,
        "1y": 365,
        "2y": 730,
        "5y": 1825,
    }
    return mapping.get(period, 90)


def fetch_upstox_historical_data(
    symbol: str, period: str = "3mo", interval: str = "1d"
) -> Dict:
    """
    Fetch historical OHLC data from Upstox API.

    Args:
        symbol: Short code like "^NSEI", "^BSESN", "^NSEBANK"
        period: Time period (1mo, 3mo, 6mo, 1y, 2y, 5y)
        interval: Candle interval (1d, 1wk, 1mo)

    Returns:
        Dict with OHLC data and metadata

    Raises:
        ValueError: If symbol is invalid or API request fails
    """

    if not validate_upstox_credentials():
        raise ValueError("Upstox credentials not configured")

    # Convert short code to Upstox format
    if symbol not in SYMBOL_TO_UPSTOX:
        raise ValueError(
            f"Unknown symbol: {symbol}. "
            f"Valid symbols: {list(SYMBOL_TO_UPSTOX.keys())}"
        )

    upstox_symbol = SYMBOL_TO_UPSTOX[symbol]
    display_name = UPSTOX_SYMBOLS[upstox_symbol]["display_name"]

    # Calculate date range
    days_back = convert_period_to_days(period)
    to_date = datetime.now().date()
    from_date = to_date - timedelta(days=days_back)

    # Map interval
    interval_mapping = {"1d": "day", "1wk": "week", "1mo": "month"}
    api_interval = interval_mapping.get(interval, "day")

    try:
        # Upstox historical candle endpoint
        url = f"{UPSTOX_BASE_URL}/historical-candle/intraday/{upstox_symbol}/{api_interval}/{from_date}/{to_date}"

        headers = get_upstox_headers()

        logger.info(f"Fetching Upstox data: {upstox_symbol} ({from_date} to {to_date})")

        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()

        data = response.json()

        if not data.get("data") or not data["data"].get("candles"):
            logger.warning(f"No data returned from Upstox for {symbol}")
            raise ValueError(f"No market data available for {symbol}")

        # Parse candles into OHLCV format
        candles = data["data"]["candles"]
        ohlc_data = []

        for candle in candles:
            # Upstox format: [timestamp, open, high, low, close, volume, oi]
            ohlc_data.append(
                {
                    "date": candle[0],  # ISO timestamp
                    "open": round(float(candle[1]), 2),
                    "high": round(float(candle[2]), 2),
                    "low": round(float(candle[3]), 2),
                    "close": round(float(candle[4]), 2),
                    "volume": int(candle[5]),
                }
            )

        # Calculate summary
        closes = [c["close"] for c in ohlc_data]
        if not closes:
            raise ValueError(f"No valid candles for {symbol}")

        latest_close = closes[-1]
        prev_close = closes[-2] if len(closes) > 1 else closes[-1]
        change = latest_close - prev_close
        change_pct = (change / prev_close * 100) if prev_close else 0.0

        period_high = max(c["high"] for c in ohlc_data)
        period_low = min(c["low"] for c in ohlc_data)

        result = {
            "symbol": symbol,
            "name": display_name,
            "period": period,
            "interval": interval,
            "count": len(ohlc_data),
            "source": "upstox",
            "summary": {
                "latest_close": round(latest_close, 2),
                "prev_close": round(prev_close, 2),
                "change": round(change, 2),
                "change_pct": round(change_pct, 2),
                "period_high": round(period_high, 2),
                "period_low": round(period_low, 2),
            },
            "data": ohlc_data,
        }

        logger.info(f"Successfully fetched {len(ohlc_data)} candles for {symbol}")
        return result

    except requests.exceptions.RequestException as e:
        logger.error(f"Upstox API request failed: {e}")
        raise ValueError(f"Failed to fetch data from Upstox: {str(e)}")
    except (KeyError, IndexError, ValueError) as e:
        logger.error(f"Error parsing Upstox response: {e}")
        raise ValueError(f"Invalid response from Upstox API: {str(e)}")


def fetch_upstox_quote(symbol: str) -> Dict:
    """
    Fetch current market quote (LTP) for a symbol.

    Args:
        symbol: Short code like "^NSEI"

    Returns:
        Dict with quote data
    """

    if not validate_upstox_credentials():
        raise ValueError("Upstox credentials not configured")

    if symbol not in SYMBOL_TO_UPSTOX:
        raise ValueError(f"Unknown symbol: {symbol}")

    upstox_symbol = SYMBOL_TO_UPSTOX[symbol]
    display_name = UPSTOX_SYMBOLS[upstox_symbol]["display_name"]

    try:
        url = f"{UPSTOX_BASE_URL}/market-quote/ltp"

        headers = get_upstox_headers()
        params = {"symbol": upstox_symbol}

        response = requests.get(url, headers=headers, params=params, timeout=10)
        response.raise_for_status()

        data = response.json()

        if not data.get("data") or not data["data"].get(upstox_symbol):
            raise ValueError(f"No quote data for {symbol}")

        quote = data["data"][upstox_symbol]

        return {
            "symbol": symbol,
            "name": display_name,
            "ltp": round(float(quote.get("ltp", 0)), 2),
            "last_traded_time": quote.get("last_traded_time"),
            "source": "upstox",
        }

    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to fetch quote from Upstox: {e}")
        raise ValueError(f"Failed to fetch quote: {str(e)}")


def fetch_upstox_market_data(
    symbol: str, period: str = "3mo", interval: str = "1d"
) -> Dict:
    """
    Main function to fetch market data from Upstox.
    Wrapper around fetch_upstox_historical_data for consistency.
    """
    return fetch_upstox_historical_data(symbol, period, interval)


def get_upstox_supported_symbols() -> Dict[str, str]:
    """Get list of supported symbols and their display names."""
    return {
        short_code: info["display_name"]
        for short_code, info in [(v["short_code"], v) for v in UPSTOX_SYMBOLS.values()]
    }
