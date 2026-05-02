# services/ml/pattern_detector.py

import pandas as pd
import numpy as np
import logging
from utils.formatters import format_number

logger = logging.getLogger(__name__)


def detect_patterns(df: pd.DataFrame) -> list[dict]:
    """
    Detect 15 classic Japanese candlestick patterns.
    Returns list of detected patterns with dates and descriptions.
    """
    patterns = []
    n = len(df)

    if n < 3:
        return patterns

    opens  = df["open"].values
    highs  = df["high"].values
    lows   = df["low"].values
    closes = df["close"].values

    # Helper functions
    def body_size(i):     return abs(closes[i] - opens[i])
    def candle_range(i):  return highs[i] - lows[i]
    def is_bull(i):       return closes[i] > opens[i]
    def is_bear(i):       return closes[i] < opens[i]
    def upper_wick(i):    return highs[i] - max(opens[i], closes[i])
    def lower_wick(i):    return min(opens[i], closes[i]) - lows[i]
    def avg_body(i, n=10): return np.mean([body_size(j) for j in range(max(0, i-n), i)]) or 1

    def date_str(i): return str(df.index[i])[:10]

    # ── Single candle patterns ────────────────────────────────────────────

    for i in range(1, n):
        ab    = avg_body(i)
        body  = body_size(i)
        rng   = candle_range(i)
        if rng == 0:
            continue

        uw = upper_wick(i)
        lw = lower_wick(i)

        # Doji — very small body
        if body <= rng * 0.1:
            doji_type = "Gravestone" if uw > rng * 0.6 else \
                        "Dragonfly"  if lw > rng * 0.6 else \
                        "Doji"
            patterns.append({
                "name":        doji_type,
                "type":        "neutral",
                "candles":     1,
                "date":        date_str(i),
                "price":       format_number(closes[i]),
                "reliability": "medium",
                "description": (
                    f"{doji_type} at ₹{format_number(closes[i])} — "
                    f"indecision. {'Bearish reversal signal at high' if doji_type == 'Gravestone' else 'Bullish reversal at low' if doji_type == 'Dragonfly' else 'Wait for confirmation.'}"
                ),
            })

        # Hammer — small body at top, long lower wick, after downtrend
        elif (lw >= body * 2.5 and uw <= body * 0.3 and
              is_bull(i) and closes[i] < np.mean(closes[max(0, i-5):i])):
            patterns.append({
                "name":        "Hammer",
                "type":        "bullish",
                "candles":     1,
                "date":        date_str(i),
                "price":       format_number(closes[i]),
                "reliability": "high",
                "description": (
                    f"Hammer at ₹{format_number(closes[i])} — "
                    "strong bullish reversal signal. Sellers pushed price down "
                    "but buyers took control. Look for confirmation next candle."
                ),
            })

        # Shooting Star — small body at bottom, long upper wick, after uptrend
        elif (uw >= body * 2.5 and lw <= body * 0.3 and
              closes[i] > np.mean(closes[max(0, i-5):i])):
            patterns.append({
                "name":        "Shooting Star",
                "type":        "bearish",
                "candles":     1,
                "date":        date_str(i),
                "price":       format_number(closes[i]),
                "reliability": "high",
                "description": (
                    f"Shooting Star at ₹{format_number(closes[i])} — "
                    "bearish reversal signal. Buyers pushed price up "
                    "but sellers took control. Watch for downside."
                ),
            })

        # Marubozu — very small wicks, large body (strong directional candle)
        elif (body >= ab * 1.8 and uw <= body * 0.05 and lw <= body * 0.05):
            patterns.append({
                "name":        f"{'Bullish' if is_bull(i) else 'Bearish'} Marubozu",
                "type":        "bullish" if is_bull(i) else "bearish",
                "candles":     1,
                "date":        date_str(i),
                "price":       format_number(closes[i]),
                "reliability": "high",
                "description": (
                    f"{'Bullish' if is_bull(i) else 'Bearish'} Marubozu — "
                    f"strong {'buying' if is_bull(i) else 'selling'} pressure. "
                    "No wicks means no opposition. Trend continuation likely."
                ),
            })

    # ── Two candle patterns ────────────────────────────────────────────

    for i in range(2, n):
        prev_body  = body_size(i - 1)
        curr_body  = body_size(i)

        # Bullish Engulfing
        if (is_bear(i - 1) and is_bull(i) and
                opens[i] <= closes[i - 1] and closes[i] >= opens[i - 1] and
                curr_body > prev_body * 1.1):
            patterns.append({
                "name":        "Bullish Engulfing",
                "type":        "bullish",
                "candles":     2,
                "date":        date_str(i),
                "price":       format_number(closes[i]),
                "reliability": "high",
                "description": (
                    f"Bullish Engulfing at ₹{format_number(closes[i])} — "
                    "buyers completely overpowered sellers. "
                    "Strong bullish reversal, especially at support or after downtrend."
                ),
            })

        # Bearish Engulfing
        elif (is_bull(i - 1) and is_bear(i) and
              opens[i] >= closes[i - 1] and closes[i] <= opens[i - 1] and
              curr_body > prev_body * 1.1):
            patterns.append({
                "name":        "Bearish Engulfing",
                "type":        "bearish",
                "candles":     2,
                "date":        date_str(i),
                "price":       format_number(closes[i]),
                "reliability": "high",
                "description": (
                    f"Bearish Engulfing at ₹{format_number(closes[i])} — "
                    "sellers completely overpowered buyers. "
                    "Strong bearish reversal, especially at resistance."
                ),
            })

        # Bullish Harami
        elif (is_bear(i - 1) and is_bull(i) and
              opens[i] > closes[i - 1] and closes[i] < opens[i - 1] and
              curr_body < prev_body * 0.6):
            patterns.append({
                "name":        "Bullish Harami",
                "type":        "bullish",
                "candles":     2,
                "date":        date_str(i),
                "price":       format_number(closes[i]),
                "reliability": "medium",
                "description": (
                    f"Bullish Harami at ₹{format_number(closes[i])} — "
                    "small bullish candle inside bearish candle. "
                    "Downtrend losing momentum. Wait for confirmation."
                ),
            })

        # Bearish Harami
        elif (is_bull(i - 1) and is_bear(i) and
              opens[i] < closes[i - 1] and closes[i] > opens[i - 1] and
              curr_body < prev_body * 0.6):
            patterns.append({
                "name":        "Bearish Harami",
                "type":        "bearish",
                "candles":     2,
                "date":        date_str(i),
                "price":       format_number(closes[i]),
                "reliability": "medium",
                "description": (
                    f"Bearish Harami at ₹{format_number(closes[i])} — "
                    "small bearish candle inside bullish candle. "
                    "Uptrend losing momentum. Watch for reversal."
                ),
            })

        # Tweezer Bottom — two lows at same level
        elif (is_bear(i - 1) and is_bull(i) and
              abs(lows[i] - lows[i - 1]) / (lows[i] or 1) * 100 < 0.1):
            patterns.append({
                "name":        "Tweezer Bottom",
                "type":        "bullish",
                "candles":     2,
                "date":        date_str(i),
                "price":       format_number(closes[i]),
                "reliability": "medium",
                "description": (
                    f"Tweezer Bottom at ₹{format_number(lows[i])} — "
                    "double test of support level. Buyers defending this zone."
                ),
            })

        # Tweezer Top
        elif (is_bull(i - 1) and is_bear(i) and
              abs(highs[i] - highs[i - 1]) / (highs[i] or 1) * 100 < 0.1):
            patterns.append({
                "name":        "Tweezer Top",
                "type":        "bearish",
                "candles":     2,
                "date":        date_str(i),
                "price":       format_number(closes[i]),
                "reliability": "medium",
                "description": (
                    f"Tweezer Top at ₹{format_number(highs[i])} — "
                    "double rejection at resistance. Sellers defending this zone."
                ),
            })

    # ── Three candle patterns ──────────────────────────────────────────

    for i in range(3, n):
        # Morning Star
        if (is_bear(i - 2) and                         # first: big bearish
                body_size(i - 1) < body_size(i - 2) * 0.4 and  # middle: small body
                is_bull(i) and                          # third: big bullish
                closes[i] > (opens[i - 2] + closes[i - 2]) / 2):  # closes above midpoint
            patterns.append({
                "name":        "Morning Star",
                "type":        "bullish",
                "candles":     3,
                "date":        date_str(i),
                "price":       format_number(closes[i]),
                "reliability": "very_high",
                "description": (
                    f"Morning Star at ₹{format_number(closes[i])} — "
                    "one of the most reliable bullish reversal patterns. "
                    "Signals end of downtrend. Strong buy signal."
                ),
            })

        # Evening Star
        elif (is_bull(i - 2) and                        # first: big bullish
              body_size(i - 1) < body_size(i - 2) * 0.4 and  # middle: small body
              is_bear(i) and                             # third: big bearish
              closes[i] < (opens[i - 2] + closes[i - 2]) / 2):  # closes below midpoint
            patterns.append({
                "name":        "Evening Star",
                "type":        "bearish",
                "candles":     3,
                "date":        date_str(i),
                "price":       format_number(closes[i]),
                "reliability": "very_high",
                "description": (
                    f"Evening Star at ₹{format_number(closes[i])} — "
                    "one of the most reliable bearish reversal patterns. "
                    "Signals end of uptrend. Strong sell signal."
                ),
            })

        # Three White Soldiers
        elif (all(is_bull(j) for j in [i, i-1, i-2]) and
              closes[i] > closes[i-1] > closes[i-2] and
              all(body_size(j) > body_size(j-1) * 0.8 for j in [i, i-1])):
            patterns.append({
                "name":        "Three White Soldiers",
                "type":        "bullish",
                "candles":     3,
                "date":        date_str(i),
                "price":       format_number(closes[i]),
                "reliability": "very_high",
                "description": (
                    f"Three White Soldiers at ₹{format_number(closes[i])} — "
                    "three consecutive bullish candles, each closing higher. "
                    "Very strong bullish momentum. Trend continuation expected."
                ),
            })

        # Three Black Crows
        elif (all(is_bear(j) for j in [i, i-1, i-2]) and
              closes[i] < closes[i-1] < closes[i-2] and
              all(body_size(j) > body_size(j-1) * 0.8 for j in [i, i-1])):
            patterns.append({
                "name":        "Three Black Crows",
                "type":        "bearish",
                "candles":     3,
                "date":        date_str(i),
                "price":       format_number(closes[i]),
                "reliability": "very_high",
                "description": (
                    f"Three Black Crows at ₹{format_number(closes[i])} — "
                    "three consecutive bearish candles, each closing lower. "
                    "Very strong bearish momentum. Downtrend continuation expected."
                ),
            })

    # Only return last 30 candles worth of patterns, most recent first
    patterns.sort(key=lambda x: x["date"], reverse=True)
    return patterns[:15]


def get_pattern_summary(patterns: list[dict]) -> dict:
    """Aggregate pattern signal for dashboard card."""
    if not patterns:
        return {"signal": "neutral", "count": 0, "description": "No patterns detected recently."}

    bullish  = [p for p in patterns if p["type"] == "bullish"]
    bearish  = [p for p in patterns if p["type"] == "bearish"]
    reliable = [p for p in patterns if p["reliability"] in ["high", "very_high"]]

    if len(bullish) > len(bearish):
        signal = "bullish"
        color  = "#1D9E75"
        desc   = f"{len(bullish)} bullish patterns detected. Most recent: {patterns[0]['name']}"
    elif len(bearish) > len(bullish):
        signal = "bearish"
        color  = "#E24B4A"
        desc   = f"{len(bearish)} bearish patterns detected. Most recent: {patterns[0]['name']}"
    else:
        signal = "neutral"
        color  = "#888780"
        desc   = f"{len(patterns)} patterns detected. Mixed signals — no clear bias."

    return {
        "signal":          signal,
        "color":           color,
        "count":           len(patterns),
        "bullish_count":   len(bullish),
        "bearish_count":   len(bearish),
        "reliable_count":  len(reliable),
        "most_recent":     patterns[0] if patterns else None,
        "description":     desc,
    }