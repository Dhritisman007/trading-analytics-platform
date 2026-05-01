# services/smc/smc_service.py

import pandas as pd
import numpy as np
import logging
from datetime import datetime, time, timezone
from utils.formatters import format_number
from services.market_service import fetch_market_data

logger = logging.getLogger(__name__)


def detect_order_blocks(df: pd.DataFrame, swing_lookback: int = 5) -> list[dict]:
    obs = []
    if len(df) < swing_lookback * 2 + 5:
        return obs

    highs  = df["high"].values
    lows   = df["low"].values
    closes = df["close"].values
    opens  = df["open"].values

    for i in range(swing_lookback, len(df) - swing_lookback):
        body_size = abs(closes[i] - opens[i])
        is_bull   = closes[i] > opens[i]
        is_bear   = closes[i] < opens[i]

        future_move = closes[i + swing_lookback] - closes[i]
        avg_body    = np.mean([abs(closes[j] - opens[j])
                               for j in range(max(0, i - 10), i)]) or 1

        is_impulsive = abs(future_move) > avg_body * 1.5
        if not is_impulsive:
            continue

        date_str = str(df.index[i])[:10]

        if is_bear and future_move > 0:
            recent_high = max(highs[max(0, i - swing_lookback):i]) if i > 0 else highs[i]
            if closes[i + swing_lookback] > recent_high:
                obs.append({
                    "type":        "bullish",
                    "date":        date_str,
                    "top":         format_number(max(opens[i], closes[i])),
                    "bottom":      format_number(min(opens[i], closes[i])),
                    "high":        format_number(highs[i]),
                    "low":         format_number(lows[i]),
                    "size":        format_number(body_size),
                    "mitigated":   _check_ob_mitigation(
                        df, i, "bullish",
                        min(opens[i], closes[i]),
                        max(opens[i], closes[i]),
                    ),
                    "strength":    "strong" if body_size > avg_body * 2 else "medium",
                    "description": "Institutional buy zone",
                })

        elif is_bull and future_move < 0:
            recent_low = min(lows[max(0, i - swing_lookback):i]) if i > 0 else lows[i]
            if closes[i + swing_lookback] < recent_low:
                obs.append({
                    "type":        "bearish",
                    "date":        date_str,
                    "top":         format_number(max(opens[i], closes[i])),
                    "bottom":      format_number(min(opens[i], closes[i])),
                    "high":        format_number(highs[i]),
                    "low":         format_number(lows[i]),
                    "size":        format_number(body_size),
                    "mitigated":   _check_ob_mitigation(
                        df, i, "bearish",
                        min(opens[i], closes[i]),
                        max(opens[i], closes[i]),
                    ),
                    "strength":    "strong" if body_size > avg_body * 2 else "medium",
                    "description": "Institutional sell zone",
                })

    return obs


def _check_ob_mitigation(df, ob_index, ob_type, ob_bottom, ob_top):
    subsequent = df.iloc[ob_index + 1:]
    if ob_type == "bullish":
        return bool((subsequent["low"] <= ob_top).any())
    return bool((subsequent["high"] >= ob_bottom).any())


def detect_liquidity_sweeps(df, swing_lookback=10, min_wick_pct=0.3):
    sweeps = []
    if len(df) < swing_lookback + 3:
        return sweeps

    highs  = df["high"].values
    lows   = df["low"].values
    closes = df["close"].values

    for i in range(swing_lookback, len(df)):
        recent_high = max(highs[i - swing_lookback:i])
        recent_low  = min(lows[i - swing_lookback:i])
        candle_size = highs[i] - lows[i]
        if candle_size == 0:
            continue

        date_str = str(df.index[i])[:10]

        if lows[i] < recent_low and closes[i] > recent_low:
            wick_below = recent_low - lows[i]
            if wick_below / candle_size >= min_wick_pct:
                sweeps.append({
                    "type":         "bullish",
                    "date":         date_str,
                    "swept_level":  format_number(recent_low),
                    "sweep_low":    format_number(lows[i]),
                    "close":        format_number(closes[i]),
                    "wick_size":    format_number(wick_below),
                    "wick_pct":     format_number(wick_below / candle_size * 100),
                    "description":  f"Swept sell-side liquidity below {format_number(recent_low)}",
                })

        elif highs[i] > recent_high and closes[i] < recent_high:
            wick_above = highs[i] - recent_high
            if wick_above / candle_size >= min_wick_pct:
                sweeps.append({
                    "type":         "bearish",
                    "date":         date_str,
                    "swept_level":  format_number(recent_high),
                    "sweep_high":   format_number(highs[i]),
                    "close":        format_number(closes[i]),
                    "wick_size":    format_number(wick_above),
                    "wick_pct":     format_number(wick_above / candle_size * 100),
                    "description":  f"Swept buy-side liquidity above {format_number(recent_high)}",
                })

    return sweeps


def detect_market_structure(df, swing_lookback=5):
    if len(df) < swing_lookback * 3:
        return {
            "bos": [], "choch": [],
            "trend": "unknown",
            "swing_highs": [], "swing_lows": [],
        }

    highs  = df["high"].values
    lows   = df["low"].values
    closes = df["close"].values

    bos_events   = []
    choch_events = []
    swing_highs  = []
    swing_lows   = []

    for i in range(swing_lookback, len(df) - swing_lookback):
        if highs[i] == max(highs[i - swing_lookback:i + swing_lookback]):
            swing_highs.append({
                "date":  str(df.index[i])[:10],
                "price": format_number(highs[i]),
                "index": i,
            })
        if lows[i] == min(lows[i - swing_lookback:i + swing_lookback]):
            swing_lows.append({
                "date":  str(df.index[i])[:10],
                "price": format_number(lows[i]),
                "index": i,
            })

    trend = "unknown"
    if len(swing_highs) >= 2 and len(swing_lows) >= 2:
        if (float(swing_highs[-1]["price"]) > float(swing_highs[-2]["price"]) and
                float(swing_lows[-1]["price"]) > float(swing_lows[-2]["price"])):
            trend = "bullish"
        elif (float(swing_highs[-1]["price"]) < float(swing_highs[-2]["price"]) and
                float(swing_lows[-1]["price"]) < float(swing_lows[-2]["price"])):
            trend = "bearish"
        else:
            trend = "ranging"

    recent_high = float(swing_highs[-1]["price"]) if swing_highs else None
    recent_low  = float(swing_lows[-1]["price"])  if swing_lows  else None

    for i in range(swing_lookback * 2, len(df)):
        date_str = str(df.index[i])[:10]

        if recent_high and closes[i] > recent_high:
            event_type = "BOS" if trend == "bullish" else "CHoCH"
            event = {
                "type":         event_type,
                "direction":    "bullish",
                "date":         date_str,
                "broken_level": format_number(recent_high),
                "close":        format_number(closes[i]),
                "description":  (
                    "Bullish BOS — trend continuation"
                    if event_type == "BOS"
                    else "CHoCH — potential bullish reversal"
                ),
            }
            (bos_events if event_type == "BOS" else choch_events).append(event)
            recent_high = closes[i]

        elif recent_low and closes[i] < recent_low:
            event_type = "BOS" if trend == "bearish" else "CHoCH"
            event = {
                "type":         event_type,
                "direction":    "bearish",
                "date":         date_str,
                "broken_level": format_number(recent_low),
                "close":        format_number(closes[i]),
                "description":  (
                    "Bearish BOS — trend continuation"
                    if event_type == "BOS"
                    else "CHoCH — potential bearish reversal"
                ),
            }
            (bos_events if event_type == "BOS" else choch_events).append(event)
            recent_low = closes[i]

    return {
        "bos":         bos_events[-10:],
        "choch":       choch_events[-5:],
        "trend":       trend,
        "swing_highs": swing_highs[-10:],
        "swing_lows":  swing_lows[-10:],
    }


def get_kill_zones() -> list[dict]:
    now          = datetime.now()
    current_time = now.time()

    zones = [
        {
            "name":        "NSE Open",
            "start":       "09:15",
            "end":         "10:15",
            "start_time":  time(9, 15),
            "end_time":    time(10, 15),
            "description": "Highest volatility — institutions set daily direction.",
            "color":       "#1D9E75",
        },
        {
            "name":        "Lunch Lull",
            "start":       "12:30",
            "end":         "13:30",
            "start_time":  time(12, 30),
            "end_time":    time(13, 30),
            "description": "Low volume — avoid trading, fake moves common.",
            "color":       "#888780",
        },
        {
            "name":        "London Open",
            "start":       "13:30",
            "end":         "15:00",
            "start_time":  time(13, 30),
            "end_time":    time(15, 0),
            "description": "European session — large institutional orders.",
            "color":       "#378ADD",
        },
        {
            "name":        "Power Hour",
            "start":       "14:30",
            "end":         "15:30",
            "start_time":  time(14, 30),
            "end_time":    time(15, 30),
            "description": "Final hour — highest volume, strong directional moves.",
            "color":       "#BA7517",
        },
        {
            "name":        "NY Pre-market",
            "start":       "19:00",
            "end":         "20:30",
            "start_time":  time(19, 0),
            "end_time":    time(20, 30),
            "description": "US pre-market affects SGX Nifty and next day open.",
            "color":       "#7F77DD",
        },
    ]

    return [
        {
            "name":        z["name"],
            "start":       z["start"],
            "end":         z["end"],
            "description": z["description"],
            "color":       z["color"],
            "active":      z["start_time"] <= current_time <= z["end_time"],
        }
        for z in zones
    ]


def detect_premium_discount(df):
    if len(df) < 20:
        return {}

    recent_high  = float(df["high"].max())
    recent_low   = float(df["low"].min())
    range_size   = recent_high - recent_low
    current      = float(df["close"].iloc[-1])

    if range_size == 0:
        return {}

    position_pct = (current - recent_low) / range_size * 100

    fib_levels = {
        "0.0":   format_number(recent_low),
        "0.236": format_number(recent_low + range_size * 0.236),
        "0.382": format_number(recent_low + range_size * 0.382),
        "0.5":   format_number(recent_low + range_size * 0.5),
        "0.618": format_number(recent_low + range_size * 0.618),
        "0.786": format_number(recent_low + range_size * 0.786),
        "1.0":   format_number(recent_high),
    }

    zone = ("premium"     if position_pct > 50 else
            "discount"    if position_pct < 50 else
            "equilibrium")

    return {
        "current_price": format_number(current),
        "swing_high":    format_number(recent_high),
        "swing_low":     format_number(recent_low),
        "position_pct":  format_number(position_pct),
        "zone":          zone,
        "zone_color":    ("#E24B4A" if zone == "premium" else
                          "#1D9E75" if zone == "discount" else "#888780"),
        "fib_levels":    fib_levels,
        "description":   (
            f"Price at {format_number(position_pct)}% of range — "
            f"{'Premium: look for sells' if zone == 'premium' else 'Discount: look for buys' if zone == 'discount' else 'Equilibrium: fair value'}."
        ),
    }


def detect_equal_highs_lows(df, tolerance_pct=0.1):
    if len(df) < 10:
        return {"equal_highs": [], "equal_lows": []}

    highs       = df["high"].values
    lows        = df["low"].values
    equal_highs = []
    equal_lows  = []

    for i in range(5, len(df)):
        for j in range(i - 5, i):
            if abs(highs[i] - highs[j]) / highs[j] * 100 <= tolerance_pct:
                equal_highs.append({
                    "date_1":      str(df.index[j])[:10],
                    "date_2":      str(df.index[i])[:10],
                    "level":       format_number((highs[i] + highs[j]) / 2),
                    "description": "Buy-side liquidity — stop hunt target",
                })
            if abs(lows[i] - lows[j]) / lows[j] * 100 <= tolerance_pct:
                equal_lows.append({
                    "date_1":      str(df.index[j])[:10],
                    "date_2":      str(df.index[i])[:10],
                    "level":       format_number((lows[i] + lows[j]) / 2),
                    "description": "Sell-side liquidity — stop hunt target",
                })

    # Deduplicate
    seen_h, seen_l   = [], []
    unique_eqh, unique_eql = [], []

    for eqh in equal_highs:
        level = float(eqh["level"])
        if not any(abs(level - s) / s * 100 < 0.5 for s in seen_h):
            unique_eqh.append(eqh)
            seen_h.append(level)

    for eql in equal_lows:
        level = float(eql["level"])
        if not any(abs(level - s) / s * 100 < 0.5 for s in seen_l):
            unique_eql.append(eql)
            seen_l.append(level)

    return {
        "equal_highs": unique_eqh[-5:],
        "equal_lows":  unique_eql[-5:],
    }


def get_full_smc_analysis(symbol="^NSEI", period="3mo", interval="1d"):
    from core.cache import cache

    cache_key = f"smc:{symbol}:{period}:{interval}"
    cached    = cache.get(cache_key)
    if cached:
        cached["_cache"] = "HIT"
        return cached

    market_data = fetch_market_data(symbol=symbol, period=period, interval=interval)

    df = pd.DataFrame(market_data["data"])
    df["date"] = pd.to_datetime(df["date"])
    df.set_index("date", inplace=True)

    order_blocks     = detect_order_blocks(df)
    liquidity_sweeps = detect_liquidity_sweeps(df)
    market_structure = detect_market_structure(df)
    premium_discount = detect_premium_discount(df)
    equal_hl         = detect_equal_highs_lows(df)
    kill_zones       = get_kill_zones()

    unmitigated_obs = [ob for ob in order_blocks if not ob["mitigated"]]

    result = {
        "symbol":           symbol,
        "name":             market_data["name"],
        "period":           period,
        "interval":         interval,
        "latest_price":     market_data["summary"]["latest_close"],
        "market_structure": market_structure,
        "order_blocks":     order_blocks[-20:],
        "unmitigated_obs":  unmitigated_obs[-10:],
        "liquidity_sweeps": liquidity_sweeps[-5:],
        "equal_highs_lows": equal_hl,
        "premium_discount": premium_discount,
        "kill_zones":       kill_zones,
        "summary": {
            "trend":            market_structure["trend"],
            "total_obs":        len(order_blocks),
            "unmitigated_obs":  len(unmitigated_obs),
            "recent_sweeps":    len(liquidity_sweeps[-5:]),
            "zone":             premium_discount.get("zone", "unknown"),
            "active_kill_zone": next(
                (kz["name"] for kz in kill_zones if kz["active"]), None
            ),
        },
    }

    cache.set(cache_key, result, ttl_seconds=1800)
    result["_cache"] = "MISS"
    return result
