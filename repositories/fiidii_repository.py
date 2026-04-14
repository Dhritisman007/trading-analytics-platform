# repositories/fiidii_repository.py
"""
Repository for FII/DII flow data access.
Handles all database operations for institutional investor tracking.
"""

from sqlalchemy.orm import Session
from sqlalchemy import desc
from models.trade import FiidiiFlow
from datetime import datetime, timedelta
from typing import List, Optional
import logging

logger = logging.getLogger(__name__)


class FiidiiFlowRepository:
    """
    Repository for FiidiiFlow model operations.
    Handles all database queries for FII/DII flows.
    """

    @staticmethod
    def create(db: Session, **kwargs) -> FiidiiFlow:
        """Create and save FII/DII flow record."""
        flow = FiidiiFlow(**kwargs)
        db.add(flow)
        db.commit()
        db.refresh(flow)
        logger.info(f"FII/DII flow recorded: {flow.date} FII:{flow.fii_net} DII:{flow.dii_net}")
        return flow

    @staticmethod
    def get_by_date(db: Session, date: str) -> Optional[FiidiiFlow]:
        """Get flow data for a specific date (YYYY-MM-DD)."""
        return db.query(FiidiiFlow).filter(FiidiiFlow.date == date).first()

    @staticmethod
    def get_recent(db: Session, days: int = 30) -> List[FiidiiFlow]:
        """Get recent FII/DII flow data."""
        cutoff = datetime.utcnow() - timedelta(days=days)
        return db.query(FiidiiFlow).filter(
            FiidiiFlow.created_at >= cutoff
        ).order_by(desc(FiidiiFlow.date)).all()

    @staticmethod
    def get_latest(db: Session) -> Optional[FiidiiFlow]:
        """Get the most recent FII/DII flow record."""
        return db.query(FiidiiFlow).order_by(desc(FiidiiFlow.date)).first()

    @staticmethod
    def get_by_signal(db: Session, signal: str, days: int = 30) -> List[FiidiiFlow]:
        """Get flows matching a signal (BULLISH, BEARISH, etc)."""
        cutoff = datetime.utcnow() - timedelta(days=days)
        return db.query(FiidiiFlow).filter(
            FiidiiFlow.signal == signal,
            FiidiiFlow.created_at >= cutoff
        ).order_by(desc(FiidiiFlow.date)).all()

    @staticmethod
    def get_net_trend(db: Session, days: int = 30) -> dict:
        """Get aggregate net flow trends."""
        cutoff = datetime.utcnow() - timedelta(days=days)
        flows = db.query(FiidiiFlow).filter(
            FiidiiFlow.created_at >= cutoff
        ).order_by(desc(FiidiiFlow.date)).all()

        if not flows:
            return {
                "days": days,
                "total_records": 0,
                "avg_fii_net": 0,
                "avg_dii_net": 0,
                "avg_combined_net": 0,
                "fii_trend": "NEUTRAL",
                "dii_trend": "NEUTRAL",
            }

        avg_fii = sum(f.fii_net for f in flows) / len(flows)
        avg_dii = sum(f.dii_net for f in flows) / len(flows)
        avg_combined = sum(f.combined_net for f in flows) / len(flows)

        fii_trend = "BULLISH" if avg_fii > 0 else "BEARISH" if avg_fii < 0 else "NEUTRAL"
        dii_trend = "BULLISH" if avg_dii > 0 else "BEARISH" if avg_dii < 0 else "NEUTRAL"

        return {
            "days": days,
            "total_records": len(flows),
            "avg_fii_net": round(avg_fii, 2),
            "avg_dii_net": round(avg_dii, 2),
            "avg_combined_net": round(avg_combined, 2),
            "fii_trend": fii_trend,
            "dii_trend": dii_trend,
        }

    @staticmethod
    def is_bullish(db: Session, threshold: float = 100.0) -> bool:
        """Check if latest FII/DII flow is bullish."""
        latest = FiidiiFlowRepository.get_latest(db)
        if not latest:
            return False
        return latest.combined_net > threshold

    @staticmethod
    def update(db: Session, date: str, **kwargs) -> FiidiiFlow:
        """Update flow record for a date."""
        flow = FiidiiFlowRepository.get_by_date(db, date)
        if not flow:
            raise ValueError(f"Flow record not found for {date}")

        for key, value in kwargs.items():
            if hasattr(flow, key):
                setattr(flow, key, value)

        db.commit()
        db.refresh(flow)
        logger.info(f"FII/DII flow updated: {date}")
        return flow
