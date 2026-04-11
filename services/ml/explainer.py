# services/ml/explainer.py

import numpy as np
import pandas as pd
import logging
from services.ml.feature_engineer import FEATURE_COLUMNS

logger = logging.getLogger(__name__)

# Plain-English labels for each feature — shown in the dashboard
FEATURE_LABELS = {
    # Normalized Indicators
    "rsi_norm":             "RSI normalized value",
    "macd_hist_norm":       "MACD histogram strength",
    "atr_pct":              "Volatility (ATR %)",
    
    # Price Action
    "price_ema_ratio":      "Price vs EMA distance",
    "return_1d":            "Today's price return",
    "return_5d":            "5-day price momentum",
    "return_20d":           "20-day price momentum",
    "volume_ratio":         "Volume vs 20-day average",
    
    # Binary Flags
    "rsi_overbought":       "RSI overbought signal",
    "rsi_oversold":         "RSI oversold signal",
    "above_ema":            "Price above EMA",
    "macd_positive":        "MACD positive zone",
    "macd_crossover":       "MACD bullish crossover",
    
    # Volatility
    "volatility_20d":       "20-day volatility",
    "high_low_ratio":       "Daily range ratio",
    
    # Momentum
    "rsi_slope":            "RSI trend direction",
    "macd_slope":           "MACD trend direction",
    
    # Trend
    "consecutive_up":       "Consecutive up days",
    "consecutive_down":     "Consecutive down days",
    
    # VWAP & Price Position
    "distance_from_vwap":   "Price vs VWAP distance",
    
    # EMA Trend
    "ema_slope_20d":        "20-day EMA slope",
    
    # Multi-timeframe
    "close_above_200ma":    "Price above 200-day MA",
    "volume_spike":         "Volume spike detected",
    
    # RSI Divergence
    "rsi_divergence":       "RSI divergence signal",
    
    # Additional Features
    "macd_histogram_slope": "MACD histogram slope",
    "atr_ratio":            "ATR vs 20-day average",
    "true_range_norm":      "True range normalized",
    "price_momentum":       "Price momentum (5-day MA)",
    "volume_momentum":      "Volume momentum indicator",
}

# Feature categories for grouping in the dashboard
FEATURE_CATEGORIES = {
    "Indicators": [
        "rsi_norm", "macd_hist_norm", "atr_pct"
    ],
    "Price Action": [
        "price_ema_ratio", "return_1d", "return_5d", "return_20d", "volume_ratio"
    ],
    "Signals": [
        "rsi_overbought", "rsi_oversold", "above_ema", "macd_positive", "macd_crossover"
    ],
    "Volatility": [
        "volatility_20d", "high_low_ratio"
    ],
    "Momentum": [
        "rsi_slope", "macd_slope"
    ],
    "Trends": [
        "consecutive_up", "consecutive_down"
    ],
    "Price Position": [
        "distance_from_vwap", "ema_slope_20d", "close_above_200ma", "volume_spike"
    ],
    "Advanced": [
        "rsi_divergence", "macd_histogram_slope", "atr_ratio", "true_range_norm",
        "price_momentum", "volume_momentum"
    ],
}


def compute_feature_contributions(
    model,
    scaler,
    latest_row: pd.Series,
    signal: str,
) -> list[dict]:
    """
    Compute how much each feature contributed to the final prediction.

    Method: feature_importance × normalised_feature_value × signal_direction
    This approximates SHAP values using Random Forest internals.

    Returns a list of contribution dicts, sorted by absolute impact.
    """
    feature_values = latest_row[FEATURE_COLUMNS].values
    scaled_values  = scaler.transform(feature_values.reshape(1, -1))[0]
    importances    = model.feature_importances_

    contributions = []
    signal_dir    = 1 if signal == "BUY" else -1

    for i, feature in enumerate(FEATURE_COLUMNS):
        importance   = float(importances[i])
        scaled_val   = float(scaled_values[i])
        raw_val      = float(feature_values[i])

        # Contribution = how much this feature pushed toward the signal
        # Positive = pushes toward BUY, Negative = pushes toward SELL
        contribution = importance * scaled_val * signal_dir

        contributions.append({
            "feature":      feature,
            "label":        FEATURE_LABELS.get(feature, feature),
            "category":     _get_category(feature),
            "importance":   round(importance, 4),
            "raw_value":    round(raw_val, 4),
            "contribution": round(contribution, 4),
            "direction":    "bullish" if contribution > 0 else "bearish",
            "magnitude":    round(abs(contribution), 4),
        })

    # Sort by absolute magnitude — most impactful first
    contributions.sort(key=lambda x: x["magnitude"], reverse=True)
    return contributions


def _get_category(feature: str) -> str:
    """Return the category name for a given feature."""
    for category, features in FEATURE_CATEGORIES.items():
        if feature in features:
            return category
    return "Other"


def get_category_summary(contributions: list[dict]) -> dict:
    """
    Aggregate contributions by category.
    Shows which indicator group (RSI, MACD, EMA etc.) had most impact.
    This is what powers the category breakdown chart in the dashboard.
    """
    summary = {}
    for cat in FEATURE_CATEGORIES:
        cat_contribs = [c for c in contributions if c["category"] == cat]
        if cat_contribs:
            total_impact    = sum(c["magnitude"]    for c in cat_contribs)
            total_contrib   = sum(c["contribution"] for c in cat_contribs)
            summary[cat] = {
                "total_impact":   round(total_impact,  4),
                "net_direction":  "bullish" if total_contrib > 0 else "bearish",
                "feature_count":  len(cat_contribs),
                "top_feature":    cat_contribs[0]["label"],
            }

    # Sort by total impact
    return dict(sorted(summary.items(), key=lambda x: x[1]["total_impact"], reverse=True))


def build_chart_data(contributions: list[dict], top_n: int = 10) -> dict:
    """
    Build chart-ready arrays for the React dashboard.
    Returns parallel arrays that map directly to a horizontal bar chart.
    """
    top = contributions[:top_n]
    return {
        "labels":        [c["label"]        for c in top],
        "importances":   [c["importance"]   for c in top],
        "contributions": [c["contribution"] for c in top],
        "directions":    [c["direction"]    for c in top],
        "categories":    [c["category"]     for c in top],
        "colors": [
            "#1D9E75" if c["direction"] == "bullish" else "#E24B4A"
            for c in top
        ],
    }


def generate_beginner_explanation(
    contributions: list[dict],
    signal: str,
    confidence: float,
    category_summary: dict,
) -> dict:
    """
    Generate multiple levels of explanation for different audiences.

    - one_line:  a single sentence summary
    - simple:    beginner-friendly paragraph
    - technical: detailed breakdown for experienced users
    """
    top3     = contributions[:3]
    top_cat  = list(category_summary.keys())[0] if category_summary else "indicators"
    bullish  = [c for c in top3 if c["direction"] == "bullish"]
    bearish  = [c for c in top3 if c["direction"] == "bearish"]

    # One-line summary
    one_line = (
        f"Model signals {signal} with {confidence}% confidence, "
        f"driven mainly by {top_cat} indicators."
    )

    # Simple explanation — no jargon
    simple_parts = []
    for c in top3:
        label = c["label"]
        direction = c["direction"]
        if direction == "bullish":
            simple_parts.append(f"{label} is showing a positive reading")
        else:
            simple_parts.append(f"{label} is showing a negative reading")

    simple = (
        f"The model looked at {len(FEATURE_COLUMNS)} technical signals and found that "
        f"{', '.join(simple_parts[:2])}. "
        f"Together these point toward a {signal} signal."
    )

    # Technical explanation — for developers / traders
    tech_parts = [
        f"{c['label']} (importance: {c['importance']:.3f}, "
        f"contribution: {c['contribution']:+.4f})"
        for c in top3
    ]
    technical = (
        f"Random Forest prediction based on {len(FEATURE_COLUMNS)} features. "
        f"Top contributors: {'; '.join(tech_parts)}. "
        f"Dominant category: {top_cat}."
    )

    return {
        "one_line":  one_line,
        "simple":    simple,
        "technical": technical,
    }