# routers/indicators.py

from fastapi import APIRouter, HTTPException, Query
import pandas as pd

from services.indicator_calculator import get_indicators
from utils.formatters import format_number

router = APIRouter(prefix="/indicators", tags=["Technical Indicators"])


@router.get("/")
def get_indicator_data(
    symbol: str = Query(
        default="^NSEI", description="^NSEI for Nifty 50, ^BSESN for Sensex"
    ),
    period: str = Query(default="3mo", description="Data period: 1mo, 3mo, 6mo, 1y"),
    interval: str = Query(
        default="1d", description="Candle interval: 1d (daily), 1wk (weekly)"
    ),
    rsi_window: int = Query(
        default=14, ge=2, le=50, description="RSI period (default 14)"
    ),
    ema_window: int = Query(
        default=20,
        ge=2,
        le=200,
        description="EMA period (default 20, try 50 or 200 for long-term)",
    ),
    atr_window: int = Query(
        default=14, ge=2, le=50, description="ATR period (default 14)"
    ),
):
    """
    Returns OHLC + RSI, EMA, MACD, ATR for the given symbol.
    Includes a 'latest' snapshot with plain-English signals for the dashboard.
    All indicator windows are configurable via query params.
    Errors are handled globally by the exception handler.
    """
    return get_indicators(
        symbol=symbol,
        period=period,
        interval=interval,
        rsi_window=rsi_window,
        ema_window=ema_window,
        atr_window=atr_window,
    )


@router.get("/latest")
def get_latest_signals(
    symbol: str = Query(default="^NSEI"),
    period: str = Query(default="3mo"),
):
    """
    Returns only the latest signals snapshot — no full data array.
    Faster for dashboard header cards that just need the current reading.
    """
    result = get_indicators(symbol=symbol, period=period)
    return {
        "symbol": result["symbol"],
        "name": result["name"],
        "latest": result["latest"],
        "windows": result["windows"],
    }


# ── Advanced indicators ───────────────────────────────────────────────────────

@router.get("/advanced")
def get_advanced_indicators(
    symbol: str = Query(default="^NSEI"),
    period: str = Query(default="3mo"),
    supertrend_period: int = Query(default=10, ge=5, le=50),
    supertrend_multiplier: float = Query(default=3.0, ge=1.0, le=5.0),
    bb_period: int = Query(default=20, ge=5, le=50),
    bb_std: float = Query(default=2.0, ge=1.0, le=4.0),
):
    """
    Advanced indicators — VWAP, Supertrend, Bollinger Bands,
    Stochastic RSI, and Ichimoku Cloud.

    All signals include plain-English explanations.
    Cached for 5 minutes.
    """
    try:
        from core.cache import cache
        from services.market_service import fetch_market_data
        from services.indicators.advanced_indicators import calculate_all_advanced

        cache_key = (
            f"advanced:{symbol}:{period}:"
            f"{supertrend_period}:{supertrend_multiplier}:"
            f"{bb_period}:{bb_std}"
        )

        cached = cache.get(cache_key)
        if cached:
            cached["_cache"] = "HIT"
            return cached

        # Fetch OHLCV data
        market_data = fetch_market_data(symbol=symbol, period=period)

        df = pd.DataFrame(market_data["data"])
        df["date"] = pd.to_datetime(df["date"])
        df.set_index("date", inplace=True)

        result_dict = calculate_all_advanced(df, config={
            "supertrend_period":     supertrend_period,
            "supertrend_multiplier": supertrend_multiplier,
            "bb_period":             bb_period,
            "bb_std":                bb_std,
        })

        df_out = result_dict["df"]

        # Build per-candle data array
        candle_data = []
        for date, row in df_out.iterrows():
            candle_data.append({
                "date":           str(date.date()),
                "close":          format_number(row["close"]),
                # VWAP
                "vwap":           format_number(row.get("vwap")),
                "vwap_u1":        format_number(row.get("vwap_u1")),
                "vwap_l1":        format_number(row.get("vwap_l1")),
                "vwap_u2":        format_number(row.get("vwap_u2")),
                "vwap_l2":        format_number(row.get("vwap_l2")),
                # Supertrend
                "supertrend":     format_number(row.get("supertrend")),
                "supertrend_dir": (
                    int(row["supertrend_direction"])
                    if pd.notna(row.get("supertrend_direction")) else 0
                ),
                # Bollinger Bands
                "bb_upper":       format_number(row.get("bb_upper")),
                "bb_middle":      format_number(row.get("bb_middle")),
                "bb_lower":       format_number(row.get("bb_lower")),
                "bb_width":       format_number(row.get("bb_width")),
                "bb_pct_b":       format_number(row.get("bb_pct_b")),
                # Stochastic RSI
                "stoch_k":        format_number(row.get("stoch_rsi_k")),
                "stoch_d":        format_number(row.get("stoch_rsi_d")),
                # Ichimoku
                "ichi_tenkan":    format_number(row.get("ichi_tenkan")),
                "ichi_kijun":     format_number(row.get("ichi_kijun")),
                "ichi_senkou_a":  format_number(row.get("ichi_senkou_a")),
                "ichi_senkou_b":  format_number(row.get("ichi_senkou_b")),
            })

        result = {
            "symbol":   symbol,
            "name":     market_data["name"],
            "period":   period,
            "count":    len(candle_data),

            # Latest signals with plain-English descriptions
            "signals": {
                "vwap":       result_dict["vwap"],
                "supertrend": result_dict["supertrend"],
                "bollinger":  result_dict["bollinger"],
                "stoch_rsi":  result_dict["stoch_rsi"],
                "ichimoku":   result_dict["ichimoku"],
            },

            # Aggregated bias score
            "overall_bias": _compute_overall_bias(result_dict),

            # Per-candle data for charting
            "data": candle_data,
        }

        cache.set(cache_key, result, ttl_seconds=300)
        result["_cache"] = "MISS"
        return result

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


def _compute_overall_bias(signals: dict) -> dict:
    """Aggregate all five advanced signals into one overall bias."""
    checks = [
        signals["vwap"].get("signal")       in ("bullish", "oversold"),
        signals["supertrend"].get("signal") == "BUY",
        signals["bollinger"].get("signal")  in ("neutral", "near_upper"),
        signals["stoch_rsi"].get("signal")  in ("BUY", "oversold"),
        signals["ichimoku"].get("signal")   == "bullish",
    ]

    bullish = sum(checks)
    bearish = len(checks) - bullish
    score   = round(bullish / len(checks) * 100)

    label = (
        "Strongly Bullish" if score >= 80 else
        "Bullish"          if score >= 60 else
        "Neutral"          if score >= 40 else
        "Bearish"          if score >= 20 else
        "Strongly Bearish"
    )
    color = (
        "#1D9E75" if score >= 60 else
        "#888780" if score >= 40 else
        "#E24B4A"
    )

    return {
        "score":   score,
        "label":   label,
        "color":   color,
        "bullish": bullish,
        "bearish": bearish,
        "total":   len(checks),
    }
