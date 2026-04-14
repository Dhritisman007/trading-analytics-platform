# repositories/trade_repository.py
"""
Repository pattern for trade data access.
All database operations go through here — services don't query directly.
This keeps business logic separate from data persistence logic.
"""

from sqlalchemy.orm import Session
from sqlalchemy import desc, and_
from models.trade import Trade, TradeSignal, TradeGrade
from datetime import datetime, timedelta
from typing import List, Optional
import logging

logger = logging.getLogger(__name__)


class TradeRepository:
    """
    Repository for Trade model operations.
    Handles all database queries for trades.
    """

    @staticmethod
    def create(db: Session, **kwargs) -> Trade:
        """Create and save a new trade record."""
        trade = Trade(**kwargs)
        db.add(trade)
        db.commit()
        db.refresh(trade)
        logger.info(f"Trade created: {trade.symbol} {trade.signal} @ {trade.entry_price}")
        return trade

    @staticmethod
    def get_by_id(db: Session, trade_id: int) -> Optional[Trade]:
        """Get trade by ID."""
        return db.query(Trade).filter(Trade.id == trade_id).first()

    @staticmethod
    def get_all_open(db: Session, symbol: Optional[str] = None) -> List[Trade]:
        """Get all open trades, optionally filtered by symbol."""
        query = db.query(Trade).filter(Trade.status == "open")
        if symbol:
            query = query.filter(Trade.symbol == symbol)
        return query.order_by(desc(Trade.created_at)).all()

    @staticmethod
    def get_recent(db: Session, days: int = 30, symbol: Optional[str] = None) -> List[Trade]:
        """Get trades from the last N days."""
        cutoff = datetime.utcnow() - timedelta(days=days)
        query = db.query(Trade).filter(Trade.created_at >= cutoff)
        if symbol:
            query = query.filter(Trade.symbol == symbol)
        return query.order_by(desc(Trade.created_at)).all()

    @staticmethod
    def get_by_symbol(db: Session, symbol: str) -> List[Trade]:
        """Get all trades for a symbol."""
        return db.query(Trade).filter(Trade.symbol == symbol).order_by(desc(Trade.created_at)).all()

    @staticmethod
    def get_by_grade(db: Session, grade: TradeGrade) -> List[Trade]:
        """Get trades by grade (A, B, C, D, F)."""
        return db.query(Trade).filter(Trade.grade == grade).order_by(desc(Trade.created_at)).all()

    @staticmethod
    def close_trade(db: Session, trade_id: int, exit_price: float, pnl: float) -> Trade:
        """Close a trade with exit price and P&L."""
        trade = TradeRepository.get_by_id(db, trade_id)
        if not trade:
            raise ValueError(f"Trade {trade_id} not found")
        
        trade.exit_price = exit_price
        trade.pnl = pnl
        trade.pnl_pct = (pnl / (trade.entry_price * trade.quantity)) * 100 if trade.quantity else 0
        trade.status = "closed"
        trade.closed_at = datetime.utcnow()
        
        db.commit()
        db.refresh(trade)
        logger.info(f"Trade closed: {trade.symbol} P&L: {trade.pnl}")
        return trade

    @staticmethod
    def update(db: Session, trade_id: int, **kwargs) -> Trade:
        """Update trade fields."""
        trade = TradeRepository.get_by_id(db, trade_id)
        if not trade:
            raise ValueError(f"Trade {trade_id} not found")
        
        for key, value in kwargs.items():
            if hasattr(trade, key):
                setattr(trade, key, value)
        
        db.commit()
        db.refresh(trade)
        return trade

    @staticmethod
    def delete(db: Session, trade_id: int) -> bool:
        """Delete a trade (soft delete via status change)."""
        trade = TradeRepository.get_by_id(db, trade_id)
        if not trade:
            return False
        
        trade.status = "cancelled"
        db.commit()
        logger.info(f"Trade deleted: {trade.symbol}")
        return True

    @staticmethod
    def get_statistics(db: Session, symbol: Optional[str] = None) -> dict:
        """Get trade statistics."""
        query = db.query(Trade).filter(Trade.status == "closed")
        if symbol:
            query = query.filter(Trade.symbol == symbol)
        
        trades = query.all()
        if not trades:
            return {
                "total": 0,
                "winning": 0,
                "losing": 0,
                "win_rate": 0,
                "total_pnl": 0,
                "avg_pnl": 0,
            }
        
        winning = [t for t in trades if t.pnl > 0]
        losing = [t for t in trades if t.pnl <= 0]
        
        return {
            "total": len(trades),
            "winning": len(winning),
            "losing": len(losing),
            "win_rate": (len(winning) / len(trades) * 100) if trades else 0,
            "total_pnl": sum(t.pnl for t in trades if t.pnl),
            "avg_pnl": (sum(t.pnl for t in trades if t.pnl) / len(trades)) if trades else 0,
        }


class PredictionRepository:
    """Repository for Prediction model operations."""

    @staticmethod
    def create(db: Session, **kwargs):
        """Create and save a new prediction."""
        from models.trade import Prediction
        prediction = Prediction(**kwargs)
        db.add(prediction)
        db.commit()
        db.refresh(prediction)
        logger.info(f"Prediction created: {prediction.symbol} {prediction.signal}")
        return prediction

    @staticmethod
    def get_recent(db: Session, symbol: str, days: int = 7):
        """Get recent predictions for a symbol (by prediction_date)."""
        from models.trade import Prediction
        cutoff = datetime.utcnow() - timedelta(days=days)
        return db.query(Prediction).filter(
            and_(
                Prediction.symbol == symbol,
                Prediction.prediction_date >= cutoff
            )
        ).order_by(desc(Prediction.prediction_date)).all()

    @staticmethod
    def get_accuracy(db: Session, symbol: Optional[str] = None) -> dict:
        """Calculate prediction accuracy."""
        from models.trade import Prediction
        query = db.query(Prediction).filter(Prediction.correct != None)
        if symbol:
            query = query.filter(Prediction.symbol == symbol)
        
        predictions = query.all()
        if not predictions:
            return {"total": 0, "correct": 0, "accuracy": 0}
        
        correct = len([p for p in predictions if p.correct])
        return {
            "total": len(predictions),
            "correct": correct,
            "accuracy": (correct / len(predictions) * 100),
        }


class BacktestResultRepository:
    """Repository for BacktestResult model operations."""

    @staticmethod
    def create(db: Session, **kwargs):
        """Create and save a backtest result."""
        from models.trade import BacktestResult
        result = BacktestResult(**kwargs)
        db.add(result)
        db.commit()
        db.refresh(result)
        logger.info(f"Backtest saved: {result.strategy} {result.symbol}")
        return result

    @staticmethod
    def get_best_strategy(db: Session, symbol: str):
        """Get best performing strategy for a symbol."""
        from models.trade import BacktestResult
        return db.query(BacktestResult).filter(
            BacktestResult.symbol == symbol
        ).order_by(desc(BacktestResult.total_return_pct)).first()

    @staticmethod
    def get_by_strategy(db: Session, strategy: str):
        """Get all results for a strategy."""
        from models.trade import BacktestResult
        return db.query(BacktestResult).filter(
            BacktestResult.strategy == strategy
        ).order_by(desc(BacktestResult.created_at)).all()
