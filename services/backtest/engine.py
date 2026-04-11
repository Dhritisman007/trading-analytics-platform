# services/backtest/engine.py

import backtrader as bt
import pandas as pd
import numpy as np
import logging
from datetime import datetime

from services.market_service import fetch_market_data
from services.backtest.strategies import STRATEGY_REGISTRY
from services.backtest.metrics import (
    calculate_sharpe_ratio,
    calculate_max_drawdown,
    calculate_profit_factor,
    calculate_win_rate,
    grade_strategy,
)
from utils.formatters import format_number
from core.exceptions import InvalidParameterError

logger = logging.getLogger(__name__)


class TradeRecorder(bt.Analyzer):
    """
    Custom backtrader analyzer that records every trade.
    Backtrader doesn't expose individual trade P&L by default.
    """
    def start(self):
        self.trades = []

    def notify_trade(self, trade):
        if trade.isclosed:
            self.trades.append({
                "entry_date":  bt.num2date(trade.dtopen).strftime("%Y-%m-%d"),
                "exit_date":   bt.num2date(trade.dtclose).strftime("%Y-%m-%d"),
                "entry_price": round(trade.price, 2),
                "exit_price":  round(trade.pnl / trade.size + trade.price, 2)
                               if trade.size != 0 else 0,
                "size":        trade.size,
                "pnl":         round(trade.pnl, 2),
                "pnl_pct":     round(trade.pnlcomm / (trade.price * abs(trade.size)) * 100, 2)
                               if trade.price and trade.size else 0,
                "commission":  round(trade.commission, 2),
            })

    def get_analysis(self):
        return self.trades


class EquityCurveRecorder(bt.Analyzer):
    """Records portfolio value at every bar for equity curve chart."""
    def start(self):
        self.curve = []

    def next(self):
        self.curve.append({
            "date":  self.data.datetime.date(0).isoformat(),
            "value": round(self.strategy.broker.getvalue(), 2),
        })

    def get_analysis(self):
        return self.curve


def run_backtest(
    strategy_name: str,
    symbol: str = "^NSEI",
    period: str = "2y",
    initial_capital: float = 100000.0,
    commission_pct: float = 0.03,
    strategy_params: dict | None = None,
) -> dict:
    """
    Run a full backtest for the given strategy on historical data.

    Args:
        strategy_name:    "rsi", "ema_cross", or "macd"
        symbol:           market symbol
        period:           how far back to test
        initial_capital:  starting capital in ₹
        commission_pct:   brokerage % per trade
        strategy_params:  override default strategy parameters

    Returns:
        Complete backtest results with metrics, trades, and equity curve
    """
    # ── Validate strategy ─────────────────────────────────────────────────
    if strategy_name not in STRATEGY_REGISTRY:
        raise InvalidParameterError(
            "strategy",
            strategy_name,
            f"Valid strategies: {list(STRATEGY_REGISTRY.keys())}"
        )

    strategy_config = STRATEGY_REGISTRY[strategy_name]
    StrategyClass   = strategy_config["class"]

    # ── Fetch market data ─────────────────────────────────────────────────
    logger.info(f"Running backtest: {strategy_name} on {symbol} for {period}")
    market_data = fetch_market_data(symbol=symbol, period=period, interval="1d")

    if market_data["count"] < 60:
        raise ValueError(
            f"Not enough data to backtest. "
            f"Got {market_data['count']} candles, need at least 60. "
            f"Try period=2y."
        )

    # ── Convert to backtrader DataFrame feed ──────────────────────────────
    df = pd.DataFrame(market_data["data"])
    df["date"]   = pd.to_datetime(df["date"])
    df.set_index("date", inplace=True)
    df.columns   = [c.capitalize() for c in df.columns]

    # Backtrader expects: open, high, low, close, volume, openinterest
    df["Openinterest"] = 0

    data_feed = bt.feeds.PandasData(dataname=df)

    # ── Set up cerebro ────────────────────────────────────────────────────
    cerebro = bt.Cerebro()
    cerebro.adddata(data_feed)
    cerebro.broker.setcash(initial_capital)
    cerebro.broker.setcommission(commission=commission_pct / 100)

    # Add strategy with params
    params = strategy_params or {}
    cerebro.addstrategy(StrategyClass, **params)

    # Add custom analyzers
    cerebro.addanalyzer(TradeRecorder,      _name="trades")
    cerebro.addanalyzer(EquityCurveRecorder, _name="equity_curve")

    # ── Run backtest ──────────────────────────────────────────────────────
    start_time = datetime.now()
    results    = cerebro.run()
    duration   = round((datetime.now() - start_time).total_seconds(), 2)

    strat        = results[0]
    trades       = strat.analyzers.trades.get_analysis()
    equity_curve = strat.analyzers.equity_curve.get_analysis()

    # ── Extract portfolio values ──────────────────────────────────────────
    final_value   = cerebro.broker.getvalue()
    total_return  = ((final_value - initial_capital) / initial_capital) * 100

    # ── Calculate buy & hold return for comparison ────────────────────────
    first_close   = market_data["data"][0]["close"]
    last_close    = market_data["data"][-1]["close"]
    buy_hold_return = ((last_close - first_close) / first_close) * 100
    buy_hold_units = int(initial_capital / first_close)
    buy_hold_value = buy_hold_units * last_close

    # ── Calculate metrics ─────────────────────────────────────────────────
    equity_values = [e["value"] for e in equity_curve]
    daily_returns = []
    for i in range(1, len(equity_values)):
        if equity_values[i - 1] > 0:
            daily_returns.append(
                (equity_values[i] - equity_values[i - 1]) / equity_values[i - 1]
            )

    sharpe    = calculate_sharpe_ratio(daily_returns)
    drawdown  = calculate_max_drawdown(equity_values)
    win_stats = calculate_win_rate(trades)
    pf        = calculate_profit_factor(trades)
    grade     = grade_strategy(
        total_return_pct=total_return,
        sharpe_ratio=sharpe,
        max_drawdown_pct=drawdown["max_drawdown_pct"],
        win_rate_pct=win_stats["win_rate_pct"],
        profit_factor=pf,
        buy_hold_return=buy_hold_return,
    )

    # ── Alpha over buy & hold ─────────────────────────────────────────────
    alpha = round(total_return - buy_hold_return, 2)

    logger.info(
        f"Backtest complete: {strategy_name} | "
        f"Return: {total_return:.1f}% | Sharpe: {sharpe} | "
        f"Trades: {len(trades)} | Grade: {grade['grade']}"
    )

    return {
        "strategy":     strategy_name,
        "description":  strategy_config["description"],
        "symbol":       symbol,
        "name":         market_data["name"],
        "period":       period,
        "run_time_sec": duration,

        "config": {
            "initial_capital": initial_capital,
            "commission_pct":  commission_pct,
            "strategy_params": params or "defaults",
            "data_start":      market_data["data"][0]["date"],
            "data_end":        market_data["data"][-1]["date"],
            "total_candles":   market_data["count"],
        },

        "performance": {
            "initial_capital":  format_number(initial_capital),
            "final_value":      format_number(final_value),
            "total_return_pct": format_number(total_return),
            "total_return_inr": format_number(final_value - initial_capital),
            "sharpe_ratio":     sharpe,
            "max_drawdown_pct": drawdown["max_drawdown_pct"],
            "profit_factor":    pf,
            **win_stats,
        },

        "vs_buy_hold": {
            "buy_hold_return_pct": format_number(buy_hold_return),
            "buy_hold_value":      format_number(buy_hold_value),
            "strategy_return_pct": format_number(total_return),
            "alpha":               format_number(alpha),
            "outperformed":        alpha > 0,
        },

        "grade": grade,

        # Chart-ready equity curve (sampled for performance)
        "equity_curve": equity_curve[::max(1, len(equity_curve) // 200)],

        # Last 20 trades for the trade log table
        "recent_trades": trades[-20:] if trades else [],
        "total_trades":  len(trades),
    }