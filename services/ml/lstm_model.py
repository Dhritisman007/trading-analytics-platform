# services/ml/lstm_model.py

import numpy as np
import pandas as pd
import logging
import os
import joblib
from datetime import datetime, timezone
from utils.formatters import format_number

logger = logging.getLogger(__name__)

MODELS_DIR     = "models"
LSTM_MODEL_PATH = os.path.join(MODELS_DIR, "lstm_{symbol}.keras")
SCALER_PATH    = os.path.join(MODELS_DIR, "lstm_scaler_{symbol}.pkl")

SEQUENCE_LENGTH = 30    # use last 30 days to predict next day
FEATURES = [
    "close", "high", "low", "volume",
    "rsi", "ema_20", "macd", "macd_signal",
    "atr", "bb_upper", "bb_lower", "bb_width",
]


def _build_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Engineer all features needed for LSTM input.
    Uses the `ta` library for clean indicator calculation.
    """
    import ta

    # Price-based
    df["ema_20"]      = ta.trend.ema_indicator(df["close"], window=20)
    df["rsi"]         = ta.momentum.rsi(df["close"], window=14)
    df["macd"]        = ta.trend.macd(df["close"])
    df["macd_signal"] = ta.trend.macd_signal(df["close"])
    df["atr"]         = ta.volatility.average_true_range(
                            df["high"], df["low"], df["close"], window=14)
    df["bb_upper"]    = ta.volatility.bollinger_hband(df["close"], window=20)
    df["bb_lower"]    = ta.volatility.bollinger_lband(df["close"], window=20)
    df["bb_width"]    = df["bb_upper"] - df["bb_lower"]

    return df.dropna()


def _create_sequences(data: np.ndarray, seq_len: int):
    """Convert flat feature array into (X, y) sequences for LSTM."""
    X, y = [], []
    for i in range(seq_len, len(data)):
        X.append(data[i - seq_len:i])
        # Target: 1 if next close > current close, else 0
        y.append(1 if data[i, 0] > data[i - 1, 0] else 0)
    return np.array(X), np.array(y)


def train_lstm(
    df: pd.DataFrame,
    symbol: str,
    epochs: int = 50,
    batch_size: int = 32,
) -> dict:
    """
    Train an LSTM model on historical price + indicator data.

    Architecture:
    - Input: (30 timesteps, 12 features)
    - LSTM(64) + Dropout(0.2)
    - LSTM(32) + Dropout(0.2)
    - Dense(16, relu)
    - Dense(1, sigmoid)  ← probability of price going up
    """
    try:
        import tensorflow as tf
        from tensorflow import keras
        from sklearn.preprocessing import MinMaxScaler
        from sklearn.model_selection import TimeSeriesSplit
    except ImportError:
        raise ImportError(
            "TensorFlow not installed. Run: pip install tensorflow"
        )

    logger.info(f"Training LSTM for {symbol} on {len(df)} candles")

    df_feat = _build_features(df.copy())

    # Only use available features
    available = [f for f in FEATURES if f in df_feat.columns]
    feature_data = df_feat[available].values

    # Scale features to [0, 1]
    scaler = MinMaxScaler(feature_range=(0, 1))
    scaled = scaler.fit_transform(feature_data)

    # Create sequences
    X, y = _create_sequences(scaled, SEQUENCE_LENGTH)
    if len(X) < 100:
        raise ValueError(f"Not enough data to train LSTM. Need 100+ rows, got {len(X)}")

    # Time-series split — never use future data for validation
    split       = int(len(X) * 0.8)
    X_train, X_val = X[:split], X[split:]
    y_train, y_val = y[:split], y[split:]

    # Build model
    model = keras.Sequential([
        keras.layers.Input(shape=(SEQUENCE_LENGTH, len(available))),
        keras.layers.LSTM(64, return_sequences=True),
        keras.layers.Dropout(0.2),
        keras.layers.LSTM(32, return_sequences=False),
        keras.layers.Dropout(0.2),
        keras.layers.Dense(16, activation="relu"),
        keras.layers.Dense(1,  activation="sigmoid"),
    ])

    model.compile(
        optimizer=keras.optimizers.Adam(learning_rate=0.001),
        loss="binary_crossentropy",
        metrics=["accuracy"],
    )

    # Callbacks
    callbacks = [
        keras.callbacks.EarlyStopping(
            patience=8,
            restore_best_weights=True,
            monitor="val_accuracy",
        ),
        keras.callbacks.ReduceLROnPlateau(
            patience=4,
            factor=0.5,
            min_lr=1e-6,
        ),
    ]

    # Train
    history = model.fit(
        X_train, y_train,
        validation_data=(X_val, y_val),
        epochs=epochs,
        batch_size=batch_size,
        callbacks=callbacks,
        verbose=0,
    )

    # Evaluate
    val_loss, val_acc = model.evaluate(X_val, y_val, verbose=0)
    accuracy          = round(float(val_acc) * 100, 2)

    logger.info(f"LSTM training complete. Accuracy: {accuracy}%")

    # Save model and scaler
    os.makedirs(MODELS_DIR, exist_ok=True)
    model_path  = LSTM_MODEL_PATH.format(symbol=symbol.replace("^", ""))
    scaler_path = SCALER_PATH.format(symbol=symbol.replace("^", ""))
    model.save(model_path)
    joblib.dump(scaler, scaler_path)

    return {
        "accuracy":    accuracy,
        "epochs_run":  len(history.history["loss"]),
        "val_loss":    round(float(val_loss), 4),
        "model_path":  model_path,
        "trained_at":  datetime.now(timezone.utc).isoformat(),
        "train_rows":  len(X_train),
        "val_rows":    len(X_val),
        "features":    available,
    }


def predict_lstm(df: pd.DataFrame, symbol: str) -> dict:
    """
    Make a prediction using the trained LSTM model.
    Returns probability of price going up tomorrow.
    """
    try:
        import tensorflow as tf
        from tensorflow import keras
    except ImportError:
        raise ImportError("TensorFlow not installed")

    model_path  = LSTM_MODEL_PATH.format(symbol=symbol.replace("^", ""))
    scaler_path = SCALER_PATH.format(symbol=symbol.replace("^", ""))

    if not os.path.exists(model_path):
        raise FileNotFoundError(
            f"LSTM model not found for {symbol}. Train it first."
        )

    model  = keras.models.load_model(model_path)
    scaler = joblib.load(scaler_path)

    df_feat = _build_features(df.copy())
    available = [f for f in FEATURES if f in df_feat.columns]

    if len(df_feat) < SEQUENCE_LENGTH:
        raise ValueError(f"Need at least {SEQUENCE_LENGTH} candles")

    # Use last SEQUENCE_LENGTH rows
    last_sequence = df_feat[available].values[-SEQUENCE_LENGTH:]
    scaled        = scaler.transform(last_sequence)
    X             = scaled.reshape(1, SEQUENCE_LENGTH, len(available))

    # Predict
    prob_up      = float(model.predict(X, verbose=0)[0][0])
    prob_down    = 1 - prob_up
    confidence   = round(max(prob_up, prob_down) * 100, 2)
    signal       = "BUY" if prob_up > 0.5 else "SELL"

    strength = (
        "strong"   if confidence >= 70 else
        "moderate" if confidence >= 55 else
        "weak"
    )

    return {
        "signal":       signal,
        "confidence":   confidence,
        "prob_up":      round(prob_up   * 100, 2),
        "prob_down":    round(prob_down * 100, 2),
        "strength":     strength,
        "model_type":   "LSTM",
        "features_used": len(available),
        "description":  (
            f"LSTM predicts {confidence}% probability of price moving "
            f"{'up' if signal == 'BUY' else 'down'} tomorrow. "
            f"Based on {SEQUENCE_LENGTH}-day sequence of {len(available)} indicators."
        ),
    }