# tests/test_predict.py

import pytest
import pandas as pd
import numpy as np
from fastapi.testclient import TestClient
from main import app
from services.ml.feature_engineer import build_features, FEATURE_COLUMNS
from services.ml.model_trainer import train_model, model_exists

client = TestClient(app)


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture
def sample_df():
    """Minimal OHLCV + indicator DataFrame for feature engineering tests."""
    np.random.seed(42)
    n = 120
    close = 22000 + np.cumsum(np.random.randn(n) * 50)
    df = pd.DataFrame({
        "open":           close - np.random.rand(n) * 20,
        "high":           close + np.random.rand(n) * 40,
        "low":            close - np.random.rand(n) * 40,
        "close":          close,
        "volume":         np.random.randint(1_000_000, 5_000_000, n),
        "RSI":            np.random.uniform(30, 70, n),
        "EMA":            close * np.random.uniform(0.98, 1.02, n),
        "ATR":            np.random.uniform(80, 200, n),
        "MACD":           np.random.uniform(-50, 50, n),
        "MACD_Signal":    np.random.uniform(-40, 40, n),
        "MACD_Histogram": np.random.uniform(-30, 30, n),
    }, index=pd.date_range("2023-01-01", periods=n, freq="B"))
    return df


# ── Feature engineering tests ─────────────────────────────────────────────────

class TestFeatureEngineer:

    def test_returns_dataframe(self, sample_df):
        result = build_features(sample_df)
        assert isinstance(result, pd.DataFrame)

    def test_all_feature_columns_present(self, sample_df):
        result = build_features(sample_df)
        for col in FEATURE_COLUMNS:
            assert col in result.columns, f"Missing feature: {col}"

    def test_target_column_present(self, sample_df):
        result = build_features(sample_df)
        assert "target" in result.columns

    def test_target_is_binary(self, sample_df):
        result = build_features(sample_df)
        assert set(result["target"].unique()).issubset({0, 1})

    def test_no_nan_after_dropna(self, sample_df):
        result = build_features(sample_df)
        assert not result[FEATURE_COLUMNS].isna().any().any()

    def test_rsi_norm_between_0_and_1(self, sample_df):
        result = build_features(sample_df)
        assert (result["rsi_norm"] >= 0).all()
        assert (result["rsi_norm"] <= 1).all()

    def test_binary_flags_are_0_or_1(self, sample_df):
        result = build_features(sample_df)
        for col in ["rsi_overbought", "rsi_oversold", "above_ema", "macd_positive"]:
            assert set(result[col].unique()).issubset({0, 1}), \
                f"{col} has non-binary values"

    def test_fewer_rows_after_feature_engineering(self, sample_df):
        result = build_features(sample_df)
        assert len(result) < len(sample_df)

    def test_feature_count_matches_expected(self, sample_df):
        result = build_features(sample_df)
        assert len(FEATURE_COLUMNS) == 29


# ── Prediction endpoint tests ─────────────────────────────────────────────────

class TestPredictEndpoint:

    def test_predict_returns_200(self):
        r = client.get("/predict/?auto_train=true")
        assert r.status_code == 200

    def test_response_has_required_keys(self):
        r = client.get("/predict/")
        body = r.json()
        # New response format has different keys
        for key in ["symbol", "signal", "confidence",
                    "probabilities", "explanation",
                    "contributions", "market_context"]:
            assert key in body, f"Missing key: {key}"

    def test_signal_is_buy_or_sell(self):
        r = client.get("/predict/")
        assert r.json()["signal"] in ["BUY", "SELL"]

    def test_confidence_between_50_and_100(self):
        r = client.get("/predict/")
        confidence = r.json()["confidence"]
        assert 50 <= confidence <= 100

    def test_probabilities_sum_to_100(self):
        r = client.get("/predict/")
        probs = r.json()["probabilities"]
        total = probs["buy"] + probs["sell"]
        assert abs(total - 100) < 1.0

    def test_top_features_not_empty(self):
        r = client.get("/predict/")
        # New response format uses "contributions" instead of "top_features"
        assert len(r.json()["contributions"]) > 0

    def test_explanation_is_string(self):
        r = client.get("/predict/")
        # New format: explanation is dict with one_line, simple, technical
        explanation = r.json()["explanation"]
        assert isinstance(explanation, dict)
        assert "one_line" in explanation
        assert isinstance(explanation["one_line"], str)
        assert len(explanation["one_line"]) > 10

    def test_disclaimer_present(self):
        r = client.get("/predict/")
        assert "educational" in r.json()["disclaimer"].lower()

    def test_model_status_endpoint(self):
        r = client.get("/predict/status")
        assert r.status_code == 200
        assert "trained" in r.json()

    def test_model_status_shows_trained_after_predict(self):
        client.get("/predict/")  # ensure trained
        r = client.get("/predict/status")
        assert r.json()["trained"] is True

    def test_model_info_has_accuracy(self):
        r = client.get("/predict/")
        assert "accuracy" in r.json()["model_info"]

    def test_market_context_has_rsi(self):
        r = client.get("/predict/")
        assert "rsi" in r.json()["market_context"]

    def test_signal_confidence_sum_with_probabilities(self):
        """Test that confidence matches the higher probability."""
        r = client.get("/predict/")
        body = r.json()
        confidence = body["confidence"]
        max_prob = max(body["probabilities"]["buy"], body["probabilities"]["sell"])
        assert confidence == max_prob

    def test_top_features_have_numeric_values(self):
        """Test that contributions have numeric importance scores."""
        r = client.get("/predict/")
        contributions = r.json()["contributions"]
        for contrib in contributions:
            assert "importance" in contrib
            assert isinstance(contrib["importance"], (int, float))
            assert contrib["importance"] >= 0

    def test_prediction_response_includes_symbol_and_name(self):
        """Test that response includes symbol and friendly name."""
        r = client.get("/predict/?symbol=^BSESN")
        body = r.json()
        assert body["symbol"] == "^BSESN"
        assert body["name"]  # Should have a name
        assert len(body["name"]) > 0