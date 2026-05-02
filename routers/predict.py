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


import pandas as pd

@router.get("/patterns")
def get_candlestick_patterns(
    symbol: str = Query(default="^NSEI"),
    period: str = Query(default="3mo"),
):
    """
    Detect candlestick patterns — Doji, Hammer, Engulfing,
    Morning Star, Evening Star, Three Soldiers/Crows, and more.
    """
    try:
        from services.market_service import fetch_market_data
        from services.ml.pattern_detector import detect_patterns, get_pattern_summary
        from core.cache import get_cache, set_cache

        cache_key = f"patterns:{symbol}:{period}"
        cached    = get_cache(cache_key)
        if cached:
            return cached

        market = fetch_market_data(symbol=symbol, period=period)
        df     = pd.DataFrame(market["data"])
        df["date"] = pd.to_datetime(df["date"])
        df.set_index("date", inplace=True)

        patterns = detect_patterns(df)
        summary  = get_pattern_summary(patterns)

        result = {
            "symbol":   symbol,
            "patterns": patterns,
            "summary":  summary,
            "count":    len(patterns),
        }
        set_cache(cache_key, result, ttl_seconds=1800)
        return result

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/train/lstm")
async def train_lstm_model(
    symbol: str = Query(default="^NSEI"),
    period: str = Query(default="2y"),
    background_tasks: BackgroundTasks = None,
):
    """
    Train the LSTM model for a symbol.
    Runs in background — training takes 1-3 minutes.
    """
    def _train():
        try:
            from services.market_service import fetch_market_data
            from services.ml.lstm_model   import train_lstm
            import logging
            logger = logging.getLogger(__name__)

            market = fetch_market_data(symbol=symbol, period=period)
            df     = pd.DataFrame(market["data"])
            df["date"] = pd.to_datetime(df["date"])
            df.set_index("date", inplace=True)

            result = train_lstm(df, symbol=symbol)
            logger.info(f"LSTM training complete for {symbol}: {result['accuracy']}%")
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"LSTM training failed for {symbol}: {e}")

    if background_tasks:
        background_tasks.add_task(_train)
        return {
            "status":  "training_started",
            "symbol":  symbol,
            "message": "LSTM training started in background. Check /predict/lstm status."
        }

    _train()
    return {"status": "complete", "symbol": symbol}


@router.get("/lstm")
def get_lstm_prediction(
    symbol: str = Query(default="^NSEI"),
    period: str = Query(default="3mo"),
):
    """
    Get LSTM prediction for a symbol.
    Returns probability of price going up tomorrow.
    """
    try:
        from services.market_service import fetch_market_data
        from services.ml.lstm_model   import predict_lstm

        market = fetch_market_data(symbol=symbol, period=period)
        df     = pd.DataFrame(market["data"])
        df["date"] = pd.to_datetime(df["date"])
        df.set_index("date", inplace=True)

        prediction = predict_lstm(df, symbol=symbol)
        prediction["symbol"] = symbol
        prediction["price"]  = market["summary"]["latest_close"]
        return prediction

    except FileNotFoundError:
        raise HTTPException(
            status_code=404,
            detail=f"LSTM model not found for {symbol}. POST /predict/train/lstm to train it first."
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/commentary")
async def get_gpt_commentary(
    symbol: str = Query(default="^NSEI"),
    period: str = Query(default="3mo"),
):
    """
    GPT-4o-mini market commentary — synthesises all indicators
    into plain English analysis. Requires OPENAI_API_KEY.
    """
    try:
        from services.market_service      import fetch_market_data
        from services.indicator_calculator import get_indicators
        from services.news.news_service    import get_news
        from services.fii_dii.fii_dii_service import get_fii_dii
        from services.ml.predictor         import predict
        from services.ml.gpt_commentary    import generate_market_commentary

        # Gather all data
        market     = fetch_market_data(symbol=symbol, period=period)
        indicators = get_indicators(symbol=symbol, period=period)
        news_mood  = get_news(limit=30)
        fii_data   = get_fii_dii(days=5)

        ml_pred = None
        try:
            ml_pred = predict(symbol=symbol)
        except Exception:
            pass

        commentary = await generate_market_commentary(
            symbol=symbol,
            market_data=market,
            indicators=indicators,
            ml_prediction=ml_pred,
            news_mood=news_mood,
            fii_dii=fii_data,
        )
        return commentary

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))