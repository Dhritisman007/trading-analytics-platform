# services/ml/feature_engineer.py

import pandas as pd
import numpy as np
import logging

logger = logging.getLogger(__name__)

# Feature columns used by the ML model (29 total)
FEATURE_COLUMNS = [
    # Normalized Indicators
    "rsi_norm",               # RSI normalized to 0-1
    "macd_hist_norm",         # MACD histogram normalized
    "atr_pct",                # ATR as % of price
    
    # Price Action
    "price_ema_ratio",        # (Price - EMA) / EMA (%)
    "return_1d",              # 1-day log return
    "return_5d",              # 5-day log return
    "return_20d",             # 20-day log return
    "volume_ratio",           # Volume / 20-day MA volume
    
    # Binary Flags
    "rsi_overbought",         # RSI > 70
    "rsi_oversold",           # RSI < 30
    "above_ema",              # Close > EMA
    "macd_positive",          # MACD > MACD_Signal
    "macd_crossover",         # MACD just crossed signal
    
    # Volatility
    "volatility_20d",         # 20-day price volatility
    "high_low_ratio",         # (High - Low) / Close
    
    # Momentum
    "rsi_slope",              # RSI trend (steepness)
    "macd_slope",             # MACD trend
    
    # Trend
    "consecutive_up",         # Count of consecutive up days
    "consecutive_down",       # Count of consecutive down days
    
    # VWAP & Price Position
    "distance_from_vwap",     # Price distance from VWAP
    
    # EMA Trend
    "ema_slope_20d",          # 20-day EMA slope
    
    # Multi-timeframe
    "close_above_200ma",      # Price > 200-day MA
    "volume_spike",           # Today's volume > 1.5x avg
    
    # RSI Divergence (simplified)
    "rsi_divergence",         # Price higher but RSI lower
    
    # Additional Features
    "macd_histogram_slope",   # MACD histogram trend
    "atr_ratio",              # Current ATR / 20-day MA ATR
    "true_range_norm",        # True range normalized
    "price_momentum",         # Price momentum (close vs 5-day MA)
    "volume_momentum",        # Volume momentum indicator
]


def build_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Engineer features from OHLCV + indicator data.
    
    Input DataFrame should have columns:
    - open, high, low, close, volume
    - RSI, EMA, ATR, MACD, MACD_Signal, MACD_Histogram
    
    Output includes all FEATURE_COLUMNS plus a 'target' column (BUY=1, SELL=0).
    """
    df = df.copy()
    
    # ── Ensure required columns exist ──────────────────────────────────────
    required = ["close", "high", "low", "volume", "RSI", "EMA", "ATR", "MACD", "MACD_Signal", "MACD_Histogram"]
    for col in required:
        if col not in df.columns:
            raise ValueError(f"Missing required column: {col}")
    
    # ── Normalized Indicators ──────────────────────────────────────────────
    df["rsi_norm"] = df["RSI"] / 100.0  # Normalize RSI to 0-1
    df["macd_hist_norm"] = np.where(
        df["MACD_Histogram"] != 0,
        df["MACD_Histogram"] / df["MACD_Histogram"].abs().max(),
        0
    ).clip(-1, 1)  # Normalize to -1 to 1
    df["atr_pct"] = (df["ATR"] / df["close"]) * 100  # ATR as % of price
    
    # ── Price Action ───────────────────────────────────────────────────────
    df["price_ema_ratio"] = ((df["close"] - df["EMA"]) / df["EMA"]) * 100  # %
    df["return_1d"] = np.log(df["close"] / df["close"].shift(1))
    df["return_5d"] = np.log(df["close"] / df["close"].shift(5))
    df["return_20d"] = np.log(df["close"] / df["close"].shift(20))
    
    # Volume ratio
    volume_ma = df["volume"].rolling(20).mean()
    df["volume_ratio"] = np.where(volume_ma > 0, df["volume"] / volume_ma, 1)
    
    # ── Binary Flags ───────────────────────────────────────────────────────
    df["rsi_overbought"] = (df["RSI"] > 70).astype(int)
    df["rsi_oversold"] = (df["RSI"] < 30).astype(int)
    df["above_ema"] = (df["close"] > df["EMA"]).astype(int)
    df["macd_positive"] = (df["MACD"] > df["MACD_Signal"]).astype(int)
    
    # MACD crossover (MACD crosses above signal line)
    macd_prev = df["MACD"].shift(1)
    signal_prev = df["MACD_Signal"].shift(1)
    df["macd_crossover"] = (
        ((macd_prev <= signal_prev) & (df["MACD"] > df["MACD_Signal"])).astype(int)
    )
    
    # ── Volatility ─────────────────────────────────────────────────────────
    df["volatility_20d"] = df["close"].pct_change().rolling(20).std()
    df["high_low_ratio"] = ((df["high"] - df["low"]) / df["close"]) * 100
    
    # ── Momentum ───────────────────────────────────────────────────────────
    df["rsi_slope"] = df["RSI"].rolling(5).apply(lambda x: (x.iloc[-1] - x.iloc[0]) / 5 if len(x) > 1 else 0, raw=False)
    df["macd_slope"] = df["MACD"].rolling(5).apply(lambda x: (x.iloc[-1] - x.iloc[0]) / 5 if len(x) > 1 else 0, raw=False)
    
    # ── Trend (consecutive up/down) ────────────────────────────────────────
    returns = df["close"].pct_change()
    df["consecutive_up"] = (returns > 0).astype(int).groupby((returns <= 0).cumsum()).cumsum()
    df["consecutive_down"] = (returns <= 0).astype(int).groupby((returns > 0).cumsum()).cumsum()
    
    # ── VWAP & Price Position ──────────────────────────────────────────────
    typical_price = (df["high"] + df["low"] + df["close"]) / 3
    cumulative_vp = (typical_price * df["volume"]).rolling(20).sum()
    cumulative_volume = df["volume"].rolling(20).sum()
    vwap = cumulative_vp / cumulative_volume
    df["distance_from_vwap"] = ((df["close"] - vwap) / vwap) * 100 if len(vwap) > 0 else 0
    
    # ── EMA Trend ──────────────────────────────────────────────────────────
    df["ema_slope_20d"] = df["EMA"].rolling(20).apply(lambda x: (x.iloc[-1] - x.iloc[0]) / 20 if len(x) > 1 else 0, raw=False)
    
    # ── Multi-timeframe ────────────────────────────────────────────────────
    ma_200 = df["close"].rolling(200).mean()
    df["close_above_200ma"] = (df["close"] > ma_200).astype(int)
    volume_ma_1d = df["volume"].rolling(1).mean()
    df["volume_spike"] = ((df["volume"] / volume_ma_1d) > 1.5).astype(int)
    
    # ── RSI Divergence ─────────────────────────────────────────────────────
    price_up = df["close"] > df["close"].shift(1)
    rsi_down = df["RSI"] < df["RSI"].shift(1)
    df["rsi_divergence"] = (price_up & rsi_down).astype(int)
    
    # ── MACD Histogram Slope ───────────────────────────────────────────────
    df["macd_histogram_slope"] = df["MACD_Histogram"].rolling(5).apply(
        lambda x: (x.iloc[-1] - x.iloc[0]) / 5 if len(x) > 1 else 0, raw=False
    )
    
    # ── ATR Ratio ──────────────────────────────────────────────────────────
    atr_ma = df["ATR"].rolling(20).mean()
    df["atr_ratio"] = np.where(atr_ma > 0, df["ATR"] / atr_ma, 1)
    
    # ── True Range Normalized ──────────────────────────────────────────────
    high_low = df["high"] - df["low"]
    high_close = (df["high"] - df["close"].shift(1)).abs()
    low_close = (df["low"] - df["close"].shift(1)).abs()
    tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
    df["true_range_norm"] = (tr / df["close"]) * 100
    
    # ── Price Momentum ─────────────────────────────────────────────────────
    price_ma_5 = df["close"].rolling(5).mean()
    df["price_momentum"] = ((df["close"] - price_ma_5) / price_ma_5 * 100) if len(price_ma_5) > 0 else 0
    
    # ── Volume Momentum ────────────────────────────────────────────────────
    volume_ma_5 = df["volume"].rolling(5).mean()
    df["volume_momentum"] = np.where(volume_ma_5 > 0, (df["volume"] - volume_ma_5) / volume_ma_5, 0)
    
    # ── Target: BUY if next day's close is higher, SELL otherwise ─────────
    df["target"] = (df["close"].shift(-1) > df["close"]).astype(int)
    
    # ── Clean up: Drop NaN rows (caused by rolling windows) ────────────────
    df = df.dropna(subset=FEATURE_COLUMNS + ["target"])
    
    return df
