# services/ml/model_trainer.py

import os
import logging
import joblib
import numpy as np
import pandas as pd
from datetime import datetime
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import TimeSeriesSplit
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    classification_report,
)

from services.ml.feature_engineer import build_features, FEATURE_COLUMNS
from services.indicator_calculator import get_indicators

logger = logging.getLogger(__name__)

# Where trained models are saved
MODEL_DIR = "models"
os.makedirs(MODEL_DIR, exist_ok=True)


def _get_model_path(symbol: str) -> str:
    """Returns the file path for a symbol's saved model."""
    safe = symbol.replace("^", "").replace("/", "_")
    return os.path.join(MODEL_DIR, f"model_{safe}.pkl")


def _get_scaler_path(symbol: str) -> str:
    """Returns the file path for a symbol's saved scaler."""
    safe = symbol.replace("^", "").replace("/", "_")
    return os.path.join(MODEL_DIR, f"scaler_{safe}.pkl")


def _get_metadata_path(symbol: str) -> str:
    safe = symbol.replace("^", "").replace("/", "_")
    return os.path.join(MODEL_DIR, f"metadata_{safe}.pkl")


def train_model(symbol: str = "^NSEI", period: str = "2y") -> dict:
    """
    Train a Random Forest model for the given symbol.

    Process:
    1. Fetch 2 years of historical data + indicators
    2. Engineer features
    3. Split into train/test using time-series split
       (NEVER use random split for time series — future leaks into past)
    4. Train RandomForestClassifier
    5. Evaluate on held-out test set
    6. Save model + scaler + metadata to disk

    Returns:
        dict with training metrics and model info
    """
    logger.info(f"Training model for {symbol} with period={period}")

    # ── Step 1: Get indicator data ────────────────────────────────────────
    indicator_data = get_indicators(
        symbol=symbol,
        period=period,
        interval="1d",
        rsi_window=14,
        ema_window=20,
        atr_window=14,
    )

    df = pd.DataFrame(indicator_data["data"])
    df["date"] = pd.to_datetime(df["date"])
    df.set_index("date", inplace=True)

    # Rename to uppercase for consistency with feature engineer
    df.rename(columns={
        "open": "open", "high": "high", "low": "low",
        "close": "close", "volume": "volume",
        "rsi": "RSI", "ema": "EMA", "atr": "ATR",
        "macd": "MACD", "macd_signal": "MACD_Signal",
        "macd_histogram": "MACD_Histogram",
    }, inplace=True)

    # ── Step 2: Feature engineering ───────────────────────────────────────
    df_features = build_features(df)

    # Separate features and target
    X = df_features[FEATURE_COLUMNS]
    y = df_features["target"]

    if len(X) < 100:
        raise ValueError(
            f"Not enough data to train. Need 100+ rows, got {len(X)}. "
            f"Use period=2y or longer."
        )

    # ── Step 3: Time-series train/test split ──────────────────────────────
    # Use last 20% of data as test set — preserves time order
    split_idx  = int(len(X) * 0.80)
    X_train    = X.iloc[:split_idx]
    X_test     = X.iloc[split_idx:]
    y_train    = y.iloc[:split_idx]
    y_test     = y.iloc[split_idx:]

    train_dates = df_features.index[:split_idx]
    test_dates  = df_features.index[split_idx:]

    logger.info(
        f"Train: {len(X_train)} rows ({train_dates[0].date()} – {train_dates[-1].date()})"
    )
    logger.info(
        f"Test:  {len(X_test)} rows ({test_dates[0].date()} – {test_dates[-1].date()})"
    )

    # ── Step 4: Scale features ────────────────────────────────────────────
    # StandardScaler: transforms each feature to mean=0, std=1
    # Fit ONLY on training data — never fit on test data (data leakage)
    scaler  = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled  = scaler.transform(X_test)

    # ── Step 5: Train Random Forest ───────────────────────────────────────
    model = RandomForestClassifier(
        n_estimators=200,       # 200 decision trees
        max_depth=8,            # prevent overfitting
        min_samples_leaf=10,    # each leaf needs 10+ samples
        max_features="sqrt",    # each tree sees sqrt(n_features)
        class_weight="balanced",# handles class imbalance
        random_state=42,        # reproducible results
        n_jobs=-1,              # use all CPU cores
    )
    model.fit(X_train_scaled, y_train)

    # ── Step 6: Evaluate ──────────────────────────────────────────────────
    y_pred      = model.predict(X_test_scaled)
    y_pred_prob = model.predict_proba(X_test_scaled)

    accuracy  = round(accuracy_score(y_test, y_pred) * 100, 2)
    precision = round(precision_score(y_test, y_pred, zero_division=0) * 100, 2)
    recall    = round(recall_score(y_test, y_pred, zero_division=0) * 100, 2)
    f1        = round(f1_score(y_test, y_pred, zero_division=0) * 100, 2)

    # Feature importance — which features matter most?
    feature_importance = dict(zip(
        FEATURE_COLUMNS,
        [round(float(v), 4) for v in model.feature_importances_]
    ))
    top_features = dict(sorted(
        feature_importance.items(),
        key=lambda x: x[1],
        reverse=True
    )[:10])

    logger.info(f"Model accuracy: {accuracy}%")
    logger.info(f"Top feature: {list(top_features.keys())[0]}")

    # ── Step 7: Save to disk ──────────────────────────────────────────────
    metadata = {
        "symbol":           symbol,
        "period":           period,
        "trained_at":       datetime.now().isoformat(),
        "train_rows":       len(X_train),
        "test_rows":        len(X_test),
        "train_start":      str(train_dates[0].date()),
        "train_end":        str(train_dates[-1].date()),
        "test_start":       str(test_dates[0].date()),
        "test_end":         str(test_dates[-1].date()),
        "feature_columns":  FEATURE_COLUMNS,
        "metrics": {
            "accuracy":  accuracy,
            "precision": precision,
            "recall":    recall,
            "f1_score":  f1,
        },
        "top_features": top_features,
        "class_distribution": {
            "buy_days":  int(y_train.sum()),
            "sell_days": int(len(y_train) - y_train.sum()),
        },
    }

    joblib.dump(model,    _get_model_path(symbol))
    joblib.dump(scaler,   _get_scaler_path(symbol))
    joblib.dump(metadata, _get_metadata_path(symbol))

    logger.info(f"Model saved to {_get_model_path(symbol)}")

    return {
        "status":   "trained",
        "symbol":   symbol,
        "metadata": metadata,
    }


def load_model(symbol: str):
    """
    Load a previously trained model from disk.
    Returns (model, scaler, metadata) tuple.
    Raises FileNotFoundError if model hasn't been trained yet.
    """
    model_path    = _get_model_path(symbol)
    scaler_path   = _get_scaler_path(symbol)
    metadata_path = _get_metadata_path(symbol)

    if not os.path.exists(model_path):
        raise FileNotFoundError(
            f"No trained model found for {symbol}. "
            f"Call POST /predict/train?symbol={symbol} first."
        )

    model    = joblib.load(model_path)
    scaler   = joblib.load(scaler_path)
    metadata = joblib.load(metadata_path)

    return model, scaler, metadata


def model_exists(symbol: str) -> bool:
    """Check if a trained model exists for this symbol."""
    return os.path.exists(_get_model_path(symbol))