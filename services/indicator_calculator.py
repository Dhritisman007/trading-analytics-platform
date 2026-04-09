# services/indicator_calculator.py

import pandas as pd
import ta
import logging
from services.market_service import fetch_market_data
from core.exceptions import InvalidParameterError, InsufficientDataError
from utils.formatters import format_number
from core.cache import cache

logger = logging.getLogger(__name__)

# ── Warm-up periods ───────────────────────────────────────────────────────────
# Each indicator needs N candles before it produces a valid value.
# We drop rows before this threshold so the frontend never sees NaN.
WARMUP = {
    "rsi": 14,
    "ema_slow": 26,   # MACD needs 26-period EMA — this is the bottleneck
    "atr": 14,
}
MIN_CANDLES_REQUIRED = max(WARMUP.values()) + 10  # buffer of 10 extra candles


def _validate_windows(rsi_window: int, ema_window: int, atr_window: int):
    """Catch bad window values before they cause confusing errors downstream."""
    if not (2 <= rsi_window <= 50):
        raise InvalidParameterError(
            param="rsi_window",
            value=rsi_window,
            reason="Must be between 2 and 50"
        )
    if not (2 <= ema_window <= 200):
        raise InvalidParameterError(
            param="ema_window",
            value=ema_window,
            reason="Must be between 2 and 200"
        )
    if not (2 <= atr_window <= 50):
        raise InvalidParameterError(
            param="atr_window",
            value=atr_window,
            reason="Must be between 2 and 50"
        )


def calculate_rsi(close: pd.Series, window: int = 14) -> pd.Series:
    """
    RSI: momentum oscillator, range 0–100.
    >70 = overbought, <30 = oversold.
    """
    return ta.momentum.RSIIndicator(close=close, window=window).rsi()


def calculate_ema(close: pd.Series, window: int = 20) -> pd.Series:
    """
    EMA: trend-following, reacts faster than SMA.
    Common windows: 9, 20, 50, 200.
    """
    return ta.trend.EMAIndicator(close=close, window=window).ema_indicator()


def calculate_macd(close: pd.Series) -> dict[str, pd.Series]:
    """
    MACD: relationship between 12-day and 26-day EMA.
    Returns three series — line, signal, and histogram.
    Histogram crossing zero = potential trend change.
    """
    macd_obj = ta.trend.MACD(close=close)
    return {
        "macd":      macd_obj.macd(),
        "signal":    macd_obj.macd_signal(),
        "histogram": macd_obj.macd_diff(),
    }


def calculate_atr(
    high: pd.Series,
    low: pd.Series,
    close: pd.Series,
    window: int = 14,
) -> pd.Series:
    """
    ATR: average price range per candle — measures volatility.
    Higher ATR = more volatile. Used for stop-loss sizing.
    """
    return ta.volatility.AverageTrueRange(
        high=high, low=low, close=close, window=window
    ).average_true_range()


def _interpret_rsi(rsi_value: float) -> str:
    """Plain-English interpretation of RSI — powers beginner tooltips later."""
    if rsi_value >= 70:
        return "overbought"
    elif rsi_value <= 30:
        return "oversold"
    else:
        return "neutral"


def _get_latest_signals(df: pd.DataFrame) -> dict:
    """
    Derive simple signals from the most recent candle.
    These become the 'current snapshot' shown at the top of the dashboard.
    """
    last = df.iloc[-1]
    prev = df.iloc[-2] if len(df) > 1 else last

    # MACD crossover: histogram changes sign = momentum shift
    macd_crossover = None
    if prev["MACD_Histogram"] < 0 and last["MACD_Histogram"] >= 0:
        macd_crossover = "bullish"
    elif prev["MACD_Histogram"] > 0 and last["MACD_Histogram"] <= 0:
        macd_crossover = "bearish"

    # Price vs EMA: is price above or below the trend line?
    price_vs_ema = "above" if last["Close"] > last["EMA"] else "below"

    return {
        "rsi_value":     format_number(last["RSI"]),
        "rsi_signal":    _interpret_rsi(float(last["RSI"])),
        "ema_value":     format_number(last["EMA"]),
        "price_vs_ema":  price_vs_ema,
        "macd_value":    format_number(last["MACD"]),
        "macd_signal":   format_number(last["MACD_Signal"]),
        "macd_crossover": macd_crossover,
        "atr_value":     format_number(last["ATR"]),
        "atr_pct":       format_number(last["ATR"] / last["Close"] * 100),
    }


def get_indicators(
    symbol: str = "^NSEI",
    period: str = "3mo",
    interval: str = "1d",
    rsi_window: int = 14,
    ema_window: int = 20,
    atr_window: int = 14,
) -> dict:
    """
    Master function: fetch OHLC data, compute all indicators, return clean result.
    This is the only function the router calls.
    """
    _validate_windows(rsi_window, ema_window, atr_window)

    # Cache key encodes all parameters that affect the result
    cache_key = f"indicators:{symbol}:{period}:{interval}:{rsi_window}:{ema_window}:{atr_window}"
    cached = cache.get(cache_key)
    if cached is not None:
        logger.info(f"Cache HIT — indicators: {cache_key}")
        return cached

    logger.info(f"Cache MISS — computing indicators: {cache_key}")

    # Reuse Day 2's service — no duplicate yfinance calls
    market_data = fetch_market_data(symbol=symbol, period=period, interval=interval)

    # Rebuild DataFrame from the already-cleaned market data
    df = pd.DataFrame(market_data["data"])
    df["date"] = pd.to_datetime(df["date"])
    df.set_index("date", inplace=True)

    # Rename to match ta library's expected column names
    df.rename(columns={
        "open": "Open", "high": "High",
        "low": "Low",  "close": "Close", "volume": "Volume"
    }, inplace=True)

    if len(df) < MIN_CANDLES_REQUIRED:
        raise InsufficientDataError(
            required=MIN_CANDLES_REQUIRED,
            got=len(df),
            context="Try period=3mo or longer"
        )

    # ── Calculate indicators ──────────────────────────────────────────────────
    df["RSI"]            = calculate_rsi(df["Close"], window=rsi_window)
    df["EMA"]            = calculate_ema(df["Close"], window=ema_window)
    df["ATR"]            = calculate_atr(df["High"], df["Low"], df["Close"], window=atr_window)

    macd_data            = calculate_macd(df["Close"])
    df["MACD"]           = macd_data["macd"]
    df["MACD_Signal"]    = macd_data["signal"]
    df["MACD_Histogram"] = macd_data["histogram"]

    # Drop warm-up rows where indicators are still NaN
    df.dropna(inplace=True)

    if df.empty:
        raise ValueError("All rows were NaN after indicator calculation. Try a longer period.")

    # ── Build response ────────────────────────────────────────────────────────
    rows = []
    for date, row in df.iterrows():
        rows.append({
            "date":           str(date.date()),
            "open":           format_number(row["Open"]),
            "high":           format_number(row["High"]),
            "low":            format_number(row["Low"]),
            "close":          format_number(row["Close"]),
            "volume":         int(row["Volume"]),
            "rsi":            format_number(row["RSI"]),
            "ema":            format_number(row["EMA"]),
            "atr":            format_number(row["ATR"]),
            "macd":           format_number(row["MACD"]),
            "macd_signal":    format_number(row["MACD_Signal"]),
            "macd_histogram": format_number(row["MACD_Histogram"]),
        })

    result = {
        "symbol":     symbol,
        "name":       market_data["name"],
        "period":     period,
        "interval":   interval,
        "windows":    {"rsi": rsi_window, "ema": ema_window, "atr": atr_window},
        "count":      len(rows),
        "latest":     _get_latest_signals(df),  # snapshot for dashboard header
        "data":       rows,
    }

    # Cache the result for 5 minutes
    cache.set(cache_key, result, ttl_seconds=300)
    logger.info(f"Cache SET — indicators: {cache_key}")
    return result
