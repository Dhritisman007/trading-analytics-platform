# tests/test_news.py

import pytest
from fastapi.testclient import TestClient
from main import app
from services.news.sentiment_analyzer import (
    analyze_sentiment,
    analyze_batch,
    estimate_market_impact,
)

client = TestClient(app)


# ── Sentiment analyzer unit tests ─────────────────────────────────────────────

class TestSentimentAnalyzer:

    def test_positive_headline_scores_positive(self):
        result = analyze_sentiment("Nifty hits all-time high, markets rally strongly")
        assert result["label"] == "positive"
        assert float(result["compound"]) > 0.15

    def test_negative_headline_scores_negative(self):
        result = analyze_sentiment("Markets crash on recession fears, Sensex plunges 1000 points")
        assert result["label"] == "negative"
        assert float(result["compound"]) < -0.15

    def test_neutral_headline_scores_neutral(self):
        result = analyze_sentiment("Markets close flat, volumes moderate on expiry day")
        assert result["label"] in ["neutral", "positive", "negative"]

    def test_empty_text_returns_neutral(self):
        result = analyze_sentiment("")
        assert result["label"] == "neutral"
        assert result["compound"] == 0.0

    def test_result_has_required_keys(self):
        result = analyze_sentiment("Nifty gains 100 points")
        for key in ["compound", "positive", "negative", "neutral", "label", "color", "emoji"]:
            assert key in result

    def test_compound_in_valid_range(self):
        result = analyze_sentiment("Stock market news today")
        assert -1.0 <= float(result["compound"]) <= 1.0

    def test_positive_label_has_green_color(self):
        result = analyze_sentiment("Markets rally, Nifty surges to record")
        if result["label"] == "positive":
            assert result["color"] == "#1D9E75"

    def test_negative_label_has_red_color(self):
        result = analyze_sentiment("Markets crash, Sensex plunges 2000 points")
        if result["label"] == "negative":
            assert result["color"] == "#E24B4A"

    def test_financial_boosters_applied(self):
        # "crash" is in our financial boosters with -2.5
        crash = analyze_sentiment("Markets crash today")
        normal = analyze_sentiment("Markets decline today")
        assert float(crash["compound"]) <= float(normal["compound"])


class TestBatchAnalysis:

    def test_empty_batch_returns_neutral(self):
        result = analyze_batch([])
        assert result["overall_label"] == "neutral"
        assert result["total"] == 0

    def test_batch_counts_correct(self):
        headlines = [
            "Nifty surges to record high",
            "Markets fall on recession fears",
            "Trading volumes remain moderate",
        ]
        result = analyze_batch(headlines)
        assert result["total"] == 3
        assert result["positive_count"] + result["negative_count"] + result["neutral_count"] == 3

    def test_all_positive_gives_positive_mood(self):
        headlines = [
            "Nifty hits all-time high rally",
            "Markets surge on rate cut hopes",
            "Sensex jumps 500 points bullish run",
        ]
        result = analyze_batch(headlines)
        assert result["overall_label"] == "positive"

    def test_distribution_sums_to_100(self):
        headlines = ["Nifty up", "Sensex down", "Markets flat"]
        result = analyze_batch(headlines)
        dist = result["sentiment_distribution"]
        total = (
            float(dist["positive_pct"]) +
            float(dist["negative_pct"]) +
            float(dist["neutral_pct"])
        )
        assert abs(total - 100.0) < 1.0


class TestMarketImpact:

    def test_high_impact_for_rbi_news(self):
        result = estimate_market_impact(0.8, ["rbi", "repo rate"])
        assert result["impact"] == "HIGH"

    def test_low_impact_for_generic_news(self):
        result = estimate_market_impact(0.1, ["company", "product"])
        assert result["impact"] == "LOW"

    def test_high_impact_keywords_extracted(self):
        result = estimate_market_impact(0.5, ["rbi", "budget", "sebi", "product"])
        assert "rbi" in result["high_impact_keywords"]
        assert "budget" in result["high_impact_keywords"]

    def test_impact_has_required_keys(self):
        result = estimate_market_impact(0.5, ["nifty"])
        for key in ["impact", "impact_color", "impact_score", "high_impact_keywords"]:
            assert key in result


# ── HTTP endpoint tests ───────────────────────────────────────────────────────

class TestNewsEndpoints:

    def test_news_endpoint_returns_200(self):
        r = client.get("/news/")
        assert r.status_code == 200

    def test_response_has_required_keys(self):
        r = client.get("/news/")
        body = r.json()
        for key in ["articles", "market_mood", "total_available",
                    "returned", "topic_distribution"]:
            assert key in body

    def test_articles_is_list(self):
        r = client.get("/news/")
        assert isinstance(r.json()["articles"], list)

    def test_each_article_has_sentiment(self):
        r = client.get("/news/")
        for article in r.json()["articles"][:5]:
            assert "sentiment" in article
            assert "label" in article["sentiment"]

    def test_each_article_has_impact(self):
        r = client.get("/news/")
        for article in r.json()["articles"][:5]:
            assert "impact" in article
            assert article["impact"]["impact"] in ["HIGH", "MEDIUM", "LOW"]

    def test_sentiment_filter_positive(self):
        r = client.get("/news/?sentiment=positive")
        assert r.status_code == 200
        for article in r.json()["articles"]:
            assert article["sentiment"]["label"] == "positive"

    def test_sentiment_filter_negative(self):
        r = client.get("/news/?sentiment=negative")
        assert r.status_code == 200
        for article in r.json()["articles"]:
            assert article["sentiment"]["label"] == "negative"

    def test_invalid_sentiment_returns_400(self):
        r = client.get("/news/?sentiment=amazing")
        assert r.status_code == 400

    def test_invalid_topic_returns_400(self):
        r = client.get("/news/?topic=invalid_xyz")
        assert r.status_code == 400

    def test_limit_respected(self):
        r = client.get("/news/?limit=5")
        assert r.status_code == 200
        assert len(r.json()["articles"]) <= 5

    def test_mood_endpoint_returns_200(self):
        r = client.get("/news/mood")
        assert r.status_code == 200

    def test_mood_has_market_mood(self):
        r = client.get("/news/mood")
        assert "market_mood" in r.json()
        assert "overall_label" in r.json()["market_mood"]

    def test_breaking_endpoint_returns_200(self):
        r = client.get("/news/breaking")
        assert r.status_code == 200

    def test_topics_endpoint_returns_list(self):
        r = client.get("/news/topics")
        assert r.status_code == 200
        assert "topics" in r.json()
        assert len(r.json()["topics"]) == 9

    def test_refresh_endpoint_returns_200(self):
        r = client.post("/news/refresh")
        assert r.status_code == 200
        assert r.json()["status"] == "refreshed"

    def test_market_mood_label_valid(self):
        r = client.get("/news/mood")
        label = r.json()["market_mood"]["overall_label"]
        assert label in ["positive", "negative", "neutral"]