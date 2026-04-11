# routers/news.py

from fastapi import APIRouter, HTTPException, Query
from services.news.news_service import get_news, get_sentiment_summary, refresh_news

router = APIRouter(prefix="/news", tags=["News & Sentiment"])

VALID_TOPICS = [
    "rbi_policy", "fii_dii", "earnings", "ipo",
    "global", "economy", "budget", "commodities", "general",
]
VALID_SENTIMENTS = ["positive", "negative", "neutral"]


@router.get("/")
def get_financial_news(
    limit: int = Query(
        default=20,
        ge=1, le=100,
        description="Max articles to return (default 20)"
    ),
    topic: str | None = Query(
        default=None,
        description=f"Filter by topic: {', '.join(VALID_TOPICS)}"
    ),
    sentiment: str | None = Query(
        default=None,
        description="Filter by sentiment: positive, negative, neutral"
    ),
    source: str | None = Query(
        default=None,
        description="Filter by source name (e.g. 'Economic Times')"
    ),
    breaking_only: bool = Query(
        default=False,
        description="Show only articles from last 2 hours"
    ),
):
    """
    Fetch Indian financial news with VADER sentiment scores.

    Each article includes:
    - Sentiment score (-1.0 to +1.0) and label (positive/neutral/negative)
    - Market impact estimate (HIGH/MEDIUM/LOW)
    - Topic tags (rbi_policy, earnings, fii_dii, etc.)
    - Breaking flag for recent articles

    Results cached for 15 minutes, auto-refreshed by scheduler.
    """
    if topic and topic not in VALID_TOPICS:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid topic '{topic}'. Valid: {VALID_TOPICS}"
        )
    if sentiment and sentiment not in VALID_SENTIMENTS:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid sentiment '{sentiment}'. Valid: {VALID_SENTIMENTS}"
        )

    try:
        return get_news(
            limit=limit,
            topic=topic,
            sentiment_filter=sentiment,
            source=source,
            breaking_only=breaking_only,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/mood")
def get_market_mood():
    """
    Quick sentiment snapshot — no full article data.
    Used by dashboard header to display overall market mood badge.
    Returns in <50ms from cache.
    """
    try:
        return get_sentiment_summary()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/breaking")
def get_breaking_news(limit: int = Query(default=10, ge=1, le=30)):
    """Articles published in the last 2 hours."""
    try:
        return get_news(limit=limit, breaking_only=True)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/topics")
def get_topics():
    """List all available topic filters with descriptions."""
    return {
        "topics": [
            {"name": "rbi_policy",  "description": "RBI rate decisions, monetary policy"},
            {"name": "fii_dii",     "description": "Institutional investor flows"},
            {"name": "earnings",    "description": "Quarterly results and guidance"},
            {"name": "ipo",         "description": "IPO listings and grey market"},
            {"name": "global",      "description": "US Fed, global market events"},
            {"name": "economy",     "description": "GDP, inflation, macro data"},
            {"name": "budget",      "description": "Union budget and fiscal policy"},
            {"name": "commodities", "description": "Oil, gold, silver prices"},
            {"name": "general",     "description": "General market news"},
        ]
    }


@router.post("/refresh")
def force_refresh():
    """
    Force an immediate news cache refresh.
    Normally auto-refreshes every 15 minutes via scheduler.
    """
    try:
        result = refresh_news()
        return {
            "status":    "refreshed",
            "articles":  result["sources"]["total"],
            "fetched_at": result["fetched_at"],
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))