# services/yfinance_service.py

"""
Yahoo Finance integration for live market data.
Fetches real historical OHLC data from yfinance.
"""

import logging
from datetime import datetime, timedelta
from typing import Dict

import yfinance as yf

from utils.formatters import format_number

logger = logging.getLogger(__name__)

# Symbol mapping
YFINANCE_SYMBOLS = {
    "^NSEI": "Nifty 50 Index",
    "^BSESN": "BSE Sensex Index",
    "^NSEBANK": "Bank Nifty Index",
}


def fetch_yfinance_market_data(
    symbol: str, period: str = "3mo", interval: str = "1d"
) -> Dict:
    """
    Fetch real market data from Yahoo Finance.

    Args:
        symbol: Ticker symbol (^NSEI, ^BSESN, ^NSEBANK)
        period: Time period ("1mo", "3mo", "6mo", "1y", "2y", "5y")
        interval: Interval ("1d", "1wk", "1mo")

    Returns:
        Dictionary with OHLCV data and summary
    """
    if symbol not in YFINANCE_SYMBOLS:
        raise ValueError(f"Unknown symbol: {symbol}")

    try:
        logger.info(f"Fetching Yahoo Finance data: {symbol} ({period}, {interval})")

        # Fetch data from yfinance
        ticker = yf.Ticker(symbol)
        df = ticker.history(period=period, interval=interval)

        if df.empty:
            logger.warning(f"No data returned from yfinance for {symbol}")
            raise ValueError(f"No market data available for {symbol}")

        # Format the data
        data = []
        for date, row in df.iterrows():
            data.append(
                {
                    "date": date.strftime("%Y-%m-%d"),
                    "open": format_number(row["Open"]),
                    "high": format_number(row["High"]),
                    "low": format_number(row["Low"]),
                    "close": format_number(row["Close"]),
                    "volume": int(row["Volume"]),
                }
            )

        # Calculate summary
        closes = [d["close"] for d in data]
        latest_close = closes[-1]
        prev_close = closes[-2] if len(closes) > 1 else closes[-1]
        change_pct = (
            ((latest_close - prev_close) / prev_close * 100) if prev_close else 0
        )

        period_high = max(d["high"] for d in data)
        period_low = min(d["low"] for d in data)

        summary = {
            "latest_close": latest_close,
            "change_pct": round(change_pct, 3),
            "period_high": period_high,
            "period_low": period_low,
        }

        result = {
            "symbol": symbol,
            "name": YFINANCE_SYMBOLS[symbol],
            "summary": summary,
            "data": data,
            "count": len(data),
        }

        logger.info(f"Successfully fetched {len(data)} candles for {symbol}")
        return result

    except Exception as e:
        logger.error(f"Yahoo Finance fetch failed: {e}")
        raise
