# tests/test_backtest.py

import pytest
from fastapi.testclient import TestClient
from main import app
from services.backtest.metrics import (
    calculate_sharpe_ratio,
    calculate_max_drawdown,
    calculate_profit_factor,
    calculate_win_rate,
    grade_strategy,
)
from services.backtest.strategies import STRATEGY_REGISTRY

client = TestClient(app)


# ── Metrics unit tests ────────────────────────────────────────────────────────

class TestSharpeRatio:

    def test_positive_returns_give_positive_sharpe(self):
        returns = [0.001] * 100
        assert calculate_sharpe_ratio(returns) > 0

    def test_zero_returns_give_zero_sharpe(self):
        returns = [0.0] * 100
        assert calculate_sharpe_ratio(returns) == 0.0

    def test_negative_returns_give_negative_sharpe(self):
        returns = [-0.001] * 100
        assert calculate_sharpe_ratio(returns) < 0

    def test_empty_returns_give_zero(self):
        assert calculate_sharpe_ratio([]) == 0.0

    def test_single_return_gives_zero(self):
        assert calculate_sharpe_ratio([0.01]) == 0.0


class TestMaxDrawdown:

    def test_no_drawdown_all_rising(self):
        equity = [100, 110, 120, 130, 140]
        result = calculate_max_drawdown(equity)
        assert result["max_drawdown_pct"] == 0.0

    def test_detects_correct_drawdown(self):
        # Peak 100 → trough 70 = 30% drawdown
        equity = [100, 110, 100, 90, 70, 80, 90]
        result = calculate_max_drawdown(equity)
        assert abs(result["max_drawdown_pct"] - 36.36) < 1.0

    def test_empty_equity_returns_zero(self):
        result = calculate_max_drawdown([])
        assert result["max_drawdown_pct"] == 0.0

    def test_peak_value_correct(self):
        equity = [100, 150, 120, 100]
        result = calculate_max_drawdown(equity)
        assert result["peak_value"] == 150


class TestProfitFactor:

    def test_profitable_trades(self):
        trades = [{"pnl": 100}, {"pnl": 200}, {"pnl": -50}]
        assert calculate_profit_factor(trades) == pytest.approx(6.0)

    def test_all_losses(self):
        trades = [{"pnl": -100}, {"pnl": -200}]
        assert calculate_profit_factor(trades) == 0.0

    def test_no_losses_returns_inf(self):
        trades = [{"pnl": 100}, {"pnl": 200}]
        result = calculate_profit_factor(trades)
        assert result == float("inf")

    def test_empty_trades(self):
        assert calculate_profit_factor([]) == 0.0


class TestWinRate:

    def test_correct_win_rate(self):
        trades = [{"pnl": 100}, {"pnl": -50}, {"pnl": 200}, {"pnl": -30}]
        result = calculate_win_rate(trades)
        assert result["win_rate_pct"] == 50.0
        assert result["wins"] == 2
        assert result["losses"] == 2

    def test_empty_trades(self):
        result = calculate_win_rate([])
        assert result["win_rate_pct"] == 0.0
        assert result["total"] == 0

    def test_all_wins(self):
        trades = [{"pnl": 100}, {"pnl": 200}]
        result = calculate_win_rate(trades)
        assert result["win_rate_pct"] == 100.0


class TestGradeStrategy:

    def test_excellent_gets_grade_a(self):
        result = grade_strategy(
            total_return_pct=25,
            sharpe_ratio=2.5,
            max_drawdown_pct=5,
            win_rate_pct=65,
            profit_factor=2.0,
            buy_hold_return=15,
        )
        assert result["grade"] == "A"

    def test_poor_gets_grade_f(self):
        result = grade_strategy(
            total_return_pct=-10,
            sharpe_ratio=-0.5,
            max_drawdown_pct=40,
            win_rate_pct=30,
            profit_factor=0.5,
            buy_hold_return=15,
        )
        assert result["grade"] in ["D", "F"]

    def test_color_is_hex(self):
        result = grade_strategy(20, 1.5, 10, 55, 1.4, 15)
        assert result["color"].startswith("#")


# ── Strategy registry ─────────────────────────────────────────────────────────

class TestStrategyRegistry:

    def test_all_three_strategies_registered(self):
        for name in ["rsi", "ema_cross", "macd"]:
            assert name in STRATEGY_REGISTRY

    def test_each_strategy_has_class_and_params(self):
        for name, config in STRATEGY_REGISTRY.items():
            assert "class"       in config
            assert "description" in config
            assert "params"      in config


# ── HTTP endpoints ────────────────────────────────────────────────────────────

class TestBacktestEndpoints:

    def test_strategies_list_returns_200(self):
        r = client.get("/backtest/strategies")
        assert r.status_code == 200
        assert "strategies" in r.json()

    def test_strategies_list_has_three(self):
        r = client.get("/backtest/strategies")
        assert len(r.json()["strategies"]) == 3

    def test_rsi_backtest_returns_200(self):
        r = client.get("/backtest/?strategy=rsi&period=2y")
        assert r.status_code == 200

    def test_response_has_required_sections(self):
        r = client.get("/backtest/?strategy=rsi&period=2y")
        body = r.json()
        for key in ["strategy", "performance", "vs_buy_hold",
                    "grade", "equity_curve", "total_trades"]:
            assert key in body

    def test_performance_has_all_metrics(self):
        r = client.get("/backtest/?strategy=rsi&period=2y")
        perf = r.json()["performance"]
        for key in ["total_return_pct", "sharpe_ratio",
                    "max_drawdown_pct", "win_rate_pct", "profit_factor"]:
            assert key in perf

    def test_equity_curve_is_list(self):
        r = client.get("/backtest/?strategy=rsi&period=2y")
        assert isinstance(r.json()["equity_curve"], list)
        assert len(r.json()["equity_curve"]) > 0

    def test_grade_is_valid_letter(self):
        r = client.get("/backtest/?strategy=rsi&period=2y")
        assert r.json()["grade"]["grade"] in list("ABCDF")

    def test_vs_buy_hold_has_alpha(self):
        r = client.get("/backtest/?strategy=rsi&period=2y")
        assert "alpha" in r.json()["vs_buy_hold"]

    def test_ema_cross_strategy(self):
        r = client.get("/backtest/?strategy=ema_cross&period=2y")
        assert r.status_code == 200

    def test_macd_strategy(self):
        r = client.get("/backtest/?strategy=macd&period=2y")
        assert r.status_code == 200

    def test_invalid_strategy_returns_400(self):
        r = client.get("/backtest/?strategy=invalid_xyz")
        assert r.status_code == 400

    def test_custom_rsi_params(self):
        r = client.get("/backtest/?strategy=rsi&rsi_period=7&oversold=25")
        assert r.status_code == 200

    def test_compare_endpoint_returns_200(self):
        r = client.get("/backtest/compare?period=2y")
        assert r.status_code == 200

    def test_compare_has_winner(self):
        r = client.get("/backtest/compare?period=2y")
        assert "winner" in r.json()

    def test_compare_has_three_results(self):
        r = client.get("/backtest/compare?period=2y")
        assert len(r.json()["results"]) == 3