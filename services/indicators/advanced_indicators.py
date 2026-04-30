# services/indicators/advanced_indicators.py

import pandas as pd
import numpy as np
import logging
from utils.formatters import format_number

logger = logging.getLogger(__name__)


# ── VWAP ──────────────────────────────────────────────────────────────────────

def calculate_vwap(df: pd.DataFrame) -> pd.DataFrame:
    """
    Volume Weighted Average Price.

    The institutional benchmark — if price is above VWAP,
    institutions are net buyers today. Below = net sellers.
    Resets at the start of each trading day.

    Bands at ±1 and ±2 standard deviations show
    overbought/oversold relative to fair value.
    """
    typical_price     = (df["high"] + df["low"] + df["close"]) / 3
    tp_x_vol          = typical_price * df["volume"]
    cumulative_tp_vol = tp_x_vol.cumsum()
    cumulative_vol    = df["volume"].cumsum()

    vwap = cumulative_tp_vol / cumulative_vol.replace(0, np.nan)

    # Standard deviation bands
    tp_sq    = (typical_price ** 2 * df["volume"]).cumsum()
    variance = (tp_sq / cumulative_vol.replace(0, np.nan)) - vwap ** 2
    std      = variance.apply(lambda x: np.sqrt(max(float(x), 0)) if pd.notna(x) else 0)

    df["vwap"]     = vwap.round(2)
    df["vwap_u1"]  = (vwap + std).round(2)      # +1 std dev
    df["vwap_l1"]  = (vwap - std).round(2)      # -1 std dev
    df["vwap_u2"]  = (vwap + 2 * std).round(2)  # +2 std dev
    df["vwap_l2"]  = (vwap - 2 * std).round(2)  # -2 std dev

    return df


def get_vwap_signal(df: pd.DataFrame) -> dict:
    """Plain-English VWAP interpretation for latest candle."""
    last       = df.iloc[-1]
    close      = float(last["close"])
    vwap       = float(last["vwap"]) if pd.notna(last["vwap"]) else 0

    if vwap == 0:
        return {"signal": "unknown", "description": "VWAP not calculated"}

    diff_pct = round((close - vwap) / vwap * 100, 2)
    above    = close > vwap

    if close > float(last["vwap_u2"]):
        signal      = "extremely_overbought"
        color       = "#E24B4A"
        description = f"Price {diff_pct}% above VWAP — extremely overbought. Strong mean reversion risk."
    elif close > float(last["vwap_u1"]):
        signal      = "overbought"
        color       = "#F09595"
        description = f"Price {diff_pct}% above VWAP — overbought. Consider taking profits."
    elif close > vwap:
        signal      = "bullish"
        color       = "#1D9E75"
        description = f"Price {diff_pct}% above VWAP — institutions are net buyers. Bullish bias."
    elif close > float(last["vwap_l1"]):
        signal      = "bearish"
        color       = "#E24B4A"
        description = f"Price {abs(diff_pct)}% below VWAP — institutions are net sellers. Bearish bias."
    else:
        signal      = "extremely_oversold"
        color       = "#1D9E75"
        description = f"Price {abs(diff_pct)}% below VWAP — extremely oversold. Bounce candidate."

    return {
        "signal":      signal,
        "color":       color,
        "vwap":        format_number(vwap),
        "diff_pct":    diff_pct,
        "above_vwap":  above,
        "description": description,
    }


# ── Supertrend ────────────────────────────────────────────────────────────────

def calculate_supertrend(
    df: pd.DataFrame,
    period: int = 10,
    multiplier: float = 3.0,
) -> pd.DataFrame:
    """
    Supertrend — ATR-based trend indicator.

    Green line below price = uptrend (BUY)
    Red line above price   = downtrend (SELL)

    Much cleaner signal than EMA for beginners —
    it's either green or red, no ambiguity.
    """
    # ATR calculation
    high_low    = df["high"] - df["low"]
    high_close  = (df["high"] - df["close"].shift()).abs()
    low_close   = (df["low"]  - df["close"].shift()).abs()
    true_range  = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
    atr         = true_range.ewm(span=period, adjust=False).mean()

    # Basic upper and lower bands
    hl2         = (df["high"] + df["low"]) / 2
    upper_band  = hl2 + (multiplier * atr)
    lower_band  = hl2 - (multiplier * atr)

    # Final bands and trend
    supertrend  = pd.Series(index=df.index, dtype=float)
    direction   = pd.Series(index=df.index, dtype=int)   # 1=up, -1=down
    final_upper = upper_band.copy()
    final_lower = lower_band.copy()

    for i in range(1, len(df)):
        # Final upper band
        if (upper_band.iloc[i] < final_upper.iloc[i - 1] or
                df["close"].iloc[i - 1] > final_upper.iloc[i - 1]):
            final_upper.iloc[i] = upper_band.iloc[i]
        else:
            final_upper.iloc[i] = final_upper.iloc[i - 1]

        # Final lower band
        if (lower_band.iloc[i] > final_lower.iloc[i - 1] or
                df["close"].iloc[i - 1] < final_lower.iloc[i - 1]):
            final_lower.iloc[i] = lower_band.iloc[i]
        else:
            final_lower.iloc[i] = final_lower.iloc[i - 1]

        # Direction and supertrend line
        prev_dir = direction.iloc[i - 1] if i > 1 else 1

        if prev_dir == -1 and df["close"].iloc[i] > final_upper.iloc[i]:
            direction.iloc[i]  = 1
        elif prev_dir == 1 and df["close"].iloc[i] < final_lower.iloc[i]:
            direction.iloc[i]  = -1
        else:
            direction.iloc[i]  = prev_dir

        supertrend.iloc[i] = (
            final_lower.iloc[i] if direction.iloc[i] == 1
            else final_upper.iloc[i]
        )

    df["supertrend"]           = supertrend.round(2)
    df["supertrend_direction"] = direction   # 1 = up (bullish), -1 = down (bearish)
    df["supertrend_upper"]     = final_upper.round(2)
    df["supertrend_lower"]     = final_lower.round(2)

    return df


def get_supertrend_signal(df: pd.DataFrame) -> dict:
    """Supertrend signal for latest candle."""
    last      = df.iloc[-1]
    prev      = df.iloc[-2] if len(df) > 1 else last
    direction = int(last["supertrend_direction"]) if pd.notna(last["supertrend_direction"]) else 0
    prev_dir  = int(prev["supertrend_direction"]) if pd.notna(prev["supertrend_direction"]) else 0

    just_flipped = direction != prev_dir

    if direction == 1:
        signal      = "BUY"
        color       = "#1D9E75"
        description = (
            ("🟢 Supertrend just flipped GREEN — fresh buy signal! " if just_flipped else "")
            + f"Price above Supertrend at ₹{format_number(last['supertrend'])}. Uptrend confirmed."
        )
    elif direction == -1:
        signal      = "SELL"
        color       = "#E24B4A"
        description = (
            ("🔴 Supertrend just flipped RED — fresh sell signal! " if just_flipped else "")
            + f"Price below Supertrend at ₹{format_number(last['supertrend'])}. Downtrend confirmed."
        )
    else:
        signal      = "NEUTRAL"
        color       = "#888780"
        description = "Supertrend direction unclear."

    return {
        "signal":       signal,
        "color":        color,
        "value":        format_number(last["supertrend"]),
        "direction":    direction,
        "just_flipped": just_flipped,
        "description":  description,
    }


# ── Bollinger Bands ───────────────────────────────────────────────────────────

def calculate_bollinger_bands(
    df: pd.DataFrame,
    period: int = 20,
    std_dev: float = 2.0,
) -> pd.DataFrame:
    """
    Bollinger Bands — volatility channels around a moving average.

    Band squeeze (bands narrowing) = volatility contraction = big move coming
    Band walk (price hugs upper/lower band) = strong trend
    Price outside bands = extreme move, likely to revert
    """
    sma    = df["close"].rolling(window=period).mean()
    std    = df["close"].rolling(window=period).std(ddof=0)

    df["bb_upper"]  = (sma + std_dev * std).round(2)
    df["bb_middle"] = sma.round(2)
    df["bb_lower"]  = (sma - std_dev * std).round(2)
    df["bb_width"]  = ((df["bb_upper"] - df["bb_lower"]) / df["bb_middle"] * 100).round(2)

    # %B — where is price within the bands (0 = lower, 1 = upper)
    band_range      = df["bb_upper"] - df["bb_lower"]
    df["bb_pct_b"]  = ((df["close"] - df["bb_lower"]) / band_range.replace(0, np.nan)).round(4)

    return df


def get_bollinger_signal(df: pd.DataFrame) -> dict:
    """Bollinger Band signal and squeeze detection."""
    last          = df.iloc[-1]
    close         = float(last["close"])
    upper         = float(last["bb_upper"]) if pd.notna(last["bb_upper"]) else 0
    lower         = float(last["bb_lower"]) if pd.notna(last["bb_lower"]) else 0
    middle        = float(last["bb_middle"]) if pd.notna(last["bb_middle"]) else 0
    width         = float(last["bb_width"])  if pd.notna(last["bb_width"])  else 0
    pct_b         = float(last["bb_pct_b"])  if pd.notna(last["bb_pct_b"])  else 0.5

    # Squeeze detection — current width vs 20-period average width
    avg_width     = df["bb_width"].rolling(20).mean().iloc[-1]
    is_squeeze    = width < float(avg_width) * 0.75 if pd.notna(avg_width) else False

    if close > upper:
        signal      = "overbought"
        color       = "#E24B4A"
        description = f"Price above upper band ₹{format_number(upper)} — overbought, expect pullback."
    elif close < lower:
        signal      = "oversold"
        color       = "#1D9E75"
        description = f"Price below lower band ₹{format_number(lower)} — oversold, bounce likely."
    elif pct_b > 0.8:
        signal      = "near_upper"
        color       = "#F09595"
        description = f"Price near upper band — bullish momentum but watch for reversal."
    elif pct_b < 0.2:
        signal      = "near_lower"
        color       = "#5DCAA5"
        description = f"Price near lower band — bearish momentum but watch for bounce."
    else:
        signal      = "neutral"
        color       = "#888780"
        description = "Price within normal Bollinger Band range."

    squeeze_msg = (
        " ⚡ SQUEEZE DETECTED — bands are contracting. Big move imminent, direction unclear."
        if is_squeeze else ""
    )

    return {
        "signal":     signal,
        "color":      color,
        "upper":      format_number(upper),
        "middle":     format_number(middle),
        "lower":      format_number(lower),
        "width":      format_number(width),
        "pct_b":      format_number(pct_b),
        "is_squeeze": is_squeeze,
        "description": description + squeeze_msg,
    }


# ── Stochastic RSI ────────────────────────────────────────────────────────────

def calculate_stoch_rsi(
    df: pd.DataFrame,
    rsi_period: int = 14,
    stoch_period: int = 14,
    k_period: int = 3,
    d_period: int = 3,
) -> pd.DataFrame:
    """
    Stochastic RSI — RSI of RSI.

    Faster and more sensitive than plain RSI.
    %K above %D with both rising from below 20 = buy signal.
    %K below %D with both falling from above 80 = sell signal.
    """
    # Calculate RSI first
    delta     = df["close"].diff()
    gain      = delta.clip(lower=0)
    loss      = (-delta).clip(lower=0)
    avg_gain  = gain.ewm(span=rsi_period, adjust=False).mean()
    avg_loss  = loss.ewm(span=rsi_period, adjust=False).mean()
    rs        = avg_gain / avg_loss.replace(0, np.nan)
    rsi       = 100 - (100 / (1 + rs))

    # Stochastic of RSI
    rsi_min   = rsi.rolling(stoch_period).min()
    rsi_max   = rsi.rolling(stoch_period).max()
    rsi_range = rsi_max - rsi_min

    stoch_rsi = (rsi - rsi_min) / rsi_range.replace(0, np.nan) * 100
    k_line    = stoch_rsi.rolling(k_period).mean()
    d_line    = k_line.rolling(d_period).mean()

    df["stoch_rsi_k"] = k_line.round(2)
    df["stoch_rsi_d"] = d_line.round(2)

    return df


def get_stoch_rsi_signal(df: pd.DataFrame) -> dict:
    """Stochastic RSI signal."""
    last       = df.iloc[-1]
    prev       = df.iloc[-2] if len(df) > 1 else last

    k          = float(last["stoch_rsi_k"]) if pd.notna(last["stoch_rsi_k"]) else 50
    d          = float(last["stoch_rsi_d"]) if pd.notna(last["stoch_rsi_d"]) else 50
    prev_k     = float(prev["stoch_rsi_k"]) if pd.notna(prev["stoch_rsi_k"]) else 50
    prev_d     = float(prev["stoch_rsi_d"]) if pd.notna(prev["stoch_rsi_d"]) else 50

    # Crossover detection
    bullish_cross = prev_k <= prev_d and k > d and k < 50
    bearish_cross = prev_k >= prev_d and k < d and k > 50

    if bullish_cross:
        signal      = "BUY"
        color       = "#1D9E75"
        description = f"%K crossed above %D at {k:.1f} — bullish crossover from oversold zone."
    elif bearish_cross:
        signal      = "SELL"
        color       = "#E24B4A"
        description = f"%K crossed below %D at {k:.1f} — bearish crossover from overbought zone."
    elif k > 80 and d > 80:
        signal      = "overbought"
        color       = "#E24B4A"
        description = f"StochRSI at {k:.1f} — overbought. Potential reversal ahead."
    elif k < 20 and d < 20:
        signal      = "oversold"
        color       = "#1D9E75"
        description = f"StochRSI at {k:.1f} — oversold. Potential bounce ahead."
    else:
        signal      = "neutral"
        color       = "#888780"
        description = f"StochRSI %K={k:.1f}, %D={d:.1f} — no clear signal."

    return {
        "signal":         signal,
        "color":          color,
        "k":              format_number(k),
        "d":              format_number(d),
        "bullish_cross":  bullish_cross,
        "bearish_cross":  bearish_cross,
        "description":    description,
    }


# ── Ichimoku Cloud ────────────────────────────────────────────────────────────

def calculate_ichimoku(df: pd.DataFrame) -> pd.DataFrame:
    """
    Ichimoku Kinko Hyo — all-in-one indicator.

    Tenkan (9):  Fast signal line
    Kijun (26):  Slow signal line / support-resistance
    Senkou A:    Leading span A (cloud boundary)
    Senkou B:    Leading span B (cloud boundary)
    Chikou:      Lagging span (current close plotted 26 periods back)

    Price above cloud = bullish
    Price inside cloud = ranging / indecision
    Price below cloud  = bearish
    """
    def midpoint(period):
        return (
            df["high"].rolling(period).max() +
            df["low"].rolling(period).min()
        ) / 2

    tenkan   = midpoint(9)
    kijun    = midpoint(26)
    senkou_a = ((tenkan + kijun) / 2).shift(26)
    senkou_b = midpoint(52).shift(26)
    chikou   = df["close"].shift(-26)

    df["ichi_tenkan"]   = tenkan.round(2)
    df["ichi_kijun"]    = kijun.round(2)
    df["ichi_senkou_a"] = senkou_a.round(2)
    df["ichi_senkou_b"] = senkou_b.round(2)
    df["ichi_chikou"]   = chikou.round(2)

    return df


def get_ichimoku_signal(df: pd.DataFrame) -> dict:
    """Ichimoku cloud signal."""
    last       = df.iloc[-1]
    close      = float(last["close"])
    senkou_a   = float(last["ichi_senkou_a"]) if pd.notna(last["ichi_senkou_a"]) else 0
    senkou_b   = float(last["ichi_senkou_b"]) if pd.notna(last["ichi_senkou_b"]) else 0
    tenkan     = float(last["ichi_tenkan"])   if pd.notna(last["ichi_tenkan"])   else 0
    kijun      = float(last["ichi_kijun"])    if pd.notna(last["ichi_kijun"])    else 0

    cloud_top  = max(senkou_a, senkou_b)
    cloud_bot  = min(senkou_a, senkou_b)
    cloud_bull = senkou_a > senkou_b  # green cloud

    if close > cloud_top:
        position    = "above_cloud"
        signal      = "bullish"
        color       = "#1D9E75"
        description = "Price above the cloud — strong bullish trend confirmed."
    elif close < cloud_bot:
        position    = "below_cloud"
        signal      = "bearish"
        color       = "#E24B4A"
        description = "Price below the cloud — strong bearish trend confirmed."
    else:
        position    = "inside_cloud"
        signal      = "neutral"
        color       = "#888780"
        description = "Price inside the cloud — ranging market, avoid trading."

    tk_cross = "bullish" if tenkan > kijun else "bearish"

    return {
        "signal":      signal,
        "color":       color,
        "position":    position,
        "cloud_color": "#1D9E75" if cloud_bull else "#E24B4A",
        "tenkan":      format_number(tenkan),
        "kijun":       format_number(kijun),
        "senkou_a":    format_number(senkou_a),
        "senkou_b":    format_number(senkou_b),
        "cloud_top":   format_number(cloud_top),
        "cloud_bottom": format_number(cloud_bot),
        "tk_cross":    tk_cross,
        "description": description,
    }


# ── Master function ───────────────────────────────────────────────────────────

def calculate_all_advanced(df: pd.DataFrame, config: dict = None) -> dict:
    """
    Calculate all advanced indicators on the DataFrame.
    Returns signals + the updated DataFrame.
    """
    cfg = config or {}

    # VWAP
    df = calculate_vwap(df)
    vwap_signal = get_vwap_signal(df)

    # Supertrend
    st_period = cfg.get("supertrend_period", 10)
    st_mult   = cfg.get("supertrend_multiplier", 3.0)
    df = calculate_supertrend(df, period=st_period, multiplier=st_mult)
    st_signal = get_supertrend_signal(df)

    # Bollinger Bands
    bb_period = cfg.get("bb_period", 20)
    bb_std    = cfg.get("bb_std",    2.0)
    df = calculate_bollinger_bands(df, period=bb_period, std_dev=bb_std)
    bb_signal = get_bollinger_signal(df)

    # Stochastic RSI
    df = calculate_stoch_rsi(df)
    srsi_signal = get_stoch_rsi_signal(df)

    # Ichimoku
    df = calculate_ichimoku(df)
    ichi_signal = get_ichimoku_signal(df)

    return {
        "df":         df,
        "vwap":       vwap_signal,
        "supertrend": st_signal,
        "bollinger":  bb_signal,
        "stoch_rsi":  srsi_signal,
        "ichimoku":   ichi_signal,
    }