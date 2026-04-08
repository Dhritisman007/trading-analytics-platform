# tests/test_fvg.py

import pytest
import pandas as pd
from fastapi.testclient import TestClient
from main import app
from services.fvg_service import (
    detect_fvgs,
    _classify_fvg_strength,
    _check_if_filled,
)

client = TestClient(app)


# ── Unit tests: FVG strength classifier ──────────────────────────────────────

class TestClassifyFVGStrength:

    def test_large_gap_relative_to_atr_is_strong(self):
        assert _classify_fvg_strength(gap_size=200, atr=100) == "strong"

    def test_medium_gap_relative_to_atr_is_medium(self):
        assert _classify_fvg_strength(gap_size=80, atr=100) == "medium"

    def test_small_gap_relative_to_atr_is_weak(self):
        assert _classify_fvg_strength(gap_size=20, atr=100) == "weak"

    def test_fallback_without_atr_large_gap(self):
        assert _classify_fvg_strength(gap_size=150, atr=None) == "strong"

    def test_fallback_without_atr_small_gap(self):
        assert _classify_fvg_strength(gap_size=10, atr=None) == "weak"


# ── Unit tests: fill detection ────────────────────────────────────────────────

class TestCheckIfFilled:

    def _make_df(self, highs, lows):
        """Helper: create a minimal DataFrame with high/low columns."""
        return pd.DataFrame({"high": highs, "low": lows})

    def test_bullish_fvg_filled_when_later_candle_dips_into_gap(self):
        # Gap top is 100. A later candle's low = 95 → dips below gap top → filled
        df = self._make_df(
            highs=[110, 130, 140, 135],
            lows= [90,  115, 125,  95],  # last candle dips to 95
        )
        fvg = {"type": "bullish", "gap_top": 100}
        assert _check_if_filled(fvg, df, fvg_index=2) is True

    def test_bullish_fvg_open_when_price_stays_above_gap(self):
        # Gap top is 100. All subsequent lows stay above 100 → still open
        df = self._make_df(
            highs=[110, 130, 145, 150],
            lows= [90,  115, 130, 135],
        )
        fvg = {"type": "bullish", "gap_top": 100}
        assert _check_if_filled(fvg, df, fvg_index=2) is False

    def test_bearish_fvg_filled_when_later_candle_rises_into_gap(self):
        # Gap bottom is 200. A later candle's high = 205 → rises above gap bottom → filled
        df = self._make_df(
            highs=[220, 190, 175, 205],
            lows= [195, 160, 150, 185],
        )
        fvg = {"type": "bearish", "gap_bottom": 200}
        assert _check_if_filled(fvg, df, fvg_index=2) is True

    def test_bearish_fvg_open_when_price_stays_below_gap(self):
        df = self._make_df(
            highs=[220, 190, 170, 180],
            lows= [195, 160, 150, 160],
        )
        fvg = {"type": "bearish", "gap_bottom": 200}
        assert _check_if_filled(fvg, df, fvg_index=2) is False


# ── Integration tests: full detect_fvgs() ────────────────────────────────────

class TestDetectFVGs:

    def test_returns_required_keys(self):
        result = detect_fvgs("^NSEI", period="3mo")
        for key in ["symbol", "name", "summary", "fvgs", "nearest_open_fvg"]:
            assert key in result

    def test_summary_has_correct_keys(self):
        result = detect_fvgs("^NSEI", period="3mo")
        for key in ["total_fvgs", "bullish", "bearish", "open", "filled", "fill_rate_pct"]:
            assert key in result["summary"]

    def test_bullish_plus_bearish_equals_total(self):
        result = detect_fvgs("^NSEI", period="3mo")
        s = result["summary"]
        assert s["bullish"] + s["bearish"] == s["total_fvgs"]

    def test_open_plus_filled_equals_total(self):
        result = detect_fvgs("^NSEI", period="3mo")
        s = result["summary"]
        assert s["open"] + s["filled"] == s["total_fvgs"]

    def test_each_fvg_has_required_fields(self):
        result = detect_fvgs("^NSEI", period="3mo")
        for fvg in result["fvgs"]:
            for field in ["type", "gap_bottom", "gap_top", "gap_size",
                          "strength", "filled", "candle_1", "candle_2", "candle_3"]:
                assert field in fvg, f"Missing field: {field}"

    def test_fvg_type_is_always_valid(self):
        result = detect_fvgs("^NSEI", period="3mo")
        for fvg in result["fvgs"]:
            assert fvg["type"] in ["bullish", "bearish"]

    def test_gap_top_always_greater_than_gap_bottom(self):
        result = detect_fvgs("^NSEI", period="3mo")
        for fvg in result["fvgs"]:
            assert fvg["gap_top"] > fvg["gap_bottom"], \
                f"gap_top {fvg['gap_top']} <= gap_bottom {fvg['gap_bottom']}"

    def test_strength_is_always_valid(self):
        result = detect_fvgs("^NSEI", period="3mo")
        for fvg in result["fvgs"]:
            assert fvg["strength"] in ["strong", "medium", "weak"]

    def test_only_open_filter_works(self):
        result = detect_fvgs("^NSEI", period="3mo", only_open=True)
        for fvg in result["fvgs"]:
            assert fvg["filled"] is False

    def test_min_gap_size_filter_works(self):
        result = detect_fvgs("^NSEI", period="3mo", min_gap_size=100.0)
        for fvg in result["fvgs"]:
            assert fvg["gap_size"] >= 100.0

    def test_fill_rate_between_0_and_100(self):
        result = detect_fvgs("^NSEI", period="3mo")
        assert 0 <= result["summary"]["fill_rate_pct"] <= 100


# ── HTTP endpoint tests ───────────────────────────────────────────────────────

class TestFVGEndpoints:

    def test_fvg_endpoint_200(self):
        r = client.get("/fvg/")
        assert r.status_code == 200

    def test_fvg_open_endpoint_200(self):
        r = client.get("/fvg/open")
        assert r.status_code == 200

    def test_only_open_query_param(self):
        r = client.get("/fvg/?only_open=true")
        assert r.status_code == 200
        for fvg in r.json()["fvgs"]:
            assert fvg["filled"] is False

    def test_min_gap_size_query_param(self):
        r = client.get("/fvg/?min_gap_size=50")
        assert r.status_code == 200
        for fvg in r.json()["fvgs"]:
            assert fvg["gap_size"] >= 50

    def test_sensex_fvg(self):
        r = client.get("/fvg/?symbol=^BSESN&period=3mo")
        assert r.status_code == 200

    def test_invalid_min_gap_rejected(self):
        r = client.get("/fvg/?min_gap_size=-10")
        assert r.status_code == 422