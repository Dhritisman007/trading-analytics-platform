# tests/test_explainer.py

import pytest
import numpy as np
import pandas as pd
from fastapi.testclient import TestClient
from main import app
from services.ml.explainer import (
    compute_feature_contributions,
    get_category_summary,
    build_chart_data,
    generate_beginner_explanation,
    FEATURE_LABELS,
    FEATURE_CATEGORIES,
)
from services.ml.feature_engineer import FEATURE_COLUMNS
from services.ml.performance_tracker import (
    record_prediction,
    get_performance_summary,
)

client = TestClient(app)


# ── Feature labels coverage ───────────────────────────────────────────────────

class TestFeatureLabels:

    def test_all_features_have_labels(self):
        for feature in FEATURE_COLUMNS:
            assert feature in FEATURE_LABELS, \
                f"Feature '{feature}' has no human-readable label"

    def test_all_features_have_categories(self):
        all_categorised = []
        for features in FEATURE_CATEGORIES.values():
            all_categorised.extend(features)
        for feature in FEATURE_COLUMNS:
            assert feature in all_categorised, \
                f"Feature '{feature}' has no category"


# ── Contribution computation ──────────────────────────────────────────────────

class TestContributions:

    @pytest.fixture
    def mock_model_scaler(self):
        """Create a minimal mock model and scaler for testing."""
        from sklearn.ensemble import RandomForestClassifier
        from sklearn.preprocessing import StandardScaler
        import numpy as np

        n_features = len(FEATURE_COLUMNS)
        X = np.random.randn(100, n_features)
        y = (np.random.randn(100) > 0).astype(int)

        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)

        model = RandomForestClassifier(n_estimators=10, random_state=42)
        model.fit(X_scaled, y)

        return model, scaler

    def test_contributions_length_matches_features(self, mock_model_scaler):
        model, scaler = mock_model_scaler
        latest = pd.Series(
            np.random.randn(len(FEATURE_COLUMNS)),
            index=FEATURE_COLUMNS
        )
        result = compute_feature_contributions(model, scaler, latest, "BUY")
        assert len(result) == len(FEATURE_COLUMNS)

    def test_each_contribution_has_required_keys(self, mock_model_scaler):
        model, scaler = mock_model_scaler
        latest = pd.Series(
            np.random.randn(len(FEATURE_COLUMNS)),
            index=FEATURE_COLUMNS
        )
        result = compute_feature_contributions(model, scaler, latest, "BUY")
        for c in result:
            for key in ["feature", "label", "category", "importance",
                        "contribution", "direction", "magnitude"]:
                assert key in c, f"Missing key: {key}"

    def test_direction_is_bullish_or_bearish(self, mock_model_scaler):
        model, scaler = mock_model_scaler
        latest = pd.Series(
            np.random.randn(len(FEATURE_COLUMNS)),
            index=FEATURE_COLUMNS
        )
        result = compute_feature_contributions(model, scaler, latest, "BUY")
        for c in result:
            assert c["direction"] in ["bullish", "bearish"]

    def test_sorted_by_magnitude_descending(self, mock_model_scaler):
        model, scaler = mock_model_scaler
        latest = pd.Series(
            np.random.randn(len(FEATURE_COLUMNS)),
            index=FEATURE_COLUMNS
        )
        result = compute_feature_contributions(model, scaler, latest, "BUY")
        magnitudes = [c["magnitude"] for c in result]
        assert magnitudes == sorted(magnitudes, reverse=True)


# ── Chart data ────────────────────────────────────────────────────────────────

class TestChartData:

    def _sample_contributions(self):
        return [
            {
                "label": f"Feature {i}", "importance": 0.1,
                "contribution": 0.05 if i % 2 == 0 else -0.03,
                "direction": "bullish" if i % 2 == 0 else "bearish",
                "category": "RSI", "magnitude": 0.05,
                "feature": FEATURE_COLUMNS[i], "raw_value": 0.5,
            }
            for i in range(15)
        ]

    def test_chart_data_has_required_keys(self):
        chart = build_chart_data(self._sample_contributions(), top_n=10)
        for key in ["labels", "importances", "contributions", "directions", "colors"]:
            assert key in chart

    def test_chart_data_length_matches_top_n(self):
        chart = build_chart_data(self._sample_contributions(), top_n=5)
        assert len(chart["labels"]) == 5

    def test_colors_are_green_or_red(self):
        chart = build_chart_data(self._sample_contributions())
        for color in chart["colors"]:
            assert color in ["#1D9E75", "#E24B4A"]


# ── Explanation generation ────────────────────────────────────────────────────

class TestExplanationGeneration:

    def _sample_data(self):
        contributions = [
            {
                "label": "RSI value", "direction": "bullish",
                "magnitude": 0.08, "contribution": 0.08,
                "feature": "rsi_norm", "importance": 0.1,
                "raw_value": 0.6, "category": "RSI",
            },
            {
                "label": "Price vs EMA distance", "direction": "bullish",
                "magnitude": 0.06, "contribution": 0.06,
                "feature": "price_ema_ratio", "importance": 0.09,
                "raw_value": 1.2, "category": "EMA",
            },
        ]
        category_summary = {
            "RSI": {"total_impact": 0.12, "net_direction": "bullish",
                    "top_feature": "RSI value", "feature_count": 1},
        }
        return contributions, category_summary

    def test_explanation_has_three_levels(self):
        contribs, cat = self._sample_data()
        result = generate_beginner_explanation(contribs, "BUY", 65.0, cat)
        for key in ["one_line", "simple", "technical"]:
            assert key in result

    def test_one_line_mentions_signal(self):
        contribs, cat = self._sample_data()
        result = generate_beginner_explanation(contribs, "BUY", 65.0, cat)
        assert "BUY" in result["one_line"]

    def test_one_line_mentions_confidence(self):
        contribs, cat = self._sample_data()
        result = generate_beginner_explanation(contribs, "BUY", 65.0, cat)
        assert "65.0" in result["one_line"]

    def test_technical_mentions_feature_count(self):
        contribs, cat = self._sample_data()
        result = generate_beginner_explanation(contribs, "BUY", 65.0, cat)
        assert "29" in result["technical"]


# ── Performance tracker ───────────────────────────────────────────────────────

class TestPerformanceTracker:

    def test_record_and_retrieve(self):
        record_prediction("^NSEI", "BUY", 65.0, 23000.0)
        summary = get_performance_summary("^NSEI")
        assert summary["total_predictions"] >= 1

    def test_summary_has_required_keys(self):
        summary = get_performance_summary()
        for key in ["total_predictions", "evaluated", "pending",
                    "correct", "incorrect", "real_accuracy"]:
            assert key in summary


# ── Full endpoint tests ───────────────────────────────────────────────────────

class TestPredictEndpointDay9:

    def test_explanation_has_three_levels(self):
        r = client.get("/predict/")
        assert r.status_code == 200
        expl = r.json()["explanation"]
        for level in ["one_line", "simple", "technical"]:
            assert level in expl

    def test_category_summary_present(self):
        r = client.get("/predict/")
        assert "category_summary" in r.json()
        assert len(r.json()["category_summary"]) > 0

    def test_chart_data_present_with_arrays(self):
        r = client.get("/predict/")
        chart = r.json()["chart_data"]
        assert "labels"      in chart
        assert "importances" in chart
        assert "colors"      in chart

    def test_strength_field_valid(self):
        r = client.get("/predict/")
        assert r.json()["strength"] in ["strong", "moderate", "weak"]

    def test_color_field_is_hex(self):
        r = client.get("/predict/")
        color = r.json()["color"]
        assert color.startswith("#")

    def test_contributions_list_not_empty(self):
        r = client.get("/predict/")
        assert len(r.json()["contributions"]) > 0

    def test_performance_endpoint(self):
        r = client.get("/predict/performance")
        assert r.status_code == 200

    def test_compare_endpoint(self):
        r = client.get("/predict/compare")
        assert r.status_code == 200
        assert "symbols" in r.json()