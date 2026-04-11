# routers/predict.py

from fastapi import APIRouter, HTTPException, Query, BackgroundTasks
from services.ml.model_trainer import train_model, model_exists, load_model
from services.ml.predictor import predict

router = APIRouter(prefix="/predict", tags=["ML Predictions"])


@router.get("/")
def get_prediction(
    symbol: str = Query(
        default="^NSEI",
        description="^NSEI for Nifty 50, ^BSESN for Sensex"
    ),
    auto_train: bool = Query(
        default=True,
        description="Auto-train model if none exists (takes ~10 seconds first time)"
    ),
):
    """
    Get a buy/sell prediction for the given symbol.

    First call will auto-train the model (~10 seconds).
    Subsequent calls use the saved model (~200ms).

    Returns signal (BUY/SELL), confidence %, plain-English explanation,
    and the top features that drove the prediction.
    """
    try:
        return predict(symbol=symbol, auto_train=auto_train)
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
        description="Training data period. More data = better model. Use 2y or more."
    ),
):
    """
    Manually trigger model training in the background.
    Returns immediately — training happens asynchronously.
    Check /predict/status to see when it's done.
    """
    background_tasks.add_task(train_model, symbol=symbol, period=period)
    return {
        "status":  "training_started",
        "symbol":  symbol,
        "period":  period,
        "message": f"Model training started in background. "
                   f"Call GET /predict/?symbol={symbol} when done (~10 seconds).",
    }


@router.get("/status")
def model_status(
    symbol: str = Query(default="^NSEI"),
):
    """
    Check if a trained model exists and see its performance metrics.
    """
    if not model_exists(symbol):
        return {
            "symbol":  symbol,
            "trained": False,
            "message": f"No model found. Call POST /predict/train?symbol={symbol}",
        }

    _, _, metadata = load_model(symbol)
    return {
        "symbol":   symbol,
        "trained":  True,
        "metadata": metadata,
    }