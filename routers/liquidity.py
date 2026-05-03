# routers/liquidity.py

import pandas as pd
from fastapi import APIRouter, HTTPException, Query
from services.market_service import fetch_market_data
from core.cache import cache
from utils.formatters import format_number

router = APIRouter(prefix="/liquidity", tags=["Volume & Liquidity"])


# ── Volume Profile ─────────────────────────────────────────────────────────────

def calculate_volume_profile(df: pd.DataFrame, num_bins: int = 40) -> dict:
    import numpy as np

    price_min = float(df["low"].min())
    price_max = float(df["high"].max())

    if price_min == price_max:
        return {}

    bins        = np.linspace(price_min, price_max, num_bins + 1)
    bin_centers = (bins[:-1] + bins[1:]) / 2
    bin_volumes = np.zeros(num_bins)

    for _, row in df.iterrows():
        candle_low  = float(row["low"])
        candle_high = float(row["high"])
        volume      = float(row["volume"])
        rng         = candle_high - candle_low

        for i, (bl, bh) in enumerate(zip(bins[:-1], bins[1:])):
            overlap = max(0, min(candle_high, bh) - max(candle_low, bl))
            if overlap > 0:
                bin_volumes[i] += volume * (overlap / rng if rng > 0 else 1)

    poc_idx   = int(bin_volumes.argmax())
    poc_price = float(bin_centers[poc_idx])

    # Value Area — 70% of total volume
    total_vol  = bin_volumes.sum()
    target_va  = total_vol * 0.70
    va_vol     = bin_volumes[poc_idx]
    va_low_idx = poc_idx
    va_hi_idx  = poc_idx

    while va_vol < target_va and (va_low_idx > 0 or va_hi_idx < num_bins - 1):
        add_low  = bin_volumes[va_low_idx - 1] if va_low_idx > 0              else 0
        add_high = bin_volumes[va_hi_idx  + 1] if va_hi_idx  < num_bins - 1  else 0
        if add_high >= add_low:
            va_hi_idx += 1; va_vol += add_high
        else:
            va_low_idx -= 1; va_vol += add_low

    vah     = float(bin_centers[va_hi_idx])
    val     = float(bin_centers[va_low_idx])
    current = float(df["close"].iloc[-1])
    max_vol = float(bin_volumes.max()) or 1

    if current > vah:
        position = "above_value_area"
        signal   = "bullish"
        signal_desc = "Price above Value Area High — bullish. May pull back to VAH as support."
    elif current < val:
        position = "below_value_area"
        signal   = "bearish"
        signal_desc = "Price below Value Area Low — bearish. May pull back to VAL as resistance."
    elif current > poc_price:
        position = "above_poc"
        signal   = "bullish"
        signal_desc = "Price above POC — moderate bullish bias."
    else:
        position = "below_poc"
        signal   = "bearish"
        signal_desc = "Price below POC — moderate bearish bias."

    return {
        "poc":           format_number(poc_price),
        "vah":           format_number(vah),
        "val":           format_number(val),
        "current_price": format_number(current),
        "position":      position,
        "signal":        signal,
        "signal_desc":   signal_desc,
        "histogram": [
            {
                "price":      format_number(float(bin_centers[i])),
                "volume":     round(float(bin_volumes[i])),
                "volume_pct": round(float(bin_volumes[i]) / max_vol * 100, 1),
                "is_poc":     i == poc_idx,
                "in_va":      va_low_idx <= i <= va_hi_idx,
                "is_vah":     i == va_hi_idx,
                "is_val":     i == va_low_idx,
            }
            for i in range(num_bins)
        ],
    }


# ── Liquidity Sweep detector ───────────────────────────────────────────────────

def detect_sweeps(
    df: pd.DataFrame,
    swing_lookback: int = 10,
    min_wick_pct:   float = 0.15,
) -> list[dict]:
    sweeps = []
    highs  = df["high"].values
    lows   = df["low"].values
    closes = df["close"].values
    opens  = df["open"].values
    vols   = df["volume"].values

    avg_vol = float(df["volume"].rolling(20).mean().iloc[-1]) or 1

    for i in range(swing_lookback, len(df)):
        recent_high = max(highs[i - swing_lookback:i])
        recent_low  = min(lows[i  - swing_lookback:i])
        rng         = highs[i] - lows[i]
        if rng == 0:
            continue

        date_str  = str(df.index[i])[:10]
        vol_ratio = float(vols[i]) / avg_vol

        # Bullish sweep — wick below recent low, close back above
        if lows[i] < recent_low and closes[i] > recent_low:
            wick = recent_low - lows[i]
            if wick / rng >= min_wick_pct:
                sweeps.append({
                    "type":         "bullish",
                    "date":         date_str,
                    "swept_level":  format_number(recent_low),
                    "sweep_low":    format_number(lows[i]),
                    "close":        format_number(closes[i]),
                    "wick_size":    format_number(wick),
                    "wick_pct":     format_number(wick / rng * 100),
                    "volume":       int(vols[i]),
                    "vol_ratio":    format_number(vol_ratio),
                    "high_volume":  vol_ratio > 1.5,
                    "recovery_pct": format_number((closes[i] - lows[i]) / rng * 100),
                    "description":  (
                        f"Swept sell-side liquidity below ₹{format_number(recent_low)}. "
                        f"Wick: {format_number(wick / rng * 100)}% of candle. "
                        f"Volume: {format_number(vol_ratio)}× average. "
                        f"{'High-volume sweep — institutional signature.' if vol_ratio > 1.5 else 'Normal volume sweep.'}"
                    ),
                })

        # Bearish sweep — wick above recent high, close back below
        elif highs[i] > recent_high and closes[i] < recent_high:
            wick = highs[i] - recent_high
            if wick / rng >= min_wick_pct:
                sweeps.append({
                    "type":         "bearish",
                    "date":         date_str,
                    "swept_level":  format_number(recent_high),
                    "sweep_high":   format_number(highs[i]),
                    "close":        format_number(closes[i]),
                    "wick_size":    format_number(wick),
                    "wick_pct":     format_number(wick / rng * 100),
                    "volume":       int(vols[i]),
                    "vol_ratio":    format_number(vol_ratio),
                    "high_volume":  vol_ratio > 1.5,
                    "recovery_pct": format_number((highs[i] - closes[i]) / rng * 100),
                    "description":  (
                        f"Swept buy-side liquidity above ₹{format_number(recent_high)}. "
                        f"Wick: {format_number(wick / rng * 100)}% of candle. "
                        f"Volume: {format_number(vol_ratio)}× average. "
                        f"{'High-volume sweep — institutional signature.' if vol_ratio > 1.5 else 'Normal volume sweep.'}"
                    ),
                })

    sweeps.sort(key=lambda x: x["date"], reverse=True)
    return sweeps


# ── VWAP ──────────────────────────────────────────────────────────────────────

def calculate_vwap_series(df: pd.DataFrame) -> dict:
    import numpy as np

    tp        = (df["high"] + df["low"] + df["close"]) / 3
    tp_vol    = tp * df["volume"]
    cum_tpvol = tp_vol.cumsum()
    cum_vol   = df["volume"].cumsum()
    vwap      = cum_tpvol / cum_vol.replace(0, np.nan)

    tp_sq     = (tp ** 2 * df["volume"]).cumsum()
    variance  = tp_sq / cum_vol.replace(0, np.nan) - vwap ** 2
    std       = variance.apply(lambda x: np.sqrt(max(float(x), 0)) if pd.notna(x) else 0)

    current    = float(df["close"].iloc[-1])
    vwap_val   = float(vwap.iloc[-1])
    std_val    = float(std.iloc[-1])

    series = []
    for date, v in vwap.items():
        s = float(std.loc[date])
        series.append({
            "date":   str(date)[:10],
            "vwap":   format_number(v),
            "upper1": format_number(float(v) + s),
            "lower1": format_number(float(v) - s),
            "upper2": format_number(float(v) + 2 * s),
            "lower2": format_number(float(v) - 2 * s),
        })

    above = current > vwap_val
    return {
        "vwap":       format_number(vwap_val),
        "std":        format_number(std_val),
        "upper_1sd":  format_number(vwap_val + std_val),
        "lower_1sd":  format_number(vwap_val - std_val),
        "upper_2sd":  format_number(vwap_val + 2 * std_val),
        "lower_2sd":  format_number(vwap_val - 2 * std_val),
        "above_vwap": above,
        "signal":     "bullish" if above else "bearish",
        "diff_pct":   format_number((current - vwap_val) / vwap_val * 100) if vwap_val else "0",
        "description": (
            f"Price {'above' if above else 'below'} VWAP ₹{format_number(vwap_val)} "
            f"by {format_number(abs((current - vwap_val) / vwap_val * 100)) if vwap_val else '0'}%. "
            f"{'Institutions net buyers today.' if above else 'Institutions net sellers today.'}"
        ),
        "series": series,
    }


# ── Volume analysis ────────────────────────────────────────────────────────────

def analyse_volume(df: pd.DataFrame) -> dict:
    import numpy as np

    vol        = df["volume"]
    closes     = df["close"]
    avg_20     = float(vol.rolling(20).mean().iloc[-1])
    avg_50     = float(vol.rolling(50).mean().iloc[-1]) if len(df) >= 50 else avg_20
    latest_vol = float(vol.iloc[-1])
    ratio_20   = round(latest_vol / avg_20, 2) if avg_20 else 1

    # Volume trend — is volume expanding or contracting?
    vol_ma5  = float(vol.rolling(5).mean().iloc[-1])
    vol_ma20 = float(vol.rolling(20).mean().iloc[-1])
    vol_trend = "expanding" if vol_ma5 > vol_ma20 * 1.1 else \
                "contracting" if vol_ma5 < vol_ma20 * 0.9 else "normal"

    # Up-volume vs down-volume
    up_vol   = float(vol[closes > closes.shift()].sum())
    down_vol = float(vol[closes < closes.shift()].sum())
    total    = up_vol + down_vol
    up_pct   = round(up_vol / total * 100, 1) if total > 0 else 50

    # Recent bars data
    recent = []
    for date, row in df.tail(30).iterrows():
        recent.append({
            "date":      str(date)[:10],
            "volume":    int(row["volume"]),
            "is_up":     float(row["close"]) >= float(row["open"]),
            "vol_ratio": round(float(row["volume"]) / avg_20, 2) if avg_20 else 1.0,
        })

    return {
        "latest_volume":  int(latest_vol),
        "avg_volume_20":  int(avg_20),
        "avg_volume_50":  int(avg_50),
        "ratio_20":       ratio_20,
        "vol_trend":      vol_trend,
        "up_volume_pct":  up_pct,
        "down_volume_pct": round(100 - up_pct, 1),
        "is_high_volume": ratio_20 > 1.5,
        "description": (
            f"Today's volume is {ratio_20}× the 20-day average. "
            f"Volume is {vol_trend}. "
            f"{up_pct}% of recent volume is on up-candles."
        ),
        "recent_bars": recent,
    }


# ── API Endpoints ──────────────────────────────────────────────────────────────

@router.get("/")
def get_full_liquidity_analysis(
    symbol: str = Query(default="^NSEI"),
    period: str = Query(default="3mo"),
    bins:   int = Query(default=40, ge=10, le=80),
):
    """
    Full volume and liquidity analysis — Volume Profile,
    VWAP, Volume Analysis, Liquidity Sweeps in one call.
    """
    cache_key = f"liquidity:{symbol}:{period}:{bins}"
    cached    = cache.get(cache_key)
    if cached:
        cached["_cache"] = "HIT"
        return cached

    try:
        market = fetch_market_data(symbol=symbol, period=period)
        df     = pd.DataFrame(market["data"])
        df["date"] = pd.to_datetime(df["date"])
        df.set_index("date", inplace=True)

        vp      = calculate_volume_profile(df, num_bins=bins)
        vwap    = calculate_vwap_series(df)
        vol     = analyse_volume(df)
        sweeps  = detect_sweeps(df)

        # Sweep stats
        bull_sweeps = [s for s in sweeps if s["type"] == "bullish"]
        bear_sweeps = [s for s in sweeps if s["type"] == "bearish"]
        hv_sweeps   = [s for s in sweeps if s["high_volume"]]

        result = {
            "symbol":          symbol,
            "name":            market["name"],
            "period":          period,
            "latest_price":    market["summary"]["latest_close"],
            "volume_profile":  vp,
            "vwap":            vwap,
            "volume_analysis": vol,
            "sweeps":          sweeps,
            "sweep_summary": {
                "total":          len(sweeps),
                "bullish":        len(bull_sweeps),
                "bearish":        len(bear_sweeps),
                "high_volume":    len(hv_sweeps),
                "most_recent":    sweeps[0] if sweeps else None,
                "bias": (
                    "bullish" if len(bull_sweeps) > len(bear_sweeps) else
                    "bearish" if len(bear_sweeps) > len(bull_sweeps) else
                    "neutral"
                ),
            },
        }

        cache.set(cache_key, result, ttl_seconds=900)
        result["_cache"] = "MISS"
        return result

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sweeps")
def get_sweeps_only(
    symbol: str = Query(default="^NSEI"),
    period: str = Query(default="3mo"),
):
    """Liquidity sweeps only — faster endpoint."""
    try:
        market = fetch_market_data(symbol=symbol, period=period)
        df     = pd.DataFrame(market["data"])
        df["date"] = pd.to_datetime(df["date"])
        df.set_index("date", inplace=True)
        sweeps = detect_sweeps(df)
        return {
            "symbol":  symbol,
            "sweeps":  sweeps,
            "total":   len(sweeps),
            "bullish": len([s for s in sweeps if s["type"] == "bullish"]),
            "bearish": len([s for s in sweeps if s["type"] == "bearish"]),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/volume-profile")
def get_volume_profile_only(
    symbol: str = Query(default="^NSEI"),
    period: str = Query(default="3mo"),
    bins:   int = Query(default=40),
):
    """Volume Profile only — POC, VAH, VAL, histogram."""
    try:
        market = fetch_market_data(symbol=symbol, period=period)
        df     = pd.DataFrame(market["data"])
        df["date"] = pd.to_datetime(df["date"])
        df.set_index("date", inplace=True)
        return calculate_volume_profile(df, num_bins=bins)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
