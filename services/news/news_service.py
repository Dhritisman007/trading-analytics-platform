# services/news/news_service.py

import logging
from datetime import datetime, timezone

from services.news.news_fetcher import fetch_rss_news, fetch_newsapi
from services.news.sentiment_analyzer import analyze_batch
from core.cache import cache

logger = logging.getLogger(__name__)

NEWS_CACHE_KEY = "news:all"
NEWS_TTL       = 900  # 15 minutes


def get_news(
    limit: int = 30,
    topic: str | None = None,
    sentiment_filter: str | None = None,
    source: str | None = None,
    breaking_only: bool = False,
) -> dict:
    """
    Fetch and return filtered news with sentiment scores.
    Results are cached for 15 minutes.

    Args:
        limit:            max articles to return
        topic:            filter by topic (rbi_policy, earnings, ipo, etc.)
        sentiment_filter: filter by label (positive, negative, neutral)
        source:           filter by news source
        breaking_only:    show only articles < 2 hours old

    Returns:
        dict with articles, market mood summary, and topic distribution
    """
    # ── Cache check ───────────────────────────────────────────────────────
    cached = cache.get(NEWS_CACHE_KEY)
    if not cached:
        cached = _fetch_and_cache()

    articles = cached.get("articles", [])

    # ── Apply filters ─────────────────────────────────────────────────────
    if topic:
        articles = [a for a in articles if topic in a.get("topics", [])]

    if sentiment_filter:
        articles = [
            a for a in articles
            if a.get("sentiment", {}).get("label") == sentiment_filter
        ]

    if source:
        articles = [
            a for a in articles
            if source.lower() in a.get("source", "").lower()
        ]

    if breaking_only:
        articles = [a for a in articles if a.get("is_breaking")]

    articles = articles[:limit]

    # ── Aggregate sentiment for filtered set ──────────────────────────────
    headlines    = [a["title"] for a in articles]
    market_mood  = analyze_batch(headlines)

    # ── Topic distribution ────────────────────────────────────────────────
    topic_counts: dict[str, int] = {}
    for article in cached.get("articles", []):
        for t in article.get("topics", []):
            topic_counts[t] = topic_counts.get(t, 0) + 1
    topic_distribution = dict(
        sorted(topic_counts.items(), key=lambda x: x[1], reverse=True)
    )

    # ── Breaking news count ───────────────────────────────────────────────
    breaking_count = sum(
        1 for a in cached.get("articles", []) if a.get("is_breaking")
    )

    return {
        "fetched_at":         cached.get("fetched_at"),
        "total_available":    len(cached.get("articles", [])),
        "returned":           len(articles),
        "breaking_count":     breaking_count,
        "market_mood":        market_mood,
        "topic_distribution": topic_distribution,
        "filters_applied": {
            "topic":            topic,
            "sentiment":        sentiment_filter,
            "source":           source,
            "breaking_only":    breaking_only,
        },
        "articles": articles,
    }


def _fetch_and_cache() -> dict:
    """
    Fetch fresh news from all sources and store in cache.
    Called by scheduler every 15 minutes and on cache miss.
    """
    logger.info("Fetching fresh news from all sources...")

    # Fetch from all sources
    rss_articles  = fetch_rss_news(max_per_feed=10)
    api_articles  = fetch_newsapi(max_articles=20)

    # Combine and deduplicate
    seen   = set()
    merged = []
    for article in rss_articles + api_articles:
        key = article["title"][:50].lower()
        if key not in seen:
            seen.add(key)
            merged.append(article)

    # Sort newest first
    merged.sort(key=lambda x: x.get("published_at", ""), reverse=True)

    result = {
        "articles":   merged,
        "fetched_at": datetime.now(timezone.utc).isoformat(),
        "sources": {
            "rss":     len(rss_articles),
            "newsapi": len(api_articles),
            "total":   len(merged),
        },
    }

    cache.set(NEWS_CACHE_KEY, result, ttl_seconds=NEWS_TTL)
    logger.info(f"Cached {len(merged)} articles")
    return result


def refresh_news() -> dict:
    """Force a cache refresh — called by the scheduler."""
    return _fetch_and_cache()


def get_sentiment_summary() -> dict:
    """
    Quick sentiment summary without full article data.
    Used by the dashboard header to show market mood badge.
    """
    cached = cache.get(NEWS_CACHE_KEY)
    if not cached:
        cached = _fetch_and_cache()

    headlines   = [a["title"] for a in cached.get("articles", [])]
    mood        = analyze_batch(headlines)

    # Separate bullish vs bearish topics
    bullish_topics = []
    bearish_topics = []
    for article in cached.get("articles", []):
        sent = article.get("sentiment", {}).get("label")
        if sent == "positive":
            bullish_topics.extend(article.get("topics", []))
        elif sent == "negative":
            bearish_topics.extend(article.get("topics", []))

    return {
        "market_mood":     mood,
        "bullish_topics":  list(set(bullish_topics))[:5],
        "bearish_topics":  list(set(bearish_topics))[:5],
        "fetched_at":      cached.get("fetched_at"),
        "article_count":   len(cached.get("articles", [])),
    }