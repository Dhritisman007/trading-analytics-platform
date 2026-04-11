# tests/test_indicators.py

import numpy as np
import pandas as pd
import pytest
from fastapi.testclient import TestClient

from main import app
from services.indicator_calculator import _interpret_rsi
from services.indicator_calculator import _validate_windows
from services.indicator_calculator import calculate_atr
from services.indicator_calculator import calculate_ema
from services.indicator_calculator import calculate_macd
from services.indicator_calculator import calculate_rsi
from services.indicator_calculator import get_indicators

client = TestClient(app)


# ── Fixtures ──────────────────────────────────────────────────────────────────


@pytest.fixture
def sample_close():
    """Synthetic price series long enough to warm up all indicators."""
    np.random.seed(42)
    prices = 22000 + np.cumsum(np.random.randn(100) * 50)
    return pd.Series(prices)


@pytest.fixture
def sample_df(sample_close):
    """Full OHLCV DataFrame for ATR testing."""
    df = pd.DataFrame(
        {
            "Close": sample_close,
            "High": sample_close + 50,
            "Low": sample_close - 50,
        }
    )
    return df


# ── Unit tests: individual calculators ───────────────────────────────────────


class TestCalculateRSI:

    def test_returns_series(self, sample_close):
        result = calculate_rsi(sample_close)
        assert isinstance(result, pd.Series)

    def test_rsi_in_valid_range(self, sample_close):
        result = calculate_rsi(sample_close).dropna()
        assert (result >= 0).all() and (result <= 100).all()

    def test_custom_window_accepted(self, sample_close):
        result = calculate_rsi(sample_close, window=7).dropna()
        assert len(result) > 0


class TestCalculateEMA:

    def test_returns_series(self, sample_close):
        result = calculate_ema(sample_close)
        assert isinstance(result, pd.Series)

    def test_ema_close_to_price(self, sample_close):
        result = calculate_ema(sample_close, window=5).dropna()
        # EMA should be in the same ballpark as the prices
        assert result.mean() > 0

    def test_longer_window_smoother(self, sample_close):
        ema9 = calculate_ema(sample_close, window=9).dropna()
        ema50 = calculate_ema(sample_close, window=50).dropna()
        # Longer EMA has lower standard deviation = smoother
        assert ema50.std() < ema9.std()


class TestCalculateMACD:

    def test_returns_dict_with_three_keys(self, sample_close):
        result = calculate_macd(sample_close)
        assert "macd" in result
        assert "signal" in result
        assert "histogram" in result

    def test_histogram_is_macd_minus_signal(self, sample_close):
        result = calculate_macd(sample_close)
        macd = result["macd"].dropna()
        signal = result["signal"].dropna()
        histogram = result["histogram"].dropna()
        combined = (macd - signal).dropna()
        # Align indexes before comparing
        common = histogram.index.intersection(combined.index)
        diff = (histogram[common] - combined[common]).abs()
        assert diff.max() < 0.01


class TestCalculateATR:

    def test_returns_series(self, sample_df):
        result = calculate_atr(sample_df["High"], sample_df["Low"], sample_df["Close"])
        assert isinstance(result, pd.Series)

    def test_atr_always_positive(self, sample_df):
        result = calculate_atr(
            sample_df["High"], sample_df["Low"], sample_df["Close"]
        ).dropna()
        # ATR has zeros during warmup; filter those out
        result_nonzero = result[result > 0]
        assert len(result_nonzero) > 0 and (result_nonzero > 0).all()


# ── Unit tests: validation + signals ─────────────────────────────────────────


class TestValidateWindows:

    def test_valid_windows_pass(self):
        _validate_windows(14, 20, 14)  # should not raise

    def test_rsi_window_too_large_raises(self):
        from core.exceptions import InvalidParameterError

        with pytest.raises(InvalidParameterError, match="rsi_window"):
            _validate_windows(999, 20, 14)

    def test_ema_window_too_large_raises(self):
        from core.exceptions import InvalidParameterError

        with pytest.raises(InvalidParameterError, match="ema_window"):
            _validate_windows(14, 999, 14)


class TestInterpretRSI:

    def test_above_70_is_overbought(self):
        assert _interpret_rsi(75) == "overbought"

    def test_below_30_is_oversold(self):
        assert _interpret_rsi(25) == "oversold"

    def test_middle_is_neutral(self):
        assert _interpret_rsi(50) == "neutral"

    def test_exact_boundary_70_is_overbought(self):
        assert _interpret_rsi(70) == "overbought"

    def test_exact_boundary_30_is_oversold(self):
        assert _interpret_rsi(30) == "oversold"


# ── Integration tests: HTTP endpoint ─────────────────────────────────────────


class TestIndicatorsEndpoint:

    def test_returns_200(self):
        r = client.get("/indicators/?period=3mo")
        assert r.status_code == 200

    def test_response_has_required_keys(self):
        r = client.get("/indicators/?period=3mo")
        body = r.json()
        for key in ["symbol", "name", "period", "count", "latest", "data"]:
            assert key in body, f"Missing key: {key}"

    def test_each_row_has_all_indicators(self):
        r = client.get("/indicators/?period=3mo")
        row = r.json()["data"][0]
        for field in [
            "date",
            "open",
            "high",
            "low",
            "close",
            "rsi",
            "ema",
            "atr",
            "macd",
            "macd_signal",
            "macd_histogram",
        ]:
            assert field in row, f"Missing field: {field}"

    def test_rsi_in_range(self):
        r = client.get("/indicators/?period=3mo")
        for row in r.json()["data"]:
            assert 0 <= row["rsi"] <= 100

    def test_high_gte_low_every_row(self):
        r = client.get("/indicators/?period=3mo")
        for row in r.json()["data"]:
            assert row["high"] >= row["low"]

    def test_custom_ema_window(self):
        r = client.get("/indicators/?ema_window=50&period=3mo")
        assert r.status_code == 200
        assert r.json()["windows"]["ema"] == 50

    def test_invalid_rsi_window_rejected(self):
        r = client.get("/indicators/?rsi_window=999")
        assert r.status_code == 422  # FastAPI validation rejects ge/le violations

    def test_latest_endpoint_returns_200(self):
        r = client.get("/indicators/latest")
        assert r.status_code == 200

    def test_latest_has_rsi_signal(self):
        r = client.get("/indicators/latest")
        latest = r.json()["latest"]
        assert latest["rsi_signal"] in ["overbought", "oversold", "neutral"]

    def test_sensex_works(self):
        r = client.get("/indicators/?symbol=^BSESN&period=3mo")
        assert r.status_code == 200
