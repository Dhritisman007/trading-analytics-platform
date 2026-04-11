# services/ml/predictor.py

import pandas as pd
import numpy as np
import logging

from services.ml.feature_engineer import build_features, FEATURE_COLUMNS
from services.ml.model_trainer import load_model, train_model, model_exists
from services.indicator_calculator import get_indicators
from utils.formatters import format_number

logger = logging.getLogger(__name__)


def _explain_prediction(
    signal: str,
    confidence: float,
    top_features: dict,
    latest_row: pd.Series,
) -> str:
    """
    Generate a plain-English explanation of why the model made this prediction.
    This powers the beginner-friendly tooltip on the dashboard.
    """
    reasons = []
    top = list(top_features.keys())[:3]  # top 3 most important features

    for feature in top:
        value = latest_row.get(feature, 0)

        if feature == "rsi_norm":
            rsi = value * 100
            if rsi > 65:
                reasons.append(f"RSI is high at {rsi:.0f}, suggesting overbought conditions")
            elif rsi < 35:
                reasons.append(f"RSI is low at {rsi:.0f}, suggesting oversold conditions")
            else:
                reasons.append(f"RSI is neutral at {rsi:.0f}")

        elif feature == "price_ema_ratio":
            pct = value
            if pct > 0:
                reasons.append(f"Price is {abs(pct):.1f}% above the EMA trend line")
            else:
                reasons.append(f"Price is {abs(pct):.1f}% below the EMA trend line")

        elif feature == "macd_hist_norm":
            if value > 0:
                reasons.append("MACD histogram is positive — bullish momentum")
            else:
                reasons.append("MACD histogram is negative — bearish momentum")

        elif feature == "return_1d":
            pct = value * 100
            if pct > 0:
                reasons.append(f"Today's price moved up {pct:.1f}%")
            else:
                reasons.append(f"Today's price moved down {abs(pct):.1f}%")

        elif feature == "macd_crossover":
            if value == 1:
                reasons.append("MACD just crossed above signal line — bullish crossover")

        elif feature == "above_ema":
            if value == 1:
                reasons.append("Price is currently above the EMA — uptrend")
            else:
                reasons.append("Price is currently below the EMA — downtrend")

        elif feature == "atr_pct":
            reasons.append(f"Market volatility (ATR) is at {value:.2f}% of price")

    if not reasons:
        reasons.append("Multiple technical indicators align with this prediction")

    return ". ".join(reasons[:2]) + "."


def predict(
    symbol: str = "^NSEI",
    period: str = "1y",
    auto_train: bool = True,
) -> dict:
    """
    Generate a buy/sell prediction for the given symbol.

    Process:
    1. Check if a trained model exists — if not, train one automatically
    2. Fetch latest indicator data
    3. Engineer features from latest data
    4. Run model prediction on the most recent row
    5. Return signal, confidence, and plain-English explanation

    Args:
        symbol:     ticker symbol
        period:     how much data to use for feature context
        auto_train: if True, trains automatically if no model exists

    Returns:
        dict with signal, confidence, explanation, and model metadata
    """
    # ── Step 1: Ensure model exists ───────────────────────────────────────
    if not model_exists(symbol):
        if auto_train:
            logger.info(f"No model for {symbol} — training automatically...")
            train_model(symbol=symbol, period="2y")
        else:
            raise FileNotFoundError(
                f"No trained model for {symbol}. "
                f"Use auto_train=true or POST /predict/train"
            )

    model, scaler, metadata = load_model(symbol)

    # ── Step 2: Get latest indicator data ─────────────────────────────────
    indicator_data = get_indicators(
        symbol=symbol,
        period=period,
        interval="1d",
    )

    df = pd.DataFrame(indicator_data["data"])
    df["date"] = pd.to_datetime(df["date"])
    df.set_index("date", inplace=True)

    df.rename(columns={
        "open": "open", "high": "high", "low": "low",
        "close": "close", "volume": "volume",
        "rsi": "RSI", "ema": "EMA", "atr": "ATR",
        "macd": "MACD", "macd_signal": "MACD_Signal",
        "macd_histogram": "MACD_Histogram",
    }, inplace=True)

    # ── Step 3: Engineer features ─────────────────────────────────────────
    df_features = build_features(df)

    if df_features.empty:
        raise ValueError("Not enough data to generate features for prediction.")

    # Use only the most recent row for prediction
    latest = df_features.iloc[-1]
    X_latest = latest[FEATURE_COLUMNS].values.reshape(1, -1)

    # ── Step 4: Predict ───────────────────────────────────────────────────
    X_scaled    = scaler.transform(X_latest)
    prediction  = model.predict(X_scaled)[0]
    probability = model.predict_proba(X_scaled)[0]

    signal     = "BUY"  if prediction == 1 else "SELL"
    confidence = round(float(max(probability)) * 100, 1)
    buy_prob   = round(float(probability[1]) * 100, 1)
    sell_prob  = round(float(probability[0]) * 100, 1)

    # Feature importance from the trained model
    feature_importance = dict(zip(
        FEATURE_COLUMNS,
        [round(float(v), 4) for v in model.feature_importances_]
    ))
    top_features = dict(sorted(
        feature_importance.items(),
        key=lambda x: x[1], reverse=True
    )[:5])

    # ── Step 5: Build explanation ─────────────────────────────────────────
    explanation = _explain_prediction(signal, confidence, top_features, latest)

    # Current market snapshot for context
    latest_close = format_number(indicator_data["data"][-1]["close"])
    latest_rsi   = format_number(indicator_data["data"][-1]["rsi"])

    return {
        "symbol":       symbol,
        "name":         indicator_data["name"],
        "signal":       signal,
        "confidence":   confidence,
        "probabilities": {
            "buy":  buy_prob,
            "sell": sell_prob,
        },
        "explanation":    explanation,
        "top_features":   top_features,
        "market_context": {
            "latest_close": latest_close,
            "rsi":          latest_rsi,
            "rsi_signal":   indicator_data["latest"]["rsi_signal"],
            "price_vs_ema": indicator_data["latest"]["price_vs_ema"],
            "macd_crossover": indicator_data["latest"]["macd_crossover"],
        },
        "model_info": {
            "trained_at":  metadata["trained_at"],
            "accuracy":    metadata["metrics"]["accuracy"],
            "train_rows":  metadata["train_rows"],
            "train_period": f"{metadata['train_start']} to {metadata['train_end']}",
        },
        "disclaimer": (
            "This prediction is for educational purposes only. "
            "Past indicator patterns do not guarantee future price movements. "
            "Never make trading decisions based solely on ML predictions."
        ),
    }