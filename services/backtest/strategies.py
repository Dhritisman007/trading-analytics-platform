# services/backtest/strategies.py

import backtrader as bt
import logging

logger = logging.getLogger(__name__)


class RSIStrategy(bt.Strategy):
    """
    RSI Mean Reversion Strategy.

    Logic:
    - BUY  when RSI drops below oversold threshold (default 30)
    - SELL when RSI rises above overbought threshold (default 70)

    This is a classic mean-reversion approach — buy when the market
    has fallen too far, sell when it has risen too far.
    """
    params = (
        ("rsi_period",    14),
        ("oversold",      30),
        ("overbought",    70),
        ("position_size", 0.95),  # use 95% of available cash
    )

    def __init__(self):
        self.rsi   = bt.indicators.RSI(self.data.close, period=self.p.rsi_period)
        self.order = None

    def next(self):
        if self.order:
            return  # wait for pending order to fill

        if not self.position:
            # Not in a trade — look for BUY signal
            if self.rsi < self.p.oversold:
                size = int(self.broker.getcash() * self.p.position_size / self.data.close[0])
                if size > 0:
                    self.order = self.buy(size=size)
                    logger.debug(f"RSI BUY: RSI={self.rsi[0]:.1f}, price={self.data.close[0]:.2f}")
        else:
            # In a trade — look for SELL signal
            if self.rsi > self.p.overbought:
                self.order = self.sell(size=self.position.size)
                logger.debug(f"RSI SELL: RSI={self.rsi[0]:.1f}, price={self.data.close[0]:.2f}")

    def notify_order(self, order):
        if order.status in [order.Completed, order.Canceled, order.Margin]:
            self.order = None


class EMAcrossStrategy(bt.Strategy):
    """
    EMA Crossover Strategy (trend following).

    Logic:
    - BUY  when fast EMA crosses above slow EMA (golden cross)
    - SELL when fast EMA crosses below slow EMA (death cross)

    This is a trend-following approach — ride the trend until
    the momentum reverses.
    """
    params = (
        ("fast_period",   9),
        ("slow_period",   21),
        ("position_size", 0.95),
    )

    def __init__(self):
        self.fast_ema    = bt.indicators.EMA(self.data.close, period=self.p.fast_period)
        self.slow_ema    = bt.indicators.EMA(self.data.close, period=self.p.slow_period)
        self.crossover   = bt.indicators.CrossOver(self.fast_ema, self.slow_ema)
        self.order       = None

    def next(self):
        if self.order:
            return

        if not self.position:
            if self.crossover > 0:  # fast crossed above slow
                size = int(self.broker.getcash() * self.p.position_size / self.data.close[0])
                if size > 0:
                    self.order = self.buy(size=size)
                    logger.debug(f"EMA BUY crossover at {self.data.close[0]:.2f}")
        else:
            if self.crossover < 0:  # fast crossed below slow
                self.order = self.sell(size=self.position.size)
                logger.debug(f"EMA SELL crossover at {self.data.close[0]:.2f}")

    def notify_order(self, order):
        if order.status in [order.Completed, order.Canceled, order.Margin]:
            self.order = None


class MACDStrategy(bt.Strategy):
    """
    MACD Histogram Crossover Strategy.

    Logic:
    - BUY  when MACD histogram crosses above zero (bullish momentum)
    - SELL when MACD histogram crosses below zero (bearish momentum)

    Uses the histogram (MACD line minus signal line) rather than
    the MACD line itself for faster signals.
    """
    params = (
        ("fast_period",   12),
        ("slow_period",   26),
        ("signal_period", 9),
        ("position_size", 0.95),
    )

    def __init__(self):
        macd           = bt.indicators.MACD(
            self.data.close,
            period_me1=self.p.fast_period,
            period_me2=self.p.slow_period,
            period_signal=self.p.signal_period,
        )
        self.histogram = macd.macd - macd.signal
        self.order     = None

    def next(self):
        if self.order:
            return

        if not self.position:
            # Histogram crosses above zero — bullish momentum
            if self.histogram[0] > 0 and self.histogram[-1] <= 0:
                size = int(self.broker.getcash() * self.p.position_size / self.data.close[0])
                if size > 0:
                    self.order = self.buy(size=size)
        else:
            # Histogram crosses below zero — bearish momentum
            if self.histogram[0] < 0 and self.histogram[-1] >= 0:
                self.order = self.sell(size=self.position.size)

    def notify_order(self, order):
        if order.status in [order.Completed, order.Canceled, order.Margin]:
            self.order = None


# Registry — maps strategy name to class and its configurable params
STRATEGY_REGISTRY = {
    "rsi": {
        "class":       RSIStrategy,
        "description": "RSI mean-reversion — buy oversold, sell overbought",
        "params": {
            "rsi_period":  {"type": "int",   "default": 14,   "min": 2,  "max": 50},
            "oversold":    {"type": "int",   "default": 30,   "min": 10, "max": 45},
            "overbought":  {"type": "int",   "default": 70,   "min": 55, "max": 90},
        },
    },
    "ema_cross": {
        "class":       EMAcrossStrategy,
        "description": "EMA crossover — trend following",
        "params": {
            "fast_period": {"type": "int",   "default": 9,    "min": 3,  "max": 50},
            "slow_period": {"type": "int",   "default": 21,   "min": 5,  "max": 200},
        },
    },
    "macd": {
        "class":       MACDStrategy,
        "description": "MACD histogram crossover — momentum",
        "params": {
            "fast_period":   {"type": "int", "default": 12,   "min": 5,  "max": 30},
            "slow_period":   {"type": "int", "default": 26,   "min": 10, "max": 60},
            "signal_period": {"type": "int", "default": 9,    "min": 3,  "max": 20},
        },
    },
}