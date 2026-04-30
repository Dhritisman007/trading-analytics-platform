# services/news/news_fetcher.py
#
# Source status (verified 2026-04-29):
#   Moneycontrol  – latestnews.xml ✓ (15), business.xml ✓ (15)
#   CNBC TV18     – commonfeeds market/stocks/economy XML ✓ (200 each)
#   LiveMint      – rss/markets ✓ (35), rss/news ✓ (35), rss/money ✓ (35)
#   Financial Express – RSS dead (410); scraped via HTML h2 a selector ✓
#   NSE India     – RSS dead (404); pulled from /api/circulars JSON ✓ (155)

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
    "User-Agent": BROWSER_HEADERS["User-Agent"],
    "Accept":          "application/rss+xml, application/xml, text/xml, */*",
    "Accept-Language": "en-IN,en;q=0.9",
    # NO Accept-Encoding — we need plain-text XML, not Brotli/gzip compressed bytes
    # that feedparser cannot decompress. httpx handles this automatically when
    # Accept-Encoding is omitted.
    "Cache-Control":   "no-cache",
}

# ── Verified-working RSS feeds ────────────────────────────────────────────────
# (Tested 2026-04-29 — all return 200 with real entries)
RSS_FEEDS = [
    # ── Economic Times ────────────────────────────────────────────────────────
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
    # ── Moneycontrol ──────────────────────────────────────────────────────────
    {
        "name":   "Moneycontrol — Latest News",
        "url":    "https://www.moneycontrol.com/rss/latestnews.xml",
        "source": "Moneycontrol",
    },
    {
        "name":   "Moneycontrol — Business",
        "url":    "https://www.moneycontrol.com/rss/business.xml",
        "source": "Moneycontrol",
    },
    {
        "name":   "Moneycontrol — Market Reports",
        "url":    "https://www.moneycontrol.com/rss/marketreports.xml",
        "source": "Moneycontrol",
    },
    # ── CNBC TV18 ─────────────────────────────────────────────────────────────
    {
        "name":   "CNBC TV18 — Markets",
        "url":    "https://www.cnbctv18.com/commonfeeds/v1/cne/rss/market.xml",
        "source": "CNBC TV18",
    },
    {
        "name":   "CNBC TV18 — Stocks",
        "url":    "https://www.cnbctv18.com/commonfeeds/v1/cne/rss/stocks.xml",
        "source": "CNBC TV18",
    },
    {
        "name":   "CNBC TV18 — Economy",
        "url":    "https://www.cnbctv18.com/commonfeeds/v1/cne/rss/economy.xml",
        "source": "CNBC TV18",
    },
    # ── LiveMint ──────────────────────────────────────────────────────────────
    {
        "name":   "LiveMint — Markets",
        "url":    "https://www.livemint.com/rss/markets",
        "source": "LiveMint",
    },
    {
        "name":   "LiveMint — News",
        "url":    "https://www.livemint.com/rss/news",
        "source": "LiveMint",
    },
    {
        "name":   "LiveMint — Money",
        "url":    "https://www.livemint.com/rss/money",
        "source": "LiveMint",
    },
    # ── Business Standard ─────────────────────────────────────────────────────
    {
        "name":   "Business Standard — Markets",
        "url":    "https://www.business-standard.com/rss/markets-106.rss",
        "source": "Business Standard",
    },
    # ── Hindu BusinessLine ────────────────────────────────────────────────────
    {
        "name":   "Hindu BusinessLine — Markets",
        "url":    "https://www.thehindubusinessline.com/markets/feeder/default.rss",
        "source": "BusinessLine",
    },
]

# ── NewsAPI (GNews) queries for Indian markets ────────────────────────────────
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

# ── Market-relevant keywords for filtering ────────────────────────────────────
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
    """Fetch from verified-working RSS feeds using browser User-Agent."""
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
                logger.warning(f"RSS ✗ {feed_config['name']}: 0 articles (feed may be down)")

        except Exception as e:
            logger.warning(f"RSS failed {feed_config['name']}: {e}")

    return all_articles


# ── Layer 2: Financial Express — HTML scraper ──────────────────────────────────
# (Their RSS returns 410 Gone; their website works fine)

def fetch_financial_express(max_articles: int = 20) -> list[dict]:
    """
    Scrape Financial Express market news from their website.
    RSS feed is permanently dead (410 Gone) — HTML scraping is the only option.
    """
    articles = []
    seen     = set()

    urls_to_try = [
        "https://www.financialexpress.com/market/",
        "https://www.financialexpress.com/market/stock-market/",
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
                logger.warning(f"Financial Express scraper: HTTP {response.status_code} for {url}")
                continue

            try:
                from bs4 import BeautifulSoup
            except ImportError:
                logger.warning("BeautifulSoup not installed — cannot scrape Financial Express")
                return []

            try:
                soup = BeautifulSoup(response.text, "lxml")
            except Exception:
                soup = BeautifulSoup(response.text, "html.parser")

            # h2 a gives ~24 fresh market headlines consistently
            selectors = [
                "h2 a",
                "article h2 a",
                "h3 a",
                ".articles li a",
            ]

            headlines = []
            for selector in selectors:
                found = soup.select(selector)
                if found:
                    headlines = found
                    break

            for tag in headlines[:max_articles]:
                title = _clean_text(tag.get_text())
                href  = tag.get("href", "")

                if not title or len(title) < 15:
                    continue
                if not href.startswith("http"):
                    href = f"https://www.financialexpress.com{href}"

                title_key = title[:50].lower()
                if title_key in seen:
                    continue
                seen.add(title_key)

                article = _build_article(
                    title=title,
                    summary="",
                    url=href,
                    source="Financial Express",
                    published_at=datetime.now(timezone.utc).isoformat(),
                )
                if article:
                    articles.append(article)

            if articles:
                logger.info(f"Financial Express scraper ✓: {len(articles)} articles from {url}")
                break

        except Exception as e:
            logger.warning(f"Financial Express scraper failed for {url}: {e}")

    return articles


# ── Layer 3: NSE India — Official Circulars JSON API ─────────────────────────
# (RSS is dead 404; /api/circulars returns 155 live items with cookie session)

def fetch_nse_circulars(max_articles: int = 20) -> list[dict]:
    """
    Fetch NSE India official circulars from their JSON API.
    NSE requires a homepage cookie to unlock the API.
    Covers: listing changes, SEBI/NSE policy, margin requirements, circuit breakers.
    """
    articles = []

    nse_headers = {
        "User-Agent":      BROWSER_HEADERS["User-Agent"],
        "Accept":          "application/json, text/plain, */*",
        "Accept-Language": "en-IN,en;q=0.9",
        # NO Accept-Encoding — avoid Brotli/gzip compressed responses that are
        # hard to decode reliably; plain JSON is preferable.
        "Referer":         "https://www.nseindia.com/",
        "Cache-Control":   "no-cache",
    }

    try:
        with httpx.Client(
            headers=nse_headers,
            timeout=15,
            follow_redirects=True,
        ) as client:
            # Step 1: Visit homepage to receive session cookie (required by NSE)
            client.get("https://www.nseindia.com/")
            time.sleep(0.3)  # brief pause to ensure cookie is set

            # Step 2: Fetch circulars
            response = client.get("https://www.nseindia.com/api/circulars")

        if response.status_code != 200:
            logger.warning(f"NSE circulars API: HTTP {response.status_code}")
            return []

        # Use response.text to avoid encoding issues with compressed bytes
        import json as _json
        try:
            data = _json.loads(response.text)
        except Exception:
            data = response.json()
        circulars = data.get("data", [])

        for item in circulars[:max_articles]:
            subject    = _clean_text(item.get("sub", ""))
            circ_no    = item.get("circDisplayNo", "")
            category   = item.get("circCategory", "")
            dept       = item.get("circDepartment", "")
            circ_link  = item.get("circFilelink", "")
            date_str   = item.get("cirDate", "")          # e.g. "20260429"
            display_dt = item.get("cirDisplayDate", "")   # e.g. "April 29, 2026"

            if not subject or len(subject) < 10:
                continue

            # Parse date
            try:
                pub_dt = datetime.strptime(date_str, "%Y%m%d").replace(tzinfo=timezone.utc)
                published_at = pub_dt.isoformat()
            except Exception:
                published_at = datetime.now(timezone.utc).isoformat()

            # Build a readable title
            title = f"NSE Circular: {subject}"
            if circ_no:
                title = f"[{circ_no}] {subject}"

            summary = f"{category} | {dept} | {display_dt}".strip(" |")

            article = _build_article(
                title=title,
                summary=summary,
                url=circ_link or "https://www.nseindia.com/regulations/circulars",
                source="NSE India",
                published_at=published_at,
            )
            if article:
                articles.append(article)

        logger.info(f"NSE circulars ✓: {len(articles)} articles")

    except Exception as e:
        logger.warning(f"NSE circulars fetch failed: {e}")

    return articles


# ── Layer 4: GNews API ────────────────────────────────────────────────────────

def fetch_newsapi(max_per_query: int = 15) -> list[dict]:
    """
    Fetch from GNews API (gnews.io).
    Free tier: 100 req/day, up to 10 articles per request.
    """
    api_key = getattr(settings, "newsapi_key", "") or ""
    if not api_key:
        logger.info("No NEWSAPI_KEY — skipping GNews")
        return []

    page_size = min(max_per_query, 10)  # GNews free tier limit

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
                        "token":   api_key,
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
            time.sleep(0.5)  # free-tier rate limit

        except Exception as e:
            logger.warning(f"GNews failed for '{query_config['q']}': {e}")

    return articles


# ── Layer 5: Moneycontrol direct scraper (last resort) ───────────────────────

def fetch_moneycontrol_direct(max_articles: int = 15) -> list[dict]:
    """
    Scrape Moneycontrol news headlines directly.
    Used as fallback if all other layers return very few articles.
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

            try:
                from bs4 import BeautifulSoup
            except ImportError:
                return []

            try:
                soup = BeautifulSoup(response.text, "lxml")
            except Exception:
                soup = BeautifulSoup(response.text, "html.parser")

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
                logger.info(f"Moneycontrol direct scraper ✓: {len(articles)} articles")
                break

        except Exception as e:
            logger.warning(f"Moneycontrol direct scraper failed: {e}")

    return articles


# ── Master fetch function ─────────────────────────────────────────────────────

def fetch_all_news() -> list[dict]:
    """
    Fetch news from all layers, combine, deduplicate, sort newest first.

    Layer priority:
    1. RSS — Moneycontrol, CNBC TV18, LiveMint, ET, BS (all verified working)
    2. Financial Express — HTML scraper (RSS permanently dead)
    3. NSE India — Official circulars JSON API (RSS permanently dead)
    4. GNews API — broad coverage fallback
    5. Moneycontrol direct scraper — absolute last resort
    """
    all_articles = []
    seen_titles  = set()

    # Layer 1: RSS (Moneycontrol, CNBC, LiveMint, ET, BS, BusinessLine)
    rss_articles = fetch_rss_news(max_per_feed=8)
    logger.info(f"RSS total: {len(rss_articles)} articles")

    # Layer 2: Financial Express (scraper — RSS is dead)
    fe_articles = fetch_financial_express(max_articles=20)
    logger.info(f"Financial Express total: {len(fe_articles)} articles")

    # Layer 3: NSE India circulars (JSON API — RSS is dead)
    nse_articles = fetch_nse_circulars(max_articles=15)
    logger.info(f"NSE India total: {len(nse_articles)} articles")

    # Layer 4: GNews API
    api_articles = fetch_newsapi(max_per_query=12)
    logger.info(f"GNews total: {len(api_articles)} articles")

    # Layer 5: Moneycontrol direct (only if very few articles so far)
    mc_articles = []
    total_so_far = len(rss_articles) + len(fe_articles) + len(nse_articles) + len(api_articles)
    if total_so_far < 10:
        mc_articles = fetch_moneycontrol_direct(max_articles=15)
        logger.info(f"Moneycontrol direct total: {len(mc_articles)} articles")

    # Combine and deduplicate
    for article in rss_articles + fe_articles + nse_articles + api_articles + mc_articles:
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