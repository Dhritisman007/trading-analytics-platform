# routers/backtest.py

from fastapi import APIRouter, HTTPException, Query, BackgroundTasks
from services.backtest.engine import run_backtest
from services.backtest.strategies import STRATEGY_REGISTRY
from core.cache import cache
from core.exceptions import InvalidParameterError, TradingPlatformError

router = APIRouter(prefix="/backtest", tags=["Backtesting"])


@router.get("/")
def run_strategy_backtest(
    strategy: str = Query(
        default="rsi",
        description="Strategy name: rsi, ema_cross, macd"
    ),
    symbol: str = Query(
        default="^NSEI",
        description="^NSEI for Nifty 50, ^BSESN for Sensex"
    ),
    period: str = Query(
        default="2y",
        description="Test period: 1y, 2y, 5y. Longer = more reliable results."
    ),
    initial_capital: float = Query(
        default=100000.0,
        ge=10000,
        description="Starting capital in ₹ (minimum ₹10,000)"
    ),
    commission_pct: float = Query(
        default=0.03,
        ge=0.0, le=1.0,
        description="Brokerage % per trade (default 0.03%)"
    ),
    # RSI strategy params
    rsi_period:  int | None = Query(default=None, ge=2,  le=50),
    oversold:    int | None = Query(default=None, ge=10, le=45),
    overbought:  int | None = Query(default=None, ge=55, le=90),
    # EMA crossover params
    fast_period: int | None = Query(default=None, ge=3,  le=50),
    slow_period: int | None = Query(default=None, ge=5,  le=200),
    # MACD params
    signal_period: int | None = Query(default=None, ge=3, le=20),
):
    """
    Run a backtest for the given strategy on historical market data.

    Returns comprehensive performance metrics including:
    - Total return % vs buy & hold
    - Sharpe ratio, max drawdown, win rate
    - Equity curve (for charting)
    - Trade log (last 20 trades)
    - Overall strategy grade (A–F)

    First run takes ~5 seconds. Results are cached for 30 minutes.
    """
    # Build strategy params from query params
    strategy_params = {}
    if strategy == "rsi":
        if rsi_period:  strategy_params["rsi_period"]  = rsi_period
        if oversold:    strategy_params["oversold"]     = oversold
        if overbought:  strategy_params["overbought"]   = overbought
    elif strategy == "ema_cross":
        if fast_period: strategy_params["fast_period"]  = fast_period
        if slow_period: strategy_params["slow_period"]  = slow_period
    elif strategy == "macd":
        if fast_period:   strategy_params["fast_period"]   = fast_period
        if slow_period:   strategy_params["slow_period"]   = slow_period
        if signal_period: strategy_params["signal_period"] = signal_period

    # Cache key — same params = same result
    cache_key = (
        f"backtest:{strategy}:{symbol}:{period}:"
        f"{initial_capital}:{commission_pct}:{strategy_params}"
    )
    cached = cache.get(cache_key)
    if cached:
        cached["_cache"] = "HIT"
        return cached

    try:
        result = run_backtest(
            strategy_name=strategy,
            symbol=symbol,
            period=period,
            initial_capital=initial_capital,
            commission_pct=commission_pct,
            strategy_params=strategy_params if strategy_params else None,
        )
        # Cache for 30 minutes — backtests are expensive
        cache.set(cache_key, result, ttl_seconds=1800)
        result["_cache"] = "MISS"
        return result

    except InvalidParameterError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except TradingPlatformError as e:
        raise HTTPException(status_code=e.status_code, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Backtest failed: {str(e)}")


@router.get("/strategies")
def list_strategies():
    """
    List all available strategies with their parameters and descriptions.
    Use this to build the strategy selector in the React dashboard.
    """
    strategies = []
    for name, config in STRATEGY_REGISTRY.items():
        strategies.append({
            "name":        name,
            "description": config["description"],
            "params":      config["params"],
        })
    return {"strategies": strategies}


@router.get("/compare")
def compare_strategies(
    symbol: str = Query(default="^NSEI"),
    period: str = Query(default="2y"),
    initial_capital: float = Query(default=100000.0, ge=10000),
):
    """
    Run all three strategies on the same data and compare.
    Shows which strategy performed best over the test period.
    Takes ~15 seconds (3 backtests).
    """
    results = []
    for strategy_name in STRATEGY_REGISTRY:
        try:
            result = run_backtest(
                strategy_name=strategy_name,
                symbol=symbol,
                period=period,
                initial_capital=initial_capital,
            )
            results.append({
                "strategy":        strategy_name,
                "description":     result["description"],
                "total_return_pct": result["performance"]["total_return_pct"],
                "sharpe_ratio":    result["performance"]["sharpe_ratio"],
                "max_drawdown_pct": result["performance"]["max_drawdown_pct"],
                "win_rate_pct":    result["performance"]["win_rate_pct"],
                "total_trades":    result["total_trades"],
                "grade":           result["grade"]["grade"],
                "outperformed_bh": result["vs_buy_hold"]["outperformed"],
                "alpha":           result["vs_buy_hold"]["alpha"],
            })
        except Exception as e:
            results.append({"strategy": strategy_name, "error": str(e)})

    # Sort by total return descending
    results.sort(
        key=lambda x: float(x.get("total_return_pct", -9999)),
        reverse=True
    )

    return {
        "symbol":   symbol,
        "period":   period,
        "results":  results,
        "winner":   results[0]["strategy"] if results else None,
    }