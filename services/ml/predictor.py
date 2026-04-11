# services/ml/predictor.py

import pandas as pd
import logging

from services.ml.feature_engineer import build_features, FEATURE_COLUMNS
from services.ml.model_trainer import load_model, train_model, model_exists
from services.ml.explainer import (
    compute_feature_contributions,
    get_category_summary,
    build_chart_data,
    generate_beginner_explanation,
)
from services.ml.performance_tracker import record_prediction
from services.indicator_calculator import get_indicators
from utils.formatters import format_number

logger = logging.getLogger(__name__)


def predict(
    symbol: str = "^NSEI",
    period: str = "1y",
    auto_train: bool = True,
    top_n_features: int = 10,
) -> dict:
    """
    Generate a buy/sell prediction with full explainability.

    Returns:
        - signal and confidence
        - feature contributions (SHAP-style)
        - category breakdown (RSI vs EMA vs MACD etc.)
        - chart-ready arrays for React
        - three levels of explanation (one_line, simple, technical)
        - market context (current RSI, EMA position, MACD)
        - model performance info
    """
    # ── Step 1: Ensure model exists ───────────────────────────────────────
    if not model_exists(symbol):
        if auto_train:
            logger.info(f"No model for {symbol} — training automatically...")
            train_model(symbol=symbol, period="2y")
        else:
            raise FileNotFoundError(
                f"No trained model for {symbol}. "
                f"Call POST /predict/train?symbol={symbol} first."
            )

    model, scaler, metadata = load_model(symbol)

    # ── Step 2: Fetch latest indicators ───────────────────────────────────
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

    # ── Step 3: Feature engineering ───────────────────────────────────────
    df_features = build_features(df)

    if df_features.empty:
        raise ValueError("Not enough data to generate prediction features.")

    latest   = df_features.iloc[-1]
    X_latest = latest[FEATURE_COLUMNS].values.reshape(1, -1)

    # ── Step 4: Predict ───────────────────────────────────────────────────
    X_scaled     = scaler.transform(X_latest)
    prediction   = model.predict(X_scaled)[0]
    probability  = model.predict_proba(X_scaled)[0]

    signal      = "BUY"  if prediction == 1 else "SELL"
    confidence  = round(float(max(probability)) * 100, 1)
    buy_prob    = round(float(probability[1]) * 100, 1)
    sell_prob   = round(float(probability[0]) * 100, 1)

    # ── Step 5: Explainability ────────────────────────────────────────────
    contributions    = compute_feature_contributions(model, scaler, latest, signal)
    category_summary = get_category_summary(contributions)
    chart_data       = build_chart_data(contributions, top_n=top_n_features)
    explanation      = generate_beginner_explanation(
        contributions, signal, confidence, category_summary
    )

    # ── Step 6: Record for performance tracking ───────────────────────────
    latest_close = format_number(indicator_data["data"][-1]["close"])
    try:
        record_prediction(
            symbol=symbol,
            signal=signal,
            confidence=confidence,
            price_at_prediction=latest_close,
        )
    except Exception as e:
        logger.warning(f"Failed to record prediction: {e}")

    # ── Step 7: Signal strength badge ─────────────────────────────────────
    # Used by dashboard to colour-code the prediction card
    if confidence >= 70:
        strength = "strong"
        color    = "#1D9E75" if signal == "BUY" else "#E24B4A"
    elif confidence >= 60:
        strength = "moderate"
        color    = "#5DCAA5" if signal == "BUY" else "#F09595"
    else:
        strength = "weak"
        color    = "#B4B2A9"

    return {
        "symbol":    symbol,
        "name":      indicator_data["name"],

        # Core prediction
        "signal":    signal,
        "confidence": confidence,
        "strength":  strength,
        "color":     color,
        "probabilities": {"buy": buy_prob, "sell": sell_prob},

        # Explainability
        "explanation":       explanation,
        "contributions":     contributions[:top_n_features],
        "category_summary":  category_summary,
        "chart_data":        chart_data,

        # Market context for dashboard header
        "market_context": {
            "latest_close":   latest_close,
            "rsi":            format_number(indicator_data["data"][-1]["rsi"]),
            "rsi_signal":     indicator_data["latest"]["rsi_signal"],
            "price_vs_ema":   indicator_data["latest"]["price_vs_ema"],
            "macd_crossover": indicator_data["latest"]["macd_crossover"],
            "atr_pct":        format_number(
                indicator_data["data"][-1]["atr"] /
                indicator_data["data"][-1]["close"] * 100
            ),
        },

        # Model metadata
        "model_info": {
            "trained_at":    metadata["trained_at"],
            "accuracy":      metadata["metrics"]["accuracy"],
            "precision":     metadata["metrics"]["precision"],
            "recall":        metadata["metrics"]["recall"],
            "f1_score":      metadata["metrics"]["f1_score"],
            "train_rows":    metadata["train_rows"],
            "train_period":  f"{metadata['train_start']} → {metadata['train_end']}",
            "top_features":  metadata["top_features"],
        },

        "disclaimer": (
            "This prediction is for educational purposes only. "
            "Past indicator patterns do not guarantee future price movements. "
            "Never make trading decisions based solely on ML predictions."
        ),
    }