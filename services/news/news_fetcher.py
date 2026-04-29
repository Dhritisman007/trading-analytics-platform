# services/news/news_fetcher.py

import httpx
import feedparser
import logging
import re
import time
from datetime import datetime, timezone, timedelta
from typing import Any

from services.news.sentiment_analyzer import (
    analyze_sentiment,
    estimate_market_impact,
)
from core.config import settings

logger = logging.getLogger(__name__)

# ── Browser headers — makes most sites think we're Chrome ────────────────────
BROWSER_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/122.0.0.0 Safari/537.36"
    ),
    "Accept":          "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-IN,en;q=0.9",
    "Accept-Encoding": "gzip, deflate, br",
    "Connection":      "keep-alive",
    "Cache-Control":   "no-cache",
}

RSS_HEADERS = {
    **BROWSER_HEADERS,
    "Accept": "application/rss+xml, application/xml, text/xml, */*",
}

# ── RSS feeds that actually work with browser headers ─────────────────────────
RSS_FEEDS = [
    {
        "name":   "Economic Times — Markets",
        "url":    "https://economictimes.indiatimes.com/markets/rssfeeds/1977021501.cms",
        "source": "Economic Times",
    },
    {
        "name":   "Economic Times — Top Stories",
        "url":    "https://economictimes.indiatimes.com/rssfeedsdefault.cms",
        "source": "Economic Times",
    },
    {
        "name":   "Financial Express — Markets",
        "url":    "https://www.financialexpress.com/market/feed/",
        "source": "Financial Express",
    },
    {
        "name":   "Hindu BusinessLine — Markets",
        "url":    "https://www.thehindubusinessline.com/markets/feeder/default.rss",
        "source": "BusinessLine",
    },
    {
        "name":   "Livemint — Markets",
        "url":    "https://www.livemint.com/rss/markets",
        "source": "LiveMint",
    },
    {
        "name":   "Moneycontrol — Latest",
        "url":    "https://www.moneycontrol.com/rss/latestnews.xml",
        "source": "Moneycontrol",
    },
    {
        "name":   "Business Standard — Markets",
        "url":    "https://www.business-standard.com/rss/markets-106.rss",
        "source": "Business Standard",
    },
    {
        "name":   "NSE India — Circulars",
        "url":    "https://www.nseindia.com/rss/rssresearch.xml",
        "source": "NSE India",
    },
]

# ── NewsAPI queries for Indian markets ────────────────────────────────────────
NEWSAPI_QUERIES = [
    {
        "q":      "Nifty OR Sensex OR NSE OR BSE",
        "source": "NewsAPI — Indian Markets",
    },
    {
        "q":      "RBI OR SEBI OR Indian stock market",
        "source": "NewsAPI — RBI/SEBI",
    },
    {
        "q":      "FII OR DII OR Nifty Bank OR Bank Nifty",
        "source": "NewsAPI — Institutional",
    },
]

# Market-relevant keywords for filtering
MARKET_KEYWORDS = [
    "nifty", "sensex", "bse", "nse", "sebi", "rbi",
    "stock", "share", "market", "equity", "index",
    "fii", "dii", "mutual fund", "ipo", "budget",
    "inflation", "gdp", "repo rate", "earnings",
    "quarterly results", "profit", "revenue",
]

TOPIC_KEYWORDS = {
    "rbi_policy":  ["rbi", "repo rate", "monetary policy", "interest rate", "mpc"],
    "fii_dii":     ["fii", "dii", "foreign institutional", "domestic institutional"],
    "earnings":    ["quarterly results", "q1", "q2", "q3", "q4", "profit", "revenue", "earnings"],
    "ipo":         ["ipo", "initial public offering", "listing", "grey market"],
    "global":      ["fed", "federal reserve", "us market", "dow jones", "nasdaq"],
    "economy":     ["gdp", "inflation", "cpi", "wpi", "trade deficit"],
    "budget":      ["budget", "finance minister", "fiscal", "tax", "gst"],
    "commodities": ["oil", "gold", "silver", "crude", "commodity"],
}


# ── Helpers ───────────────────────────────────────────────────────────────────

def _clean_text(text: str) -> str:
    if not text:
        return ""
    clean = re.sub(r"<[^>]+>", "", text)
    clean = re.sub(r"\s+", " ", clean).strip()
    return clean[:500]


def _extract_keywords(text: str) -> list[str]:
    text_lower = text.lower()
    return [kw for kw in MARKET_KEYWORDS if kw in text_lower]


def _detect_topics(text: str) -> list[str]:
    text_lower = text.lower()
    topics = [
        topic for topic, keywords in TOPIC_KEYWORDS.items()
        if any(kw in text_lower for kw in keywords)
    ]
    return topics if topics else ["general"]


def _is_breaking(published_at: str) -> bool:
    try:
        pub_time = datetime.fromisoformat(published_at.replace("Z", "+00:00"))
        return (datetime.now(timezone.utc) - pub_time) < timedelta(hours=2)
    except Exception:
        return False


def _build_article(
    title: str,
    summary: str,
    url: str,
    source: str,
    published_at: str,
) -> dict | None:
    """Build a standardised article dict with sentiment analysis."""
    title   = _clean_text(title)
    summary = _clean_text(summary)

    if not title or len(title) < 10:
        return None

    full_text = f"{title}. {summary}"
    sentiment = analyze_sentiment(full_text)
    keywords  = _extract_keywords(full_text)
    topics    = _detect_topics(full_text)
    impact    = estimate_market_impact(float(sentiment["compound"]), keywords)

    return {
        "title":        title,
        "summary":      summary[:200] if summary else "",
        "url":          url or "",
        "source":       source,
        "published_at": published_at,
        "is_breaking":  _is_breaking(published_at),
        "keywords":     keywords,
        "topics":       topics,
        "sentiment":    sentiment,
        "impact":       impact,
    }


def _parse_rss_entry(entry: Any, source: str) -> dict | None:
    """Parse a single feedparser RSS entry."""
    try:
        title   = _clean_text(entry.get("title", ""))
        summary = _clean_text(entry.get("summary", entry.get("description", "")))
        link    = entry.get("link", "")

        published_parsed = entry.get("published_parsed")
        if published_parsed:
            pub_dt       = datetime(*published_parsed[:6], tzinfo=timezone.utc)
            published_at = pub_dt.isoformat()
        else:
            published_at = datetime.now(timezone.utc).isoformat()

        return _build_article(title, summary, link, source, published_at)

    except Exception as e:
        logger.debug(f"RSS parse error: {e}")
        return None


# ── Layer 1: RSS with browser headers ─────────────────────────────────────────

def fetch_rss_news(max_per_feed: int = 10) -> list[dict]:
    """Fetch from RSS feeds using browser User-Agent."""
    all_articles = []
    seen_titles  = set()

    for feed_config in RSS_FEEDS:
        try:
            # Try with browser headers first
            try:
                with httpx.Client(
                    headers=RSS_HEADERS,
                    timeout=15,
                    follow_redirects=True,
                ) as client:
                    response = client.get(feed_config["url"])
                    feed     = feedparser.parse(response.content)
            except Exception:
                # Fallback to direct feedparser
                feed = feedparser.parse(feed_config["url"])

            count = 0
            for entry in feed.entries:
                if count >= max_per_feed:
                    break

                article = _parse_rss_entry(entry, feed_config["source"])
                if not article:
                    continue

                title_key = article["title"][:50].lower()
                if title_key in seen_titles:
                    continue

                seen_titles.add(title_key)
                all_articles.append(article)
                count += 1

            if count > 0:
                logger.info(f"RSS ✓ {feed_config['name']}: {count} articles")
            else:
                logger.debug(f"RSS ✗ {feed_config['name']}: 0 articles")

        except Exception as e:
            logger.warning(f"RSS failed {feed_config['name']}: {e}")

    return all_articles


# ── Layer 2: NewsAPI ──────────────────────────────────────────────────────────

def fetch_newsapi(max_per_query: int = 15) -> list[dict]:
    """
    Fetch from GNews API (gnews.io) — the key in .env is a GNews UUID key.
    Free tier: 100 req/day, up to 10 articles per request.
    Docs: https://gnews.io/docs/v4
    """
    api_key = getattr(settings, "newsapi_key", "") or ""
    if not api_key:
        logger.info("No NEWSAPI_KEY — skipping GNews")
        return []

    # GNews free tier: max 10 results per request
    page_size = min(max_per_query, 10)

    articles = []
    seen     = set()

    for query_config in NEWSAPI_QUERIES:
        try:
            with httpx.Client(timeout=10) as client:
                response = client.get(
                    "https://gnews.io/api/v4/search",
                    params={
                        "q":       query_config["q"],
                        "lang":    "en",
                        "country": "in",
                        "max":     page_size,
                        "sortby":  "publishedAt",
                        "token":   api_key,        # GNews v4 uses 'token', not 'apikey'
                    },
                )
                data = response.json()

            if "errors" in data:
                logger.warning(f"GNews error: {data['errors']}")
                continue

            for item in data.get("articles", []):
                title = item.get("title", "")
                if not title:
                    continue

                title_key = title[:50].lower()
                if title_key in seen:
                    continue
                seen.add(title_key)

                article = _build_article(
                    title=title,
                    summary=item.get("description", ""),
                    url=item.get("url", ""),
                    source=item.get("source", {}).get("name", "GNews"),
                    published_at=item.get(
                        "publishedAt",
                        datetime.now(timezone.utc).isoformat()
                    ),
                )
                if article:
                    articles.append(article)

            logger.info(f"GNews ✓ '{query_config['q']}': {len(articles)} total so far")
            time.sleep(0.5)  # be polite — free tier rate limits

        except Exception as e:
            logger.warning(f"GNews failed for '{query_config['q']}': {e}")

    return articles


# ── Layer 3: Moneycontrol direct scraper ──────────────────────────────────────

def fetch_moneycontrol_direct(max_articles: int = 15) -> list[dict]:
    """
    Scrape Moneycontrol news headlines directly from their website.
    Used as fallback when RSS is blocked.
    """
    articles = []

    urls_to_try = [
        "https://www.moneycontrol.com/news/business/markets/",
        "https://www.moneycontrol.com/news/business/stocks/",
    ]

    for url in urls_to_try:
        try:
            with httpx.Client(
                headers=BROWSER_HEADERS,
                timeout=15,
                follow_redirects=True,
            ) as client:
                response = client.get(url)

            if response.status_code != 200:
                continue

            from bs4 import BeautifulSoup
            # Use lxml if available, fall back to built-in html.parser
            try:
                soup = BeautifulSoup(response.text, "lxml")
            except Exception:
                soup = BeautifulSoup(response.text, "html.parser")

            # Moneycontrol article selectors
            selectors = [
                "li.clearfix h2 a",
                ".news_list li a",
                "article h2 a",
                ".common-article h3 a",
            ]

            headlines = []
            for selector in selectors:
                found = soup.select(selector)
                if found:
                    headlines = found[:max_articles]
                    break

            for tag in headlines:
                title = _clean_text(tag.get_text())
                href  = tag.get("href", "")

                if not title or len(title) < 15:
                    continue
                if not href.startswith("http"):
                    href = f"https://www.moneycontrol.com{href}"

                article = _build_article(
                    title=title,
                    summary="",
                    url=href,
                    source="Moneycontrol",
                    published_at=datetime.now(timezone.utc).isoformat(),
                )
                if article:
                    articles.append(article)

            if articles:
                logger.info(f"Moneycontrol scraper ✓: {len(articles)} articles from {url}")
                break

        except Exception as e:
            logger.warning(f"Moneycontrol scraper failed: {e}")

    return articles


# ── Master fetch function ─────────────────────────────────────────────────────

def fetch_all_news() -> list[dict]:
    """
    Fetch news from all layers, combine, deduplicate, sort newest first.

    Priority:
    1. RSS feeds with browser headers (ET, Financial Express, LiveMint, etc.)
    2. NewsAPI (most reliable, covers all major Indian publications)
    3. Moneycontrol direct scraper (fallback if NewsAPI returned nothing)
    """
    all_articles = []
    seen_titles  = set()

    # Layer 1: RSS
    rss_articles = fetch_rss_news(max_per_feed=8)
    logger.info(f"RSS total: {len(rss_articles)} articles")

    # Layer 2: NewsAPI
    api_articles = fetch_newsapi(max_per_query=12)
    logger.info(f"NewsAPI total: {len(api_articles)} articles")

    # Layer 3: Moneycontrol direct (only if NewsAPI returned nothing)
    mc_articles = []
    if len(api_articles) < 5:
        mc_articles = fetch_moneycontrol_direct(max_articles=15)
        logger.info(f"Moneycontrol scraper total: {len(mc_articles)} articles")

    # Combine and deduplicate
    for article in rss_articles + api_articles + mc_articles:
        key = article["title"][:60].lower()
        if key not in seen_titles:
            seen_titles.add(key)
            all_articles.append(article)

    # Sort newest first
    all_articles.sort(
        key=lambda x: x.get("published_at", ""),
        reverse=True
    )

    logger.info(f"Final total: {len(all_articles)} unique articles")
    return all_articles