# tests/test_risk.py

import pytest
from fastapi.testclient import TestClient
from main import app
from services.risk_service import (
    calculate_position_size,
    calculate_risk_reward,
    calculate_atr_stops,
    calculate_breakeven,
    score_trade,
    full_risk_analysis,
)

client = TestClient(app)


# ── Position sizing ───────────────────────────────────────────────────────────

class TestPositionSize:

    def test_basic_calculation(self):
        result = calculate_position_size(
            capital=500000,
            risk_pct=1.0,
            entry_price=23450,
            stop_loss=23100,
        )
        assert result["units"] > 0
        assert result["risk_amount"] > 0
        assert result["capital_used_pct"] > 0

    def test_risk_amount_close_to_target(self):
        result = calculate_position_size(
            capital=500000,
            risk_pct=1.0,
            entry_price=23450,
            stop_loss=23100,
        )
        # Risk should be close to 1% of 500000 = 5000
        assert abs(float(result["risk_amount"]) - 5000) < 500

    def test_stop_above_entry_raises(self):
        with pytest.raises(ValueError, match="Stop loss"):
            calculate_position_size(500000, 1.0, 23000, 23500)

    def test_risk_pct_too_high_raises(self):
        with pytest.raises(ValueError, match="Risk %"):
            calculate_position_size(500000, 10.0, 23450, 23100)

    def test_negative_capital_raises(self):
        with pytest.raises(ValueError, match="Capital"):
            calculate_position_size(-100000, 1.0, 23450, 23100)

    def test_higher_risk_pct_gives_more_units(self):
        r1 = calculate_position_size(500000, 1.0, 23450, 23100)
        r2 = calculate_position_size(500000, 2.0, 23450, 23100)
        assert r2["units"] > r1["units"]

    def test_wider_stop_gives_fewer_units(self):
        r1 = calculate_position_size(500000, 1.0, 23450, 23100)  # 350 stop
        r2 = calculate_position_size(500000, 1.0, 23450, 22950)  # 500 stop
        assert r1["units"] > r2["units"]


# ── Risk:Reward ───────────────────────────────────────────────────────────────

class TestRiskReward:

    def test_basic_calculation(self):
        result = calculate_risk_reward(23450, 23100, 24150)
        assert float(result["rr_ratio"]) > 0
        assert "rr_display" in result

    def test_rr_ratio_correct(self):
        # Risk = 350, Reward = 700 → R:R = 2.0
        result = calculate_risk_reward(23450, 23100, 24150)
        assert abs(float(result["rr_ratio"]) - 2.0) < 0.01

    def test_excellent_quality_at_3x(self):
        # Risk = 100, Reward = 300 → R:R = 3.0
        result = calculate_risk_reward(1000, 900, 1300)
        assert result["quality"] == "EXCELLENT"

    def test_good_quality_at_2x(self):
        result = calculate_risk_reward(1000, 900, 1200)
        assert result["quality"] == "GOOD"

    def test_poor_quality_at_1x(self):
        result = calculate_risk_reward(1000, 900, 1100)
        assert result["quality"] == "POOR"

    def test_target_below_entry_raises(self):
        with pytest.raises(ValueError, match="Target"):
            calculate_risk_reward(23450, 23100, 23000)

    def test_rr_display_format(self):
        result = calculate_risk_reward(1000, 900, 1200)
        assert result["rr_display"].startswith("1:")


# ── ATR stops ─────────────────────────────────────────────────────────────────

class TestATRStops:

    def test_stop_below_entry(self):
        result = calculate_atr_stops(23450, atr=200, atr_multiplier=1.5)
        assert float(result["stop_loss"]) < 23450

    def test_target_above_entry(self):
        result = calculate_atr_stops(23450, atr=200, atr_multiplier=1.5, rr_ratio=2.0)
        assert float(result["target_price"]) > 23450

    def test_stop_distance_equals_atr_times_multiplier(self):
        result = calculate_atr_stops(23450, atr=200, atr_multiplier=1.5)
        assert abs(float(result["stop_distance"]) - 300) < 0.01

    def test_zero_atr_raises(self):
        with pytest.raises(ValueError):
            calculate_atr_stops(23450, atr=0)


# ── Trade scoring ─────────────────────────────────────────────────────────────

class TestTradeScore:

    def test_high_rr_gives_high_score(self):
        result = score_trade(rr_ratio=3.0)
        assert result["score"] >= 40

    def test_low_rr_gives_low_score(self):
        result = score_trade(rr_ratio=0.5)
        assert result["score"] <= 10

    def test_grade_a_for_excellent_trade(self):
        result = score_trade(
            rr_ratio=3.0,
            signal_confidence=75.0,
            rsi_value=45.0,
            signal="BUY",
        )
        assert result["grade"] == "A"

    def test_grade_f_for_terrible_trade(self):
        result = score_trade(
            rr_ratio=0.3,
            signal_confidence=51.0,
            rsi_value=75.0,
            signal="BUY",
        )
        assert result["grade"] == "F"

    def test_factors_list_not_empty(self):
        result = score_trade(rr_ratio=2.0, signal_confidence=65.0)
        assert len(result["factors"]) > 0

    def test_color_is_hex(self):
        result = score_trade(rr_ratio=2.0)
        assert result["color"].startswith("#")


# ── Full analysis ─────────────────────────────────────────────────────────────

class TestFullAnalysis:

    def _default_params(self):
        return dict(
            capital=500000,
            risk_pct=1.0,
            entry_price=23450,
            stop_loss=23100,
            target_price=24150,
        )

    def test_returns_all_sections(self):
        result = full_risk_analysis(**self._default_params())
        for key in ["inputs", "position_size", "risk_reward",
                    "breakeven", "projections", "trade_score", "summary"]:
            assert key in result

    def test_summary_is_string(self):
        result = full_risk_analysis(**self._default_params())
        assert isinstance(result["summary"], str)
        assert len(result["summary"]) > 10

    def test_with_atr_includes_atr_stops(self):
        result = full_risk_analysis(**self._default_params(), atr=210.0)
        assert result["atr_stops"] is not None

    def test_without_atr_atr_stops_is_none(self):
        result = full_risk_analysis(**self._default_params())
        assert result["atr_stops"] is None

    def test_max_profit_greater_than_max_loss_for_good_rr(self):
        result = full_risk_analysis(**self._default_params())
        assert float(result["projections"]["max_profit"]) > \
               float(result["projections"]["max_loss"])


# ── HTTP endpoints ────────────────────────────────────────────────────────────

class TestRiskEndpoints:

    BASE = (
        "/risk/?capital=500000"
        "&entry_price=23450"
        "&stop_loss=23100"
        "&target_price=24150"
    )

    def test_full_analysis_returns_200(self):
        r = client.get(self.BASE)
        assert r.status_code == 200

    def test_response_has_summary(self):
        r = client.get(self.BASE)
        assert "summary" in r.json()

    def test_with_ml_params(self):
        r = client.get(
            self.BASE + "&signal=BUY&signal_confidence=65&rsi_value=52"
        )
        assert r.status_code == 200
        assert r.json()["trade_score"]["grade"] in list("ABCDF")

    def test_stop_above_entry_returns_400(self):
        r = client.get(
            "/risk/?capital=500000&entry_price=23000"
            "&stop_loss=23500&target_price=24000"
        )
        assert r.status_code == 400

    def test_invalid_risk_pct_returns_422(self):
        r = client.get(self.BASE + "&risk_pct=99")
        assert r.status_code == 422

    def test_quick_endpoint_returns_200(self):
        r = client.get(
            "/risk/quick?capital=500000&entry_price=23450&stop_loss=23100"
        )
        assert r.status_code == 200

    def test_quick_has_units(self):
        r = client.get(
            "/risk/quick?capital=500000&entry_price=23450&stop_loss=23100"
        )
        assert "units" in r.json()

    def test_atr_stops_endpoint(self):
        r = client.get("/risk/atr-stops?entry_price=23450")
        assert r.status_code == 200

    def test_atr_stops_has_stop_and_target(self):
        r = client.get("/risk/atr-stops?entry_price=23450")
        body = r.json()
        assert "stop_loss"    in body
        assert "target_price" in body