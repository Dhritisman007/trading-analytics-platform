# tests/test_fii_dii.py

import pytest
from fastapi.testclient import TestClient
from main import app
from services.fii_dii.data_fetcher import generate_fallback_data
from services.fii_dii.flow_analyzer import (
    analyze_flows,
    calculate_moving_average,
    detect_consecutive_days,
    compute_pressure_score,
    generate_signal,
)

client = TestClient(app)


# ── Data fetcher tests ────────────────────────────────────────────────────────

class TestFallbackData:

    def test_returns_list(self):
        data = generate_fallback_data(days=30)
        assert isinstance(data, list)

    def test_returns_correct_count(self):
        data = generate_fallback_data(days=30)
        # Less than 30 because weekends are skipped
        assert 15 <= len(data) <= 25

    def test_each_record_has_required_keys(self):
        data = generate_fallback_data(days=10)
        for record in data:
            assert "date"         in record
            assert "fii"          in record
            assert "dii"          in record
            assert "combined_net" in record

    def test_fii_has_buy_sell_net(self):
        data = generate_fallback_data(days=10)
        for record in data:
            for key in ["gross_buy", "gross_sell", "net", "action"]:
                assert key in record["fii"]

    def test_action_is_buy_or_sell(self):
        data = generate_fallback_data(days=20)
        for record in data:
            assert record["fii"]["action"] in ["buy", "sell"]
            assert record["dii"]["action"] in ["buy", "sell"]

    def test_sorted_oldest_first(self):
        data = generate_fallback_data(days=20)
        dates = [d["date"] for d in data]
        assert dates == sorted(dates)


# ── Flow analyzer tests ───────────────────────────────────────────────────────

class TestMovingAverage:

    def test_correct_average(self):
        values = [100, 200, 300, 400, 500]
        result = calculate_moving_average(values, window=3)
        assert result == 400.0  # avg of 300, 400, 500

    def test_insufficient_data_returns_none(self):
        result = calculate_moving_average([100, 200], window=5)
        assert result is None

    def test_single_value_window_1(self):
        result = calculate_moving_average([150], window=1)
        assert result == 150.0


class TestConsecutiveDays:

    def _make_data(self, fii_actions: list[str]) -> list[dict]:
        """Helper to create minimal test data."""
        return [
            {
                "date": f"2024-01-{i+1:02d}",
                "fii": {"net": 100 if a == "buy" else -100, "action": a,
                        "gross_buy": 1000, "gross_sell": 900},
                "dii": {"net": 50, "action": "buy",
                        "gross_buy": 500, "gross_sell": 450},
                "combined_net": 150,
            }
            for i, a in enumerate(fii_actions)
        ]

    def test_detects_buying_streak(self):
        data   = self._make_data(["sell", "buy", "buy", "buy", "buy", "buy"])
        result = detect_consecutive_days(data, "fii")
        assert result["days"]   == 5
        assert result["action"] == "buy"

    def test_detects_selling_streak(self):
        data   = self._make_data(["buy", "sell", "sell", "sell"])
        result = detect_consecutive_days(data, "fii")
        assert result["days"]   == 3
        assert result["action"] == "sell"

    def test_significant_flag_above_5(self):
        data   = self._make_data(["buy"] * 6)
        result = detect_consecutive_days(data, "fii")
        assert result["significant"] is True

    def test_not_significant_below_5(self):
        data   = self._make_data(["buy"] * 3)
        result = detect_consecutive_days(data, "fii")
        assert result["significant"] is False


class TestPressureScore:

    def test_strong_fii_buying_positive_score(self):
        result = compute_pressure_score(
            fii_net=1000,
            dii_net=500,
            fii_5d_avg=500,
            dii_5d_avg=300,
        )
        assert result["score"] > 0
        assert result["label"] in ["moderate buying", "strong buying"]

    def test_strong_selling_negative_score(self):
        result = compute_pressure_score(
            fii_net=-1000,
            dii_net=-500,
            fii_5d_avg=500,
            dii_5d_avg=300,
        )
        assert result["score"] < 0

    def test_score_in_valid_range(self):
        result = compute_pressure_score(5000, 3000, 500, 300)
        assert -100 <= result["score"] <= 100

    def test_has_required_keys(self):
        result = compute_pressure_score(500, 200, 400, 200)
        for key in ["score", "label", "color",
                    "fii_contribution", "dii_contribution"]:
            assert key in result


class TestGenerateSignal:

    def _streak(self, action, days=3):
        return {"days": days, "action": action, "significant": days >= 5}

    def _pressure(self):
        return {"score": 30, "label": "moderate buying", "color": "#5DCAA5"}

    def test_both_buying_is_bullish(self):
        result = generate_signal(
            "buy", "buy",
            self._streak("buy"), self._streak("buy"),
            self._pressure()
        )
        assert result["signal"] == "BULLISH"

    def test_both_selling_is_bearish(self):
        result = generate_signal(
            "sell", "sell",
            self._streak("sell"), self._streak("sell"),
            self._pressure()
        )
        assert result["signal"] == "BEARISH"

    def test_fii_buy_dii_sell_cautious_bullish(self):
        result = generate_signal(
            "buy", "sell",
            self._streak("buy"), self._streak("sell"),
            self._pressure()
        )
        assert "BULLISH" in result["signal"]

    def test_description_is_string(self):
        result = generate_signal(
            "buy", "buy",
            self._streak("buy", 6), self._streak("buy"),
            self._pressure()
        )
        assert isinstance(result["description"], str)
        assert len(result["description"]) > 10


class TestAnalyzeFlows:

    def test_returns_required_keys(self):
        data   = generate_fallback_data(days=30)
        result = analyze_flows(data)
        for key in ["today", "signal", "pressure", "streaks",
                    "moving_averages", "period_summary", "chart_data"]:
            assert key in result

    def test_chart_data_has_arrays(self):
        data   = generate_fallback_data(days=30)
        result = analyze_flows(data)
        chart  = result["chart_data"]
        for key in ["dates", "fii_net", "dii_net", "combined", "fii_colors"]:
            assert key in chart
            assert isinstance(chart[key], list)

    def test_chart_arrays_same_length(self):
        data   = generate_fallback_data(days=30)
        result = analyze_flows(data)
        chart  = result["chart_data"]
        length = len(chart["dates"])
        assert len(chart["fii_net"]) == length
        assert len(chart["dii_net"]) == length

    def test_colors_are_valid_hex(self):
        data   = generate_fallback_data(days=30)
        result = analyze_flows(data)
        for color in result["chart_data"]["fii_colors"]:
            assert color.startswith("#")

    def test_empty_data_returns_error(self):
        result = analyze_flows([])
        assert "error" in result


# ── HTTP endpoint tests ───────────────────────────────────────────────────────

class TestFiiDiiEndpoints:

    def test_main_endpoint_returns_200(self):
        r = client.get("/fii-dii/")
        assert r.status_code == 200

    def test_response_has_required_sections(self):
        r = client.get("/fii-dii/")
        body = r.json()
        for key in ["today", "signal", "pressure",
                    "chart_data", "period_summary"]:
            assert key in body

    def test_today_endpoint_returns_200(self):
        r = client.get("/fii-dii/today")
        assert r.status_code == 200

    def test_today_has_fii_and_dii(self):
        r = client.get("/fii-dii/today")
        body = r.json()
        assert "fii"     in body
        assert "dii"     in body
        assert "signal"  in body
        assert "pressure" in body

    def test_signal_is_valid(self):
        r      = client.get("/fii-dii/today")
        signal = r.json()["signal"]["signal"]
        valid  = ["BULLISH", "CAUTIOUSLY BULLISH", "CAUTIOUSLY BEARISH", "BEARISH"]
        assert signal in valid

    def test_pressure_score_in_range(self):
        r     = client.get("/fii-dii/today")
        score = r.json()["pressure"]["score"]
        assert -100 <= float(score) <= 100

    def test_chart_endpoint_returns_200(self):
        r = client.get("/fii-dii/chart")
        assert r.status_code == 200
        assert "chart_data" in r.json()

    def test_summary_endpoint_returns_200(self):
        r = client.get("/fii-dii/summary")
        assert r.status_code == 200
        assert "period_summary" in r.json()

    def test_period_summary_buy_sell_consistent(self):
        r      = client.get("/fii-dii/summary")
        period = r.json()["period_summary"]
        assert (
            period["fii_buy_days"] + period["fii_sell_days"] ==
            period["days"]
        )

    def test_refresh_endpoint_returns_200(self):
        r = client.post("/fii-dii/refresh")
        assert r.status_code == 200
        assert r.json()["status"] == "refreshed"

    def test_invalid_days_returns_422(self):
        r = client.get("/fii-dii/?days=999")
        assert r.status_code == 422

    def test_days_param_respected(self):
        r = client.get("/fii-dii/?days=10")
        assert r.status_code == 200