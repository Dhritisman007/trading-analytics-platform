# services/news/news_fetcher.py

import httpx
import feedparser
import logging
import re
from datetime import datetime, timezone, timedelta
from typing import Any

from services.news.sentiment_analyzer import (
    analyze_sentiment,
    estimate_market_impact,
)
from core.config import settings
from utils.formatters import format_number

logger = logging.getLogger(__name__)

# Indian financial news RSS feeds — no API key needed
RSS_FEEDS = [
    {
        "name":   "Economic Times — Markets",
        "url":    "https://economictimes.indiatimes.com/markets/rssfeeds/1977021501.cms",
        "source": "Economic Times",
    },
    {
        "name":   "Moneycontrol — Markets",
        "url":    "https://www.moneycontrol.com/rss/marketreports.xml",
        "source": "Moneycontrol",
    },
    {
        "name":   "LiveMint — Markets",
        "url":    "https://www.livemint.com/rss/markets",
        "source": "LiveMint",
    },
    {
        "name":   "Business Standard — Markets",
        "url":    "https://www.business-standard.com/rss/markets-106.rss",
        "source": "Business Standard",
    },
]

# Keywords that make news relevant to Indian equity markets
MARKET_KEYWORDS = [
    "nifty", "sensex", "bse", "nse", "sebi", "rbi",
    "stock", "share", "market", "equity", "index",
    "fii", "dii", "mutual fund", "ipo", "budget",
    "inflation", "gdp", "repo rate", "earnings",
    "quarterly results", "profit", "revenue",
]

# Topics used for categorising articles
TOPIC_KEYWORDS = {
    "rbi_policy":    ["rbi", "repo rate", "monetary policy", "interest rate", "mpc"],
    "fii_dii":       ["fii", "dii", "foreign institutional", "domestic institutional", "net buy", "net sell"],
    "earnings":      ["quarterly results", "q1", "q2", "q3", "q4", "profit", "revenue", "earnings"],
    "ipo":           ["ipo", "initial public offering", "listing", "grey market"],
    "global":        ["fed", "federal reserve", "us market", "dow jones", "nasdaq", "global"],
    "economy":       ["gdp", "inflation", "cpi", "wpi", "iip", "trade deficit"],
    "budget":        ["budget", "finance minister", "fiscal", "tax", "gst"],
    "commodities":   ["oil", "gold", "silver", "crude", "commodity"],
}


def _clean_text(text: str) -> str:
    """Remove HTML tags and normalize whitespace."""
    if not text:
        return ""
    clean = re.sub(r"<[^>]+>", "", text)
    clean = re.sub(r"\s+", " ", clean).strip()
    return clean[:500]  # cap at 500 chars for sentiment analysis


def _extract_keywords(text: str) -> list[str]:
    """Find market-relevant keywords in a text."""
    text_lower = text.lower()
    return [kw for kw in MARKET_KEYWORDS if kw in text_lower]


def _detect_topics(text: str) -> list[str]:
    """Categorise article by financial topic."""
    text_lower = text.lower()
    topics = []
    for topic, keywords in TOPIC_KEYWORDS.items():
        if any(kw in text_lower for kw in keywords):
            topics.append(topic)
    return topics if topics else ["general"]


def _is_breaking(published_at: str) -> bool:
    """Flag articles published in the last 2 hours as breaking."""
    try:
        pub_time = datetime.fromisoformat(published_at.replace("Z", "+00:00"))
        age = datetime.now(timezone.utc) - pub_time
        return age < timedelta(hours=2)
    except Exception:
        return False


def _parse_rss_entry(entry: Any, source: str) -> dict | None:
    """Convert a single RSS entry into a clean article dict."""
    try:
        title   = _clean_text(entry.get("title", ""))
        summary = _clean_text(entry.get("summary", entry.get("description", "")))
        link    = entry.get("link", "")

        if not title:
            return None

        # Parse publish time
        published_parsed = entry.get("published_parsed")
        if published_parsed:
            pub_dt = datetime(*published_parsed[:6], tzinfo=timezone.utc)
            published_at = pub_dt.isoformat()
        else:
            published_at = datetime.now(timezone.utc).isoformat()

        # Analyze sentiment on title + summary combined
        full_text   = f"{title}. {summary}"
        sentiment   = analyze_sentiment(full_text)
        keywords    = _extract_keywords(full_text)
        topics      = _detect_topics(full_text)
        impact      = estimate_market_impact(
            float(sentiment["compound"]), keywords
        )

        return {
            "title":        title,
            "summary":      summary[:200] if summary else "",
            "url":          link,
            "source":       source,
            "published_at": published_at,
            "is_breaking":  _is_breaking(published_at),
            "keywords":     keywords,
            "topics":       topics,
            "sentiment":    sentiment,
            "impact":       impact,
        }

    except Exception as e:
        logger.debug(f"Failed to parse RSS entry: {e}")
        return None


def fetch_rss_news(max_per_feed: int = 10) -> list[dict]:
    """
    Fetch articles from all configured RSS feeds.
    Runs synchronously — called by the scheduler.
    """
    all_articles = []
    seen_titles  = set()  # deduplication

    for feed_config in RSS_FEEDS:
        try:
            logger.debug(f"Fetching RSS: {feed_config['name']}")
            feed     = feedparser.parse(feed_config["url"])
            count    = 0

            for entry in feed.entries:
                if count >= max_per_feed:
                    break

                article = _parse_rss_entry(entry, feed_config["source"])
                if not article:
                    continue

                # Skip duplicates by title similarity
                title_key = article["title"][:50].lower()
                if title_key in seen_titles:
                    continue

                seen_titles.add(title_key)
                all_articles.append(article)
                count += 1

        except Exception as e:
            logger.warning(f"Failed to fetch {feed_config['name']}: {e}")

    # Sort newest first
    all_articles.sort(key=lambda x: x["published_at"], reverse=True)
    logger.info(f"Fetched {len(all_articles)} articles from {len(RSS_FEEDS)} feeds")
    return all_articles


def fetch_newsapi(
    query: str = "Nifty OR Sensex OR NSE OR BSE OR Indian stock market",
    max_articles: int = 20,
) -> list[dict]:
    """
    Fetch news from NewsAPI (requires API key).
    Falls back gracefully if no key is configured.
    """
    api_key = getattr(settings, "newsapi_key", None)
    if not api_key:
        logger.info("No NEWSAPI_KEY configured — skipping NewsAPI")
        return []

    try:
        url    = "https://newsapi.org/v2/everything"
        params = {
            "q":          query,
            "language":   "en",
            "sortBy":     "publishedAt",
            "pageSize":   max_articles,
            "apiKey":     api_key,
        }

        with httpx.Client(timeout=10) as client:
            response = client.get(url, params=params)
            response.raise_for_status()

        data     = response.json()
        articles = []

        for item in data.get("articles", []):
            title   = _clean_text(item.get("title", ""))
            summary = _clean_text(item.get("description", ""))

            if not title or title == "[Removed]":
                continue

            full_text = f"{title}. {summary}"
            sentiment = analyze_sentiment(full_text)
            keywords  = _extract_keywords(full_text)
            topics    = _detect_topics(full_text)
            impact    = estimate_market_impact(float(sentiment["compound"]), keywords)

            articles.append({
                "title":        title,
                "summary":      summary[:200],
                "url":          item.get("url", ""),
                "source":       item.get("source", {}).get("name", "NewsAPI"),
                "published_at": item.get("publishedAt", datetime.now(timezone.utc).isoformat()),
                "is_breaking":  _is_breaking(item.get("publishedAt", "")),
                "keywords":     keywords,
                "topics":       topics,
                "sentiment":    sentiment,
                "impact":       impact,
            })

        return articles

    except Exception as e:
        logger.warning(f"NewsAPI fetch failed: {e}")
        return []