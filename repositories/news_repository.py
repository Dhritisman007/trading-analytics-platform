# repositories/news_repository.py
"""
Repository for news article data access.
Handles all database operations for news sentiment analysis and archival.
"""

from sqlalchemy.orm import Session
from sqlalchemy import desc, and_
from models.trade import NewsArticle
from datetime import datetime, timedelta
from typing import List, Optional
import logging

logger = logging.getLogger(__name__)


class NewsArticleRepository:
    """
    Repository for NewsArticle model operations.
    Handles all database queries for news articles.
    """

    @staticmethod
    def create(db: Session, **kwargs) -> NewsArticle:
        """Create and save a new news article."""
        article = NewsArticle(**kwargs)
        db.add(article)
        db.commit()
        db.refresh(article)
        logger.info(f"News article saved: {article.title[:50]}")
        return article

    @staticmethod
    def get_by_id(db: Session, article_id: int) -> Optional[NewsArticle]:
        """Get news article by ID."""
        return db.query(NewsArticle).filter(NewsArticle.id == article_id).first()

    @staticmethod
    def get_by_url(db: Session, url: str) -> Optional[NewsArticle]:
        """Get news article by URL (check for duplicates)."""
        return db.query(NewsArticle).filter(NewsArticle.url == url).first()

    @staticmethod
    def get_recent(db: Session, days: int = 7, limit: int = 100) -> List[NewsArticle]:
        """Get recent news articles."""
        cutoff = datetime.utcnow() - timedelta(days=days)
        return db.query(NewsArticle).filter(
            NewsArticle.published_at >= cutoff
        ).order_by(desc(NewsArticle.published_at)).limit(limit).all()

    @staticmethod
    def get_by_sentiment(db: Session, sentiment: str, days: int = 7) -> List[NewsArticle]:
        """Get articles by sentiment (positive, negative, neutral)."""
        cutoff = datetime.utcnow() - timedelta(days=days)
        return db.query(NewsArticle).filter(
            and_(
                NewsArticle.sentiment == sentiment,
                NewsArticle.published_at >= cutoff
            )
        ).order_by(desc(NewsArticle.published_at)).all()

    @staticmethod
    def get_market_news(db: Session, days: int = 7) -> List[NewsArticle]:
        """Get market-related news."""
        cutoff = datetime.utcnow() - timedelta(days=days)
        return db.query(NewsArticle).filter(
            and_(
                NewsArticle.is_market_news == True,
                NewsArticle.published_at >= cutoff
            )
        ).order_by(desc(NewsArticle.published_at)).all()

    @staticmethod
    def get_high_impact(db: Session, days: int = 7, min_score: float = 0.7) -> List[NewsArticle]:
        """Get high-impact news articles."""
        cutoff = datetime.utcnow() - timedelta(days=days)
        return db.query(NewsArticle).filter(
            and_(
                NewsArticle.impact_score >= min_score,
                NewsArticle.published_at >= cutoff
            )
        ).order_by(desc(NewsArticle.impact_score)).all()

    @staticmethod
    def get_sentiment_aggregate(db: Session, days: int = 7) -> dict:
        """Get sentiment aggregates over period."""
        cutoff = datetime.utcnow() - timedelta(days=days)
        articles = db.query(NewsArticle).filter(
            NewsArticle.published_at >= cutoff
        ).all()

        if not articles:
            return {
                "total": 0,
                "positive": 0,
                "negative": 0,
                "neutral": 0,
                "avg_sentiment_score": 0,
            }

        positive = len([a for a in articles if a.sentiment == "positive"])
        negative = len([a for a in articles if a.sentiment == "negative"])
        neutral = len([a for a in articles if a.sentiment == "neutral"])
        avg_score = sum(a.sentiment_score for a in articles if a.sentiment_score) / len(articles) if articles else 0

        return {
            "total": len(articles),
            "positive": positive,
            "negative": negative,
            "neutral": neutral,
            "avg_sentiment_score": round(avg_score, 3),
        }

    @staticmethod
    def delete_old(db: Session, days: int = 90) -> int:
        """Delete articles older than N days (archive old data)."""
        cutoff = datetime.utcnow() - timedelta(days=days)
        deleted = db.query(NewsArticle).filter(
            NewsArticle.published_at < cutoff
        ).delete()
        db.commit()
        logger.info(f"Deleted {deleted} old news articles")
        return deleted
