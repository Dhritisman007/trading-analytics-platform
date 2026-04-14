"""
tests/test_repositories.py

Comprehensive tests for repository pattern implementation.
Tests all CRUD operations and query methods for each repository.
"""

import pytest
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from core.database import SessionLocal, Base, engine
from models.trade import (
    Trade, TradeSignal, TradeGrade,
    Prediction, BacktestResult,
    NewsArticle, FiidiiFlow, UserPreference
)
from repositories import (
    TradeRepository,
    PredictionRepository,
    BacktestResultRepository,
    NewsArticleRepository,
    FiidiiFlowRepository,
    UserPreferenceRepository,
)


@pytest.fixture(scope="function")
def db():
    """Create a new database session for each test."""
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    yield db
    db.close()
    Base.metadata.drop_all(bind=engine)


# ═══════════════════════════════════════════════════════════════════════════════
# TRADE REPOSITORY TESTS
# ═══════════════════════════════════════════════════════════════════════════════

class TestTradeRepository:
    """Tests for TradeRepository CRUD operations."""

    def test_create_trade(self, db):
        """Test creating a trade record."""
        trade = TradeRepository.create(
            db=db,
            symbol="^NSEI",
            entry_price=22000.0,
            stop_loss=21800.0,
            take_profit=22500.0,
            quantity=10,
            signal=TradeSignal.BUY,
            ml_confidence=78.5,
            grade=TradeGrade.A,
            risk_pct=1.0,
            reward_pct=2.27,
            rr_ratio=2.27,
        )

        assert trade.id is not None
        assert trade.symbol == "^NSEI"
        assert trade.signal == TradeSignal.BUY
        assert trade.status == "open"

    def test_get_by_id(self, db):
        """Test retrieving a trade by ID."""
        trade = TradeRepository.create(
            db=db, symbol="^NSEI", entry_price=22000.0,
            stop_loss=21800.0, take_profit=22500.0, quantity=10,
            signal=TradeSignal.BUY, ml_confidence=75.0, grade=TradeGrade.B
        )

        retrieved = TradeRepository.get_by_id(db, trade.id)
        assert retrieved is not None
        assert retrieved.id == trade.id
        assert retrieved.symbol == "^NSEI"

    def test_get_all_open(self, db):
        """Test getting all open trades."""
        TradeRepository.create(
            db=db, symbol="^NSEI", entry_price=22000.0,
            stop_loss=21800.0, take_profit=22500.0, quantity=10,
            signal=TradeSignal.BUY, ml_confidence=75.0, grade=TradeGrade.B
        )
        TradeRepository.create(
            db=db, symbol="^BSESN", entry_price=73000.0,
            stop_loss=72000.0, take_profit=74500.0, quantity=5,
            signal=TradeSignal.SELL, ml_confidence=72.0, grade=TradeGrade.C
        )

        open_trades = TradeRepository.get_all_open(db)
        assert len(open_trades) == 2

    def test_get_by_symbol(self, db):
        """Test filtering trades by symbol."""
        TradeRepository.create(
            db=db, symbol="^NSEI", entry_price=22000.0,
            stop_loss=21800.0, take_profit=22500.0, quantity=10,
            signal=TradeSignal.BUY, ml_confidence=75.0, grade=TradeGrade.B
        )
        TradeRepository.create(
            db=db, symbol="^BSESN", entry_price=73000.0,
            stop_loss=72000.0, take_profit=74500.0, quantity=5,
            signal=TradeSignal.SELL, ml_confidence=72.0, grade=TradeGrade.C
        )

        nsei_trades = TradeRepository.get_by_symbol(db, "^NSEI")
        assert len(nsei_trades) == 1
        assert nsei_trades[0].symbol == "^NSEI"

    def test_get_by_grade(self, db):
        """Test filtering trades by grade."""
        TradeRepository.create(
            db=db, symbol="^NSEI", entry_price=22000.0,
            stop_loss=21800.0, take_profit=22500.0, quantity=10,
            signal=TradeSignal.BUY, ml_confidence=85.0, grade=TradeGrade.A
        )
        TradeRepository.create(
            db=db, symbol="^NSEI", entry_price=22100.0,
            stop_loss=21900.0, take_profit=22600.0, quantity=5,
            signal=TradeSignal.BUY, ml_confidence=72.0, grade=TradeGrade.C
        )

        grade_a = TradeRepository.get_by_grade(db, TradeGrade.A)
        assert len(grade_a) == 1
        assert grade_a[0].grade == TradeGrade.A

    def test_close_trade(self, db):
        """Test closing a trade."""
        trade = TradeRepository.create(
            db=db, symbol="^NSEI", entry_price=22000.0,
            stop_loss=21800.0, take_profit=22500.0, quantity=10,
            signal=TradeSignal.BUY, ml_confidence=75.0, grade=TradeGrade.B
        )

        closed = TradeRepository.close_trade(db, trade.id, exit_price=22400.0, pnl=4000.0)
        assert closed.status == "closed"
        assert closed.exit_price == 22400.0
        assert closed.pnl == 4000.0

    def test_get_statistics(self, db):
        """Test getting trade statistics."""
        TradeRepository.create(
            db=db, symbol="^NSEI", entry_price=22000.0,
            stop_loss=21800.0, take_profit=22500.0, quantity=10,
            signal=TradeSignal.BUY, ml_confidence=75.0, grade=TradeGrade.B
        )
        trade2 = TradeRepository.create(
            db=db, symbol="^NSEI", entry_price=22100.0,
            stop_loss=21900.0, take_profit=22600.0, quantity=10,
            signal=TradeSignal.BUY, ml_confidence=75.0, grade=TradeGrade.B
        )

        # Close trades with different outcomes
        TradeRepository.close_trade(db, trade2.id, exit_price=22400.0, pnl=3000.0)

        stats = TradeRepository.get_statistics(db, symbol="^NSEI")
        assert stats["total"] == 1  # Only closed trades
        assert stats["total_pnl"] == 3000.0


# ═══════════════════════════════════════════════════════════════════════════════
# PREDICTION REPOSITORY TESTS
# ═══════════════════════════════════════════════════════════════════════════════

class TestPredictionRepository:
    """Tests for PredictionRepository operations."""

    def test_create_prediction(self, db):
        """Test creating a prediction record."""
        pred = PredictionRepository.create(
            db=db,
            symbol="^NSEI",
            signal=TradeSignal.BUY,
            confidence=78.5,
            prediction_date=datetime.utcnow(),
            top_feature_1="RSI Momentum",
            top_feature_1_contribution=0.34,
            model_version="v1.0"
        )

        assert pred.id is not None
        assert pred.symbol == "^NSEI"
        assert pred.signal == TradeSignal.BUY
        assert pred.confidence == 78.5

    def test_get_recent_predictions(self, db):
        """Test getting recent predictions."""
        PredictionRepository.create(
            db=db, symbol="^NSEI", signal=TradeSignal.BUY, confidence=78.0,
            prediction_date=datetime.utcnow()
        )
        PredictionRepository.create(
            db=db, symbol="^NSEI", signal=TradeSignal.SELL, confidence=72.0,
            prediction_date=datetime.utcnow() - timedelta(days=10)  # Old
        )

        recent = PredictionRepository.get_recent(db, symbol="^NSEI", days=7)
        assert len(recent) == 1
        assert recent[0].signal == TradeSignal.BUY

    def test_get_accuracy(self, db):
        """Test calculating prediction accuracy."""
        # Create predictions with known outcomes
        PredictionRepository.create(
            db=db, symbol="^NSEI", signal=TradeSignal.BUY, confidence=78.0,
            prediction_date=datetime.utcnow(), correct=True
        )
        PredictionRepository.create(
            db=db, symbol="^NSEI", signal=TradeSignal.SELL, confidence=72.0,
            prediction_date=datetime.utcnow(), correct=False
        )
        PredictionRepository.create(
            db=db, symbol="^NSEI", signal=TradeSignal.BUY, confidence=75.0,
            prediction_date=datetime.utcnow(), correct=True
        )

        accuracy = PredictionRepository.get_accuracy(db, symbol="^NSEI")
        assert accuracy["total"] == 3
        assert accuracy["correct"] == 2
        assert accuracy["accuracy"] == pytest.approx(66.67, abs=0.1)


# ═══════════════════════════════════════════════════════════════════════════════
# BACKTEST RESULT REPOSITORY TESTS
# ═══════════════════════════════════════════════════════════════════════════════

class TestBacktestResultRepository:
    """Tests for BacktestResultRepository operations."""

    def test_create_backtest_result(self, db):
        """Test creating a backtest result."""
        result = BacktestResultRepository.create(
            db=db,
            strategy="rsi",
            symbol="^NSEI",
            period="2y",
            total_return_pct=28.5,
            buy_hold_return_pct=15.2,
            alpha=0.13,
            sharpe_ratio=1.45,
            max_drawdown_pct=12.3,
            win_rate_pct=68.0,
            profit_factor=2.1,
            total_trades=45,
            winning_trades=31,
            losing_trades=14
        )

        assert result.id is not None
        assert result.strategy == "rsi"
        assert result.total_return_pct == 28.5

    def test_get_best_strategy(self, db):
        """Test getting best performing strategy."""
        BacktestResultRepository.create(
            db=db, strategy="rsi", symbol="^NSEI", period="2y",
            total_return_pct=28.5, buy_hold_return_pct=15.2,
            sharpe_ratio=1.45, max_drawdown_pct=12.3,
            win_rate_pct=68.0, profit_factor=2.1,
            total_trades=45, winning_trades=31, losing_trades=14
        )
        BacktestResultRepository.create(
            db=db, strategy="ema_cross", symbol="^NSEI", period="2y",
            total_return_pct=35.8, buy_hold_return_pct=15.2,
            sharpe_ratio=1.62, max_drawdown_pct=10.5,
            win_rate_pct=72.0, profit_factor=2.4,
            total_trades=38, winning_trades=27, losing_trades=11
        )

        best = BacktestResultRepository.get_best_strategy(db, "^NSEI")
        assert best.strategy == "ema_cross"
        assert best.total_return_pct == 35.8

    def test_get_by_strategy(self, db):
        """Test getting all results for a strategy."""
        BacktestResultRepository.create(
            db=db, strategy="rsi", symbol="^NSEI", period="2y",
            total_return_pct=28.5, buy_hold_return_pct=15.2,
            sharpe_ratio=1.45, max_drawdown_pct=12.3,
            win_rate_pct=68.0, profit_factor=2.1,
            total_trades=45, winning_trades=31, losing_trades=14
        )
        BacktestResultRepository.create(
            db=db, strategy="rsi", symbol="^BSESN", period="2y",
            total_return_pct=32.1, buy_hold_return_pct=18.0,
            sharpe_ratio=1.51, max_drawdown_pct=11.2,
            win_rate_pct=70.0, profit_factor=2.2,
            total_trades=40, winning_trades=28, losing_trades=12
        )

        rsi_results = BacktestResultRepository.get_by_strategy(db, "rsi")
        assert len(rsi_results) == 2


# ═══════════════════════════════════════════════════════════════════════════════
# NEWS ARTICLE REPOSITORY TESTS
# ═══════════════════════════════════════════════════════════════════════════════

class TestNewsArticleRepository:
    """Tests for NewsArticleRepository operations."""

    def test_create_article(self, db):
        """Test creating a news article."""
        article = NewsArticleRepository.create(
            db=db,
            title="RBI raises rates to 6.5%",
            description="Reserve Bank announces...",
            source="Reuters",
            url="https://example.com/news",
            sentiment="negative",
            sentiment_score=-0.45,
            is_market_news=True,
            market_impact="high",
            impact_score=0.85,
            published_at=datetime.utcnow()
        )

        assert article.id is not None
        assert article.sentiment == "negative"
        assert article.is_market_news is True

    def test_get_by_sentiment(self, db):
        """Test filtering articles by sentiment."""
        NewsArticleRepository.create(
            db=db, title="Positive", sentiment="positive", sentiment_score=0.45,
            source="Reuters", url="https://example1.com", published_at=datetime.utcnow()
        )
        NewsArticleRepository.create(
            db=db, title="Negative", sentiment="negative", sentiment_score=-0.45,
            source="Reuters", url="https://example2.com", published_at=datetime.utcnow()
        )

        negative = NewsArticleRepository.get_by_sentiment(db, "negative", days=7)
        assert len(negative) == 1
        assert negative[0].sentiment == "negative"

    def test_get_sentiment_aggregate(self, db):
        """Test getting sentiment aggregate."""
        NewsArticleRepository.create(
            db=db, title="Positive1", sentiment="positive", sentiment_score=0.45,
            source="Reuters", url="https://ex1.com", published_at=datetime.utcnow()
        )
        NewsArticleRepository.create(
            db=db, title="Positive2", sentiment="positive", sentiment_score=0.50,
            source="Reuters", url="https://ex2.com", published_at=datetime.utcnow()
        )
        NewsArticleRepository.create(
            db=db, title="Negative", sentiment="negative", sentiment_score=-0.45,
            source="Reuters", url="https://ex3.com", published_at=datetime.utcnow()
        )

        agg = NewsArticleRepository.get_sentiment_aggregate(db, days=7)
        assert agg["total"] == 3
        assert agg["positive"] == 2
        assert agg["negative"] == 1


# ═══════════════════════════════════════════════════════════════════════════════
# FIIDII FLOW REPOSITORY TESTS
# ═══════════════════════════════════════════════════════════════════════════════

class TestFiidiiFlowRepository:
    """Tests for FiidiiFlowRepository operations."""

    def test_create_flow(self, db):
        """Test creating FII/DII flow record."""
        flow = FiidiiFlowRepository.create(
            db=db,
            date="2026-04-14",
            fii_gross_buy=2500.0,
            fii_gross_sell=2100.0,
            fii_net=400.0,
            dii_gross_buy=1800.0,
            dii_gross_sell=2200.0,
            dii_net=-400.0,
            combined_net=0.0,
            signal="NEUTRAL",
            pressure_score=0.5
        )

        assert flow.id is not None
        assert flow.date == "2026-04-14"
        assert flow.fii_net == 400.0

    def test_get_latest(self, db):
        """Test getting latest flow."""
        FiidiiFlowRepository.create(
            db=db, date="2026-04-12", fii_net=200.0, dii_net=-100.0,
            fii_gross_buy=2000.0, fii_gross_sell=1800.0,
            dii_gross_buy=1500.0, dii_gross_sell=1600.0,
            combined_net=100.0, signal="BULLISH", pressure_score=0.6
        )
        FiidiiFlowRepository.create(
            db=db, date="2026-04-14", fii_net=400.0, dii_net=-200.0,
            fii_gross_buy=2500.0, fii_gross_sell=2100.0,
            dii_gross_buy=1800.0, dii_gross_sell=2000.0,
            combined_net=200.0, signal="BULLISH", pressure_score=0.7
        )

        latest = FiidiiFlowRepository.get_latest(db)
        assert latest.date == "2026-04-14"

    def test_get_net_trend(self, db):
        """Test getting net flow trends."""
        FiidiiFlowRepository.create(
            db=db, date="2026-04-12", fii_net=300.0, dii_net=100.0,
            fii_gross_buy=2000.0, fii_gross_sell=1700.0,
            dii_gross_buy=1600.0, dii_gross_sell=1500.0,
            combined_net=400.0, signal="BULLISH", pressure_score=0.7
        )
        FiidiiFlowRepository.create(
            db=db, date="2026-04-13", fii_net=500.0, dii_net=-50.0,
            fii_gross_buy=2500.0, fii_gross_sell=2000.0,
            dii_gross_buy=1500.0, dii_gross_sell=1550.0,
            combined_net=450.0, signal="BULLISH", pressure_score=0.8
        )

        trend = FiidiiFlowRepository.get_net_trend(db, days=30)
        assert trend["fii_trend"] == "BULLISH"
        assert trend["total_records"] == 2

    def test_is_bullish(self, db):
        """Test checking if latest flow is bullish."""
        FiidiiFlowRepository.create(
            db=db, date="2026-04-14", fii_net=400.0, dii_net=-200.0,
            fii_gross_buy=2500.0, fii_gross_sell=2100.0,
            dii_gross_buy=1800.0, dii_gross_sell=2000.0,
            combined_net=200.0, signal="BULLISH", pressure_score=0.7
        )

        is_bullish = FiidiiFlowRepository.is_bullish(db, threshold=100.0)
        assert is_bullish is True


# ═══════════════════════════════════════════════════════════════════════════════
# USER PREFERENCE REPOSITORY TESTS
# ═══════════════════════════════════════════════════════════════════════════════

class TestUserPreferenceRepository:
    """Tests for UserPreferenceRepository operations."""

    def test_create_or_update_new(self, db):
        """Test creating a new user preference."""
        pref = UserPreferenceRepository.create_or_update(
            db=db,
            user_id="user123",
            default_symbol="^NSEI",
            default_risk_pct=1.5,
            notify_strong_signals=True
        )

        assert pref.user_id == "user123"
        assert pref.default_symbol == "^NSEI"

    def test_create_or_update_existing(self, db):
        """Test updating existing user preference."""
        UserPreferenceRepository.create_or_update(
            db=db, user_id="user123", default_symbol="^NSEI", default_risk_pct=1.0
        )

        updated = UserPreferenceRepository.create_or_update(
            db=db, user_id="user123", default_symbol="^BSESN", default_risk_pct=2.0
        )

        assert updated.default_symbol == "^BSESN"
        assert updated.default_risk_pct == 2.0

    def test_get_by_user_id(self, db):
        """Test retrieving user preferences."""
        UserPreferenceRepository.create_or_update(
            db=db, user_id="user123", default_symbol="^NSEI"
        )

        pref = UserPreferenceRepository.get_by_user_id(db, "user123")
        assert pref is not None
        assert pref.user_id == "user123"

    def test_get_default_symbol(self, db):
        """Test getting default symbol."""
        UserPreferenceRepository.create_or_update(
            db=db, user_id="user123", default_symbol="^BSESN"
        )

        symbol = UserPreferenceRepository.get_default_symbol(db, "user123")
        assert symbol == "^BSESN"

    def test_get_risk_preference(self, db):
        """Test getting risk preference."""
        UserPreferenceRepository.create_or_update(
            db=db, user_id="user123", default_risk_pct=2.5
        )

        risk = UserPreferenceRepository.get_risk_preference(db, "user123")
        assert risk == 2.5

    def test_delete(self, db):
        """Test deleting user preferences."""
        UserPreferenceRepository.create_or_update(
            db=db, user_id="user123", default_symbol="^NSEI"
        )

        deleted = UserPreferenceRepository.delete(db, "user123")
        assert deleted is True

        pref = UserPreferenceRepository.get_by_user_id(db, "user123")
        assert pref is None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
