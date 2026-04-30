# services/upstox_service.py

"""
Upstox API v2 integration — historical + intraday OHLC data.

Endpoints used:
  Historical (daily/weekly/monthly):
    GET /v2/historical-candle/{instrumentKey}/{interval}/{toDate}/{fromDate}

  Intraday — today's candles only:
    GET /v2/historical-candle/intraday/{instrumentKey}/{interval}

  Historical intraday (past days, not just today):
    GET /v2/historical-candle/{instrumentKey}/{interval}/{toDate}/{fromDate}
    with interval = "1minute", "5minute", etc.

Interval names (Upstox):
  "1minute", "3minute", "5minute", "10minute", "15minute",
  "30minute", "60minute", "day", "week", "month"

Historical intraday limit: max 30 days lookback for minute intervals,
365 days for 60minute.
"""

import logging
from datetime import datetime, timedelta, timezone, date as date_type
from typing import Dict

import requests

from utils.formatters import format_number

logger = logging.getLogger(__name__)

UPSTOX_BASE_URL = "https://api.upstox.com/v2"

# ── Symbol maps ───────────────────────────────────────────────────────────────
# Upstox uses pipe-separated instrument keys for indices
UPSTOX_SYMBOLS = {
    "NSE_INDEX|Nifty 50":   {"display_name": "Nifty 50",    "short_code": "^NSEI"},
    "NSE_INDEX|Nifty Bank": {"display_name": "Bank Nifty",  "short_code": "^NSEBANK"},
    "BSE_INDEX|SENSEX":     {"display_name": "BSE Sensex",  "short_code": "^BSESN"},
}

SYMBOL_TO_UPSTOX = {v["short_code"]: k for k, v in UPSTOX_SYMBOLS.items()}

# ── Interval mapping ───────────────────────────────────────────────────────────
# Historical candle endpoint (/historical-candle/{symbol}/{interval}/{to}/{from})
# Only these intervals are accepted:
INTERVAL_MAP_HISTORICAL = {
    "1m":  "1minute",
    "30m": "30minute",
    "1d":  "day",
    "1wk": "week",
    "1mo": "month",
    # Approximations for unsupported intervals → closest available
    "3m":  "1minute",   # use 1m, frontend can aggregate
    "5m":  "1minute",   # use 1m
    "10m": "1minute",
    "15m": "1minute",
    "60m": "30minute",  # use 30m
    "1h":  "30minute",
    "2h":  "30minute",
    "4h":  "day",
}

# Intraday-today endpoint (/historical-candle/intraday/{symbol}/{interval})
# Full interval support — today's data only
INTERVAL_MAP_INTRADAY = {
    "1m":  "1minute",
    "3m":  "3minute",
    "5m":  "5minute",
    "10m": "10minute",
    "15m": "15minute",
    "30m": "30minute",
    "60m": "60minute",
    "1h":  "60minute",
    "2h":  "60minute",
    "4h":  "60minute",
}

# Unified map (historical takes priority — used for validation)
INTERVAL_MAP = {**INTERVAL_MAP_HISTORICAL, **INTERVAL_MAP_INTRADAY}

# Max lookback in days per interval (Upstox hard limits)
INTERVAL_MAX_DAYS = {
    "1minute":  30,
    "3minute":  1,    # intraday-today only
    "5minute":  1,    # intraday-today only
    "10minute": 1,
    "15minute": 1,
    "30minute": 30,
    "60minute": 1,    # intraday-today only
    "day":      3650,
    "week":     3650,
    "month":    3650,
}

# Period string → days
PERIOD_DAYS = {
    "1d":  1,
    "5d":  5,
    "1mo": 30,
    "3mo": 90,
    "6mo": 180,
    "1y":  365,
    "2y":  730,
    "5y":  1825,
}


# ── Helpers ───────────────────────────────────────────────────────────────────

def _headers() -> dict:
    from core.config import settings
    return {
        "Authorization": f"Bearer {settings.upstox_access_token}",
        "Accept":        "application/json",
    }


def _check_credentials() -> None:
    from core.config import settings
    if not settings.upstox_access_token:
        raise ValueError(
            "UPSTOX_ACCESS_TOKEN not set. "
            "Visit http://127.0.0.1:8000/auth/upstox/login to generate a token, "
            "then add it to your .env file and restart the server."
        )


def _upstox_key(symbol: str) -> str:
    """Convert short code (^NSEI) to Upstox instrument key."""
    if symbol not in SYMBOL_TO_UPSTOX:
        raise ValueError(
            f"Unknown symbol '{symbol}'. "
            f"Valid: {list(SYMBOL_TO_UPSTOX.keys())}"
        )
    return SYMBOL_TO_UPSTOX[symbol]


def _api_interval_intraday(interval: str) -> str:
    """Map interval for the intraday-today endpoint (full set supported)."""
    mapped = INTERVAL_MAP_INTRADAY.get(interval)
    if not mapped:
        raise ValueError(
            f"Unsupported intraday interval '{interval}'. "
            f"Valid: {list(INTERVAL_MAP_INTRADAY.keys())}"
        )
    return mapped


def _api_interval_historical(interval: str) -> str:
    """Map interval for the historical endpoint (limited set: 1minute/30minute/day/week/month)."""
    mapped = INTERVAL_MAP_HISTORICAL.get(interval)
    if not mapped:
        raise ValueError(
            f"Unsupported historical interval '{interval}'. "
            f"Valid: {list(INTERVAL_MAP_HISTORICAL.keys())}"
        )
    return mapped


def _api_interval(interval: str) -> str:
    """General interval lookup — uses historical map as canonical."""
    return INTERVAL_MAP.get(interval, "day")


def _clamp_days(requested_days: int, api_interval: str) -> int:
    """Clamp requested lookback to Upstox's hard limit for that interval."""
    limit = INTERVAL_MAX_DAYS.get(api_interval, 30)
    if requested_days > limit:
        logger.warning(
            f"Requested {requested_days} days but Upstox only supports "
            f"{limit} days for {api_interval} interval. Clamping."
        )
        return limit
    return requested_days


def _parse_candles(candles: list, is_intraday: bool) -> list:
    """
    Convert Upstox candle arrays to our OHLCV dicts.

    Upstox candle format: [timestamp, open, high, low, close, volume, oi]
    timestamp is ISO-8601 with timezone: "2024-01-15T09:15:00+05:30"
    """
    data = []
    for c in candles:
        try:
            ts_raw = c[0]
            if is_intraday:
                # Keep full datetime string for lightweight-charts unix conversion
                # Strip timezone suffix so JS Date() parses cleanly
                dt = datetime.fromisoformat(ts_raw)
                # Send unix seconds for intraday — timezone-aware and
                # lets the frontend display in any tz (we use IST)
                date_str = int(dt.timestamp())
            else:
                dt = datetime.fromisoformat(ts_raw)
                date_str = dt.strftime("%Y-%m-%d")

            data.append({
                "date":   date_str,
                "open":   format_number(float(c[1])),
                "high":   format_number(float(c[2])),
                "low":    format_number(float(c[3])),
                "close":  format_number(float(c[4])),
                "volume": int(c[5]),
            })
        except Exception as e:
            logger.warning(f"Skipping malformed candle {c}: {e}")

    # Upstox returns newest-first — reverse to chronological order
    data.reverse()
    return data


def _build_summary(data: list) -> dict:
    closes      = [d["close"] for d in data]
    latest      = closes[-1]
    prev        = closes[-2] if len(closes) > 1 else latest
    change_pct  = ((latest - prev) / prev * 100) if prev else 0.0
    return {
        "latest_close": latest,
        "change_pct":   round(change_pct, 3),
        "period_high":  max(d["high"] for d in data),
        "period_low":   min(d["low"]  for d in data),
    }


# ── Core fetch functions ──────────────────────────────────────────────────────

def fetch_upstox_intraday_today(symbol: str, interval: str = "5m") -> Dict:
    """
    Fetch today's intraday candles using the dedicated intraday endpoint.
    Only available during / after market hours for the current day.

    Endpoint: GET /v2/historical-candle/intraday/{instrumentKey}/{interval}
    """
    _check_credentials()
    inst_key     = _upstox_key(symbol)
    api_interval = _api_interval_intraday(interval)   # full interval set
    is_intraday  = True

    url = f"{UPSTOX_BASE_URL}/historical-candle/intraday/{inst_key}/{api_interval}"

    logger.info(f"Upstox intraday-today: {symbol} {interval} → {url}")

    try:
        resp = requests.get(url, headers=_headers(), timeout=10)
        resp.raise_for_status()
    except requests.exceptions.HTTPError as e:
        status = e.response.status_code if e.response is not None else "?"
        body   = e.response.text[:200] if e.response is not None else ""
        logger.warning(f"Upstox intraday-today {status} for {symbol}: {body}")
        raise ValueError(f"Intraday data not available for {symbol} today (HTTP {status}). Market may be closed.")

    body = resp.json()
    candles = body.get("data", {}).get("candles", [])

    if not candles:
        raise ValueError(
            f"No intraday data for {symbol} today. "
            "Market may be closed or pre-market."
        )

    data = _parse_candles(candles, is_intraday=True)
    return {
        "symbol":      symbol,
        "name":        UPSTOX_SYMBOLS[inst_key]["display_name"],
        "interval":    interval,
        "period":      "today",
        "is_intraday": True,
        "source":      "upstox",
        "summary":     _build_summary(data),
        "data":        data,
        "count":       len(data),
    }


def fetch_upstox_historical(
    symbol: str,
    period: str = "3mo",
    interval: str = "1d",
) -> Dict:
    """
    Fetch historical candles (daily, weekly, monthly, or intraday for past days).

    Endpoint: GET /v2/historical-candle/{instrumentKey}/{interval}/{toDate}/{fromDate}

    Upstox limits:
      - Minute intervals: max 30 days lookback
      - 60-minute:        max 365 days
      - day/week/month:   no practical limit
    """
    _check_credentials()
    inst_key     = _upstox_key(symbol)
    api_interval = _api_interval_historical(interval)  # limited set only
    is_intraday  = api_interval not in ("day", "week", "month")

    days         = PERIOD_DAYS.get(period, 90)
    days         = _clamp_days(days, api_interval)

    to_date   = date_type.today()
    from_date = to_date - timedelta(days=days)

    # URL-encode the pipe in instrument key
    inst_encoded = inst_key.replace("|", "%7C")
    url = (
        f"{UPSTOX_BASE_URL}/historical-candle"
        f"/{inst_encoded}/{api_interval}"
        f"/{to_date}/{from_date}"
    )

    logger.info(
        f"Upstox historical: {symbol} {interval}({api_interval}) "
        f"{from_date} → {to_date}"
    )

    try:
        resp = requests.get(url, headers=_headers(), timeout=15)
        resp.raise_for_status()
    except requests.exceptions.HTTPError as e:
        status = e.response.status_code if e.response is not None else "?"
        body   = e.response.text[:300] if e.response is not None else ""
        logger.error(f"Upstox HTTP {status}: {body}")
        raise ValueError(f"Upstox API error {status} for {symbol}: {body}")

    body    = resp.json()
    candles = body.get("data", {}).get("candles", [])

    if not candles:
        raise ValueError(
            f"No data returned from Upstox for {symbol} "
            f"({interval}, {period}). "
            "Check credentials or try a shorter period."
        )

    data = _parse_candles(candles, is_intraday)

    return {
        "symbol":      symbol,
        "name":        UPSTOX_SYMBOLS[inst_key]["display_name"],
        "interval":    interval,
        "period":      period,
        "is_intraday": is_intraday,
        "source":      "upstox",
        "summary":     _build_summary(data),
        "data":        data,
        "count":       len(data),
    }


# ── Public wrapper (called by market_service.py) ──────────────────────────────

def fetch_upstox_market_data(
    symbol: str,
    period: str = "3mo",
    interval: str = "1d",
) -> Dict:
    """
    Main entry point — called by market_service.fetch_market_data().
    Routes to the right Upstox endpoint based on interval and period.
    """
    api_interval = _api_interval(interval)
    is_intraday  = api_interval not in ("day", "week", "month")

    # If intraday AND period is "1d", use today's endpoint for freshest data
    if is_intraday and period == "1d":
        try:
            return fetch_upstox_intraday_today(symbol, interval)
        except ValueError:
            # Market closed / pre-open — fall back to historical
            logger.info("Today's intraday not available, falling back to historical")

    # Otherwise use the historical endpoint (covers both daily and intraday)
    return fetch_upstox_historical(symbol, period, interval)


# ── Quote (LTP) ───────────────────────────────────────────────────────────────

def fetch_upstox_quote(symbol: str) -> Dict:
    """Fetch current Last Traded Price (LTP) for a symbol."""
    _check_credentials()
    inst_key = _upstox_key(symbol)

    url    = f"{UPSTOX_BASE_URL}/market-quote/ltp"
    params = {"symbol": inst_key}

    try:
        resp = requests.get(url, headers=_headers(), params=params, timeout=10)
        resp.raise_for_status()
        body  = resp.json()
        quote = body.get("data", {}).get(inst_key, {})

        return {
            "symbol": symbol,
            "name":   UPSTOX_SYMBOLS[inst_key]["display_name"],
            "ltp":    round(float(quote.get("ltp", 0)), 2),
            "source": "upstox",
        }
    except Exception as e:
        logger.error(f"Upstox quote fetch failed: {e}")
        raise ValueError(f"Quote fetch failed for {symbol}: {e}")


# ── Utility ───────────────────────────────────────────────────────────────────

def get_upstox_supported_symbols() -> Dict[str, str]:
    return {
        v["short_code"]: v["display_name"]
        for v in UPSTOX_SYMBOLS.values()
    }
