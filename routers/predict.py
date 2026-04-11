# routers/predict.py

from fastapi import APIRouter, HTTPException, Query, BackgroundTasks
from services.ml.model_trainer import train_model, model_exists, load_model
from services.ml.predictor import predict
from services.ml.performance_tracker import (
    check_outcomes,
    get_performance_summary,
)

router = APIRouter(prefix="/predict", tags=["ML Predictions"])

SUPPORTED_SYMBOLS = ["^NSEI", "^BSESN", "^NSEBANK"]


@router.get("/")
def get_prediction(
    symbol: str = Query(
        default="^NSEI",
        description="^NSEI for Nifty 50, ^BSESN for Sensex"
    ),
    auto_train: bool = Query(
        default=True,
        description="Auto-train if no model exists (~10 seconds first time)"
    ),
    top_n: int = Query(
        default=10,
        ge=3, le=29,
        description="How many top features to include in explanation"
    ),
):
    """
    Get a buy/sell prediction with full explainability.
    First call trains the model automatically (~10s).
    Subsequent calls return in ~200ms from the saved model.
    """
    try:
        return predict(
            symbol=symbol,
            auto_train=auto_train,
            top_n_features=top_n,
        )
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Prediction failed: {str(e)}")


@router.post("/train")
def trigger_training(
    background_tasks: BackgroundTasks,
    symbol: str = Query(default="^NSEI"),
    period: str = Query(
        default="2y",
        description="Training period. More = better. Use 2y minimum."
    ),
):
    """Trigger model training in background. Returns immediately."""
    background_tasks.add_task(train_model, symbol=symbol, period=period)
    return {
        "status":  "training_started",
        "symbol":  symbol,
        "period":  period,
        "message": f"Training started. Call GET /predict/status?symbol={symbol} to check.",
    }


@router.post("/train/all")
def train_all_models(background_tasks: BackgroundTasks):
    """Train models for all supported symbols in the background."""
    for sym in SUPPORTED_SYMBOLS:
        background_tasks.add_task(train_model, symbol=sym, period="2y")
    return {
        "status":  "training_started",
        "symbols": SUPPORTED_SYMBOLS,
        "message": "Training all models in background. Takes ~30 seconds total.",
    }


@router.get("/status")
def model_status(
    symbol: str = Query(default="^NSEI"),
):
    """Check if a model is trained and see its metrics."""
    if not model_exists(symbol):
        return {
            "symbol":  symbol,
            "trained": False,
            "message": f"No model. Call POST /predict/train?symbol={symbol}",
        }
    _, _, metadata = load_model(symbol)
    return {"symbol": symbol, "trained": True, "metadata": metadata}


@router.get("/performance")
def prediction_performance(
    symbol: str = Query(default="^NSEI"),
):
    """
    Shows real-world prediction accuracy vs model training accuracy.
    Compares what the model predicted against what actually happened.
    """
    return get_performance_summary(symbol=symbol)


@router.post("/performance/update")
def update_outcomes(
    symbol: str = Query(default="^NSEI"),
    current_price: float = Query(..., description="Current market price to evaluate past predictions"),
):
    """
    Evaluate past predictions against current price.
    Call this periodically to track real-world accuracy.
    """
    return check_outcomes(symbol=symbol, current_price=current_price)


@router.get("/compare")
def compare_symbols():
    """
    Get predictions for all supported symbols side by side.
    Powers the multi-symbol comparison panel in the dashboard.
    """
    results = []
    for sym in SUPPORTED_SYMBOLS:
        try:
            result = predict(symbol=sym, auto_train=True)
            results.append({
                "symbol":     result["symbol"],
                "name":       result["name"],
                "signal":     result["signal"],
                "confidence": result["confidence"],
                "strength":   result["strength"],
                "color":      result["color"],
                "rsi":        result["market_context"]["rsi"],
                "rsi_signal": result["market_context"]["rsi_signal"],
                "top_reason": result["explanation"]["one_line"],
            })
        except Exception as e:
            results.append({
                "symbol": sym,
                "error":  str(e),
            })

    return {
        "symbols":   results,
        "generated": __import__("datetime").datetime.now().isoformat(),
    }