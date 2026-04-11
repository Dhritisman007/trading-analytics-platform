# services/news/sentiment_analyzer.py

import re
import logging
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from utils.formatters import format_number

logger = logging.getLogger(__name__)

# Single analyzer instance — expensive to create, reuse it
_analyzer = SentimentIntensityAnalyzer()

# Financial domain booster words — VADER doesn't know these
# Positive booster: words that signal good news for markets
# Negative booster: words that signal bad news for markets
FINANCIAL_BOOSTERS = {
    # Strong positive signals
    "rally":           2.0,
    "bullish":         2.0,
    "surge":           1.8,
    "outperform":      1.5,
    "breakout":        1.5,
    "all-time high":   2.5,
    "record high":     2.0,
    "beat estimates":  1.8,
    "rate cut":        1.5,
    "stimulus":        1.5,
    "dividend":        1.2,
    "upgrade":         1.5,

    # Strong negative signals
    "crash":          -2.5,
    "bearish":        -2.0,
    "plunge":         -2.0,
    "recession":      -2.0,
    "downgrade":      -1.5,
    "miss estimates": -1.8,
    "rate hike":      -1.2,
    "outflow":        -1.5,
    "default":        -2.5,
    "ban":            -1.8,
    "penalty":        -1.5,
    "fraud":          -2.5,
    "scam":           -2.5,
}

# Add financial boosters to VADER's lexicon
for word, score in FINANCIAL_BOOSTERS.items():
    _analyzer.lexicon[word] = score


def analyze_sentiment(text: str) -> dict:
    """
    Score the sentiment of a news headline or article snippet.

    Args:
        text: headline or short text to analyze

    Returns:
        dict with compound score, label, and individual pos/neg/neu scores
    """
    if not text or not text.strip():
        return {
            "compound":  0.0,
            "positive":  0.0,
            "negative":  0.0,
            "neutral":   1.0,
            "label":     "neutral",
            "color":     "#888780",
            "emoji":     "—",
        }

    # Clean text slightly — remove HTML tags, extra whitespace
    clean_text = re.sub(r"<[^>]+>", "", text).strip()

    scores = _analyzer.polarity_scores(clean_text)
    compound = scores["compound"]

    # Classification thresholds — tuned for financial news
    if compound >= 0.15:
        label = "positive"
        color = "#1D9E75"
        emoji = "↑"
    elif compound <= -0.15:
        label = "negative"
        color = "#E24B4A"
        emoji = "↓"
    else:
        label = "neutral"
        color = "#888780"
        emoji = "—"

    return {
        "compound": format_number(compound, 4),
        "positive": format_number(scores["pos"], 4),
        "negative": format_number(scores["neg"], 4),
        "neutral":  format_number(scores["neu"], 4),
        "label":    label,
        "color":    color,
        "emoji":    emoji,
    }


def analyze_batch(texts: list[str]) -> dict:
    """
    Analyze a batch of headlines and return aggregate market mood.
    Used to compute the overall sentiment score for the news panel header.
    """
    if not texts:
        return {
            "overall_score":  0.0,
            "overall_label":  "neutral",
            "overall_color":  "#888780",
            "positive_count": 0,
            "negative_count": 0,
            "neutral_count":  0,
            "total":          0,
        }

    scores     = [_analyzer.polarity_scores(t)["compound"] for t in texts]
    avg_score  = sum(scores) / len(scores)

    positive   = sum(1 for s in scores if s >= 0.15)
    negative   = sum(1 for s in scores if s <= -0.15)
    neutral    = len(scores) - positive - negative

    if avg_score >= 0.15:
        label = "positive"
        color = "#1D9E75"
    elif avg_score <= -0.15:
        label = "negative"
        color = "#E24B4A"
    else:
        label = "neutral"
        color = "#888780"

    return {
        "overall_score":  format_number(avg_score, 4),
        "overall_label":  label,
        "overall_color":  color,
        "positive_count": positive,
        "negative_count": negative,
        "neutral_count":  neutral,
        "total":          len(scores),
        "sentiment_distribution": {
            "positive_pct": format_number(positive / len(scores) * 100),
            "negative_pct": format_number(negative / len(scores) * 100),
            "neutral_pct":  format_number(neutral  / len(scores) * 100),
        },
    }


def estimate_market_impact(
    sentiment_score: float,
    keywords: list[str],
) -> dict:
    """
    Estimate how strongly this news might impact the market.
    Combines sentiment strength with keyword importance.
    """
    # High-impact financial keywords
    high_impact = {
        "rbi", "budget", "gdp", "inflation", "repo rate",
        "sebi", "ipo", "fii", "dii", "nifty", "sensex",
        "federal reserve", "fed", "recession", "earnings",
    }

    matched = [k for k in keywords if k.lower() in high_impact]
    keyword_boost = min(len(matched) * 0.1, 0.3)

    abs_score  = abs(sentiment_score)
    raw_impact = abs_score + keyword_boost

    if raw_impact >= 0.6:
        impact = "HIGH"
        color  = "#E24B4A" if sentiment_score < 0 else "#1D9E75"
    elif raw_impact >= 0.3:
        impact = "MEDIUM"
        color  = "#BA7517"
    else:
        impact = "LOW"
        color  = "#888780"

    return {
        "impact":           impact,
        "impact_color":     color,
        "impact_score":     format_number(raw_impact, 3),
        "high_impact_keywords": matched,
    }