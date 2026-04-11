# services/ml/performance_tracker.py

import os
import json
import logging
from datetime import datetime, timezone
from utils.formatters import format_number

logger = logging.getLogger(__name__)

PERFORMANCE_FILE = "models/prediction_history.json"


def _load_history() -> list:
    """Load prediction history from disk."""
    if not os.path.exists(PERFORMANCE_FILE):
        return []
    with open(PERFORMANCE_FILE, "r") as f:
        return json.load(f)


def _save_history(history: list) -> None:
    """Save prediction history to disk."""
    os.makedirs("models", exist_ok=True)
    with open(PERFORMANCE_FILE, "w") as f:
        json.dump(history, f, indent=2)


def record_prediction(
    symbol: str,
    signal: str,
    confidence: float,
    price_at_prediction: float,
) -> None:
    """
    Record a prediction so we can evaluate it later.
    Called every time /predict is hit.
    """
    history = _load_history()
    history.append({
        "id":                   len(history) + 1,
        "symbol":               symbol,
        "signal":               signal,
        "confidence":           confidence,
        "price_at_prediction":  price_at_prediction,
        "predicted_at":         datetime.now(timezone.utc).isoformat(),
        "outcome":              None,  # filled in later by check_outcomes()
        "outcome_price":        None,
        "correct":              None,
    })
    _save_history(history)
    logger.debug(f"Recorded prediction: {signal} for {symbol} at {price_at_prediction}")


def check_outcomes(symbol: str, current_price: float) -> dict:
    """
    Look at past predictions and mark them as correct/incorrect
    based on whether price went up or down since the prediction.

    Call this periodically to track real-world accuracy.
    """
    history   = _load_history()
    updated   = 0
    correct   = 0
    incorrect = 0

    for record in history:
        if record["symbol"] != symbol:
            continue
        if record["outcome"] is not None:
            # Already evaluated
            if record["correct"]:
                correct += 1
            else:
                incorrect += 1
            continue

        # Evaluate: did price go in the predicted direction?
        pred_price = record["price_at_prediction"]
        if pred_price and current_price:
            price_went_up = current_price > pred_price

            if record["signal"] == "BUY" and price_went_up:
                record["correct"] = True
            elif record["signal"] == "SELL" and not price_went_up:
                record["correct"] = True
            else:
                record["correct"] = False

            record["outcome"]       = "up" if price_went_up else "down"
            record["outcome_price"] = current_price
            updated += 1

            if record["correct"]:
                correct += 1
            else:
                incorrect += 1

    if updated:
        _save_history(history)

    total    = correct + incorrect
    accuracy = format_number(correct / total * 100) if total > 0 else None

    return {
        "symbol":    symbol,
        "evaluated": total,
        "correct":   correct,
        "incorrect": incorrect,
        "real_world_accuracy": accuracy,
        "updated_this_call":   updated,
    }


def get_performance_summary(symbol: str | None = None) -> dict:
    """
    Get a summary of prediction performance.
    Shows real-world accuracy vs model's training accuracy.
    """
    history = _load_history()

    if symbol:
        history = [h for h in history if h["symbol"] == symbol]

    total      = len(history)
    evaluated  = [h for h in history if h["outcome"] is not None]
    correct    = [h for h in evaluated if h.get("correct")]
    pending    = [h for h in history  if h["outcome"] is None]

    # Accuracy by confidence band — do high-confidence predictions do better?
    high_conf   = [h for h in evaluated if h.get("confidence", 0) >= 65]
    high_correct = [h for h in high_conf if h.get("correct")]

    return {
        "symbol":         symbol or "all",
        "total_predictions": total,
        "evaluated":      len(evaluated),
        "pending":        len(pending),
        "correct":        len(correct),
        "incorrect":      len(evaluated) - len(correct),
        "real_accuracy":  format_number(
            len(correct) / len(evaluated) * 100
        ) if evaluated else None,
        "high_confidence_accuracy": format_number(
            len(high_correct) / len(high_conf) * 100
        ) if high_conf else None,
        "recent_predictions": [
            {
                "signal":     h["signal"],
                "confidence": h["confidence"],
                "correct":    h["correct"],
                "predicted_at": h["predicted_at"],
            }
            for h in history[-5:]  # last 5
        ],
    }