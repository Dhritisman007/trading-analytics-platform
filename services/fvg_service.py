# services/fvg_service.py

import pandas as pd
import logging
from services.market_service import fetch_market_data
from core.exceptions import InsufficientDataError
from utils.formatters import format_number
from core.cache import cache

logger = logging.getLogger(__name__)


def _classify_fvg_strength(gap_size: float, atr: float | None) -> str:
    """
    Grade an FVG as strong / medium / weak based on its size
    relative to the average true range (volatility).
    If ATR isn't available, fall back to raw gap size.
    """
    if atr and atr > 0:
        ratio = gap_size / atr
        if ratio >= 1.5:
            return "strong"
        elif ratio >= 0.75:
            return "medium"
        else:
            return "weak"
    # Fallback: classify by absolute gap size
    if gap_size >= 100:
        return "strong"
    elif gap_size >= 30:
        return "medium"
    return "weak"


def _check_if_filled(fvg: dict, df: pd.DataFrame, fvg_index: int) -> bool:
    """
    An FVG is 'filled' when a subsequent candle trades through the gap zone.
    For bullish FVG: price comes back down and a candle's low <= fvg_top
    For bearish FVG: price comes back up and a candle's high >= fvg_bottom
    We only check candles AFTER the FVG formed.
    """
    subsequent = df.iloc[fvg_index + 1:]

    if fvg["type"] == "bullish":
        # Gap zone: fvg_bottom to fvg_top
        # Filled when a later candle's low dips into or below the gap top
        return bool((subsequent["low"] <= fvg["gap_top"]).any())

    elif fvg["type"] == "bearish":
        # Filled when a later candle's high rises into or above the gap bottom
        return bool((subsequent["high"] >= fvg["gap_bottom"]).any())

    return False


def detect_fvgs(
    symbol: str = "^NSEI",
    period: str = "3mo",
    interval: str = "1d",
    min_gap_size: float = 0.0,
    only_open: bool = False,
) -> dict:
    """
    Detect all Fair Value Gaps in the given market data.

    Args:
        symbol:       yfinance ticker
        period:       how far back to look
        interval:     candle size
        min_gap_size: filter out tiny gaps smaller than this (in price points)
        only_open:    if True, return only unfilled FVGs

    Returns:
        dict with all detected FVGs, summary counts, and latest price context
    """
    # ── Cache check ───────────────────────────────────────────────────────
    cache_key = f"fvg:{symbol}:{period}:{interval}:{min_gap_size}:{only_open}"
    cached = cache.get(cache_key)
    if cached is not None:
        logger.info(f"Cache HIT — FVGs: {cache_key}")
        return cached

    logger.info(f"Cache MISS — detecting FVGs: {cache_key}")

    # Reuse Day 2's service — same pattern as indicators
    market_data = fetch_market_data(symbol=symbol, period=period, interval=interval)

    df = pd.DataFrame(market_data["data"])
    df["date"] = pd.to_datetime(df["date"])
    df.set_index("date", inplace=True)

    # Need at least 3 candles to detect any FVG
    if len(df) < 3:
        raise InsufficientDataError(
            required=3,
            got=len(df),
            context="FVG detection requires at least 3 candles. Use a longer period."
        )

    fvgs = []

    # Slide a window of 3 candles across the entire dataset
    # i = candle 1, i+1 = candle 2 (the impulse), i+2 = candle 3
    for i in range(len(df) - 2):
        c1 = df.iloc[i]      # candle before impulse
        c2 = df.iloc[i + 1]  # impulse candle (big move)
        c3 = df.iloc[i + 2]  # candle after impulse

        c1_date = str(df.index[i].date())
        c2_date = str(df.index[i + 1].date())
        c3_date = str(df.index[i + 2].date())

        # ── Bullish FVG check ─────────────────────────────────────────────
        # Gap exists between top of C1 and bottom of C3
        if c1["high"] < c3["low"]:
            gap_bottom = format_number(c1["high"])
            gap_top    = format_number(c3["low"])
            gap_size   = format_number(c3["low"] - c1["high"])

            if gap_size < min_gap_size:
                continue

            fvg = {
                "type":        "bullish",
                "candle_1":    c1_date,
                "candle_2":    c2_date,  # the impulse candle
                "candle_3":    c3_date,
                "gap_bottom":  gap_bottom,
                "gap_top":     gap_top,
                "gap_size":    gap_size,
                "gap_size_pct": format_number(gap_size / c1["close"] * 100),
                "strength":    _classify_fvg_strength(gap_size, atr=None),
                "filled":      _check_if_filled(
                    {"type": "bullish", "gap_top": gap_top},
                    df, i + 2
                ),
                "impulse_candle": {
                    "open":  format_number(c2["open"]),
                    "close": format_number(c2["close"]),
                    "size":  format_number(abs(c2["close"] - c2["open"])),
                }
            }
            fvgs.append(fvg)

        # ── Bearish FVG check ─────────────────────────────────────────────
        # Gap exists between bottom of C1 and top of C3
        elif c1["low"] > c3["high"]:
            gap_bottom = format_number(c3["high"])
            gap_top    = format_number(c1["low"])
            gap_size   = format_number(c1["low"] - c3["high"])

            if gap_size < min_gap_size:
                continue

            fvg = {
                "type":        "bearish",
                "candle_1":    c1_date,
                "candle_2":    c2_date,
                "candle_3":    c3_date,
                "gap_bottom":  gap_bottom,
                "gap_top":     gap_top,
                "gap_size":    gap_size,
                "gap_size_pct": format_number(gap_size / c1["close"] * 100),
                "strength":    _classify_fvg_strength(gap_size, atr=None),
                "filled":      _check_if_filled(
                    {"type": "bearish", "gap_bottom": gap_bottom},
                    df, i + 2
                ),
                "impulse_candle": {
                    "open":  format_number(c2["open"]),
                    "close": format_number(c2["close"]),
                    "size":  format_number(abs(c2["close"] - c2["open"])),
                }
            }
            fvgs.append(fvg)

    # Apply open-only filter if requested
    if only_open:
        fvgs = [f for f in fvgs if not f["filled"]]

    # Sort newest first — most relevant for trading
    fvgs.sort(key=lambda x: x["candle_2"], reverse=True)

    # ── Summary stats ─────────────────────────────────────────────────────
    bullish_fvgs = [f for f in fvgs if f["type"] == "bullish"]
    bearish_fvgs = [f for f in fvgs if f["type"] == "bearish"]
    open_fvgs    = [f for f in fvgs if not f["filled"]]
    filled_fvgs  = [f for f in fvgs if f["filled"]]

    latest_price = market_data["summary"]["latest_close"]

    # Find the nearest open FVG to current price — most actionable
    nearest_open = None
    if open_fvgs:
        nearest_open = min(
            open_fvgs,
            key=lambda f: abs((f["gap_top"] + f["gap_bottom"]) / 2 - latest_price)
        )

    result = {
        "symbol":       symbol,
        "name":         market_data["name"],
        "period":       period,
        "interval":     interval,
        "latest_price": latest_price,
        "summary": {
            "total_fvgs":   len(fvgs),
            "bullish":      len(bullish_fvgs),
            "bearish":      len(bearish_fvgs),
            "open":         len(open_fvgs),
            "filled":       len(filled_fvgs),
            "fill_rate_pct": format_number(
                len(filled_fvgs) / len(fvgs) * 100 if fvgs else 0
            ),
        },
        "nearest_open_fvg": nearest_open,
        "fvgs":         fvgs,
    }

    # Cache the result for 10 minutes
    cache.set(cache_key, result, ttl_seconds=600)
    logger.info(f"Cache SET — FVGs: {cache_key}")
    return result