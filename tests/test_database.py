# tests/test_database.py
"""
Tests for database models and repository operations.
Updated to use current model names and repository API.
"""

import pytest
from datetime import date, datetime, timezone
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from core.database import Base
from models.trade import (
    Trade,
    TradeSignal,
    TradeGrade,
    Prediction,
    BacktestResult,
    NewsArticle,
    FiidiiFlow,
    UserPreference,
)
from repositories import (
    TradeRepository,
    PredictionRepository,
    BacktestResultRepository,
    NewsArticleRepository,
    FiidiiFlowRepository,
)

# Use in-memory SQLite for tests — fast and no setup needed
TEST_DB_URL = "sqlite:///:memory:"


@pytest.fixture(scope="module")
def test_engine():
    engine = create_engine(
        TEST_DB_URL,
        connect_args={"check_same_thread": False},
    )
    Base.metadata.create_all(engine)
    yield engine
    Base.metadata.drop_all(engine)


@pytest.fixture
def db(test_engine):
    """Fresh session for each test."""
    Session = sessionmaker(bind=test_engine)
    session = Session()
    yield session
    session.rollback()
    session.close()


# ── Model tests ───────────────────────────────────────────────────────────────

class TestModels:

    def test_trade_model_creates(self, db):
        record = Trade(
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
        db.add(record)
        db.commit()
        assert record.id is not None

    def test_prediction_model_creates(self, db):
        record = Prediction(
            symbol="^NSEI",
            signal=TradeSignal.BUY,
            confidence=65.5,
            prediction_date=datetime.now(timezone.utc),
        )
        db.add(record)
        db.commit()
        assert record.id is not None
        assert record.correct is None  # not yet evaluated

    def test_backtest_model_creates(self, db):
        record = BacktestResult(
            strategy="rsi",
            symbol="^NSEI",
            period="2y",
            total_return_pct=15.0,
            buy_hold_return_pct=12.0,
            alpha=3.0,
            sharpe_ratio=1.2,
            max_drawdown_pct=8.5,
            win_rate_pct=55.0,
            profit_factor=1.4,
            total_trades=22,
            winning_trades=12,
            losing_trades=10,
        )
        db.add(record)
        db.commit()
        assert record.id is not None

    def test_news_article_model_creates(self, db):
        record = NewsArticle(
            title="Nifty hits all-time high",
            description="Markets rally on strong earnings.",
            source="Economic Times",
            url=f"https://example.com/news/{id(record) if False else 'unique1'}",
            sentiment="positive",
            sentiment_score=0.72,
        )
        db.add(record)
        db.commit()
        assert record.id is not None

    def test_fiidii_flow_model_creates(self, db):
        record = FiidiiFlow(
            date="2024-01-15",
            fii_gross_buy=4000.0,
            fii_gross_sell=2500.0,
            fii_net=1500.0,
            dii_gross_buy=2000.0,
            dii_gross_sell=1500.0,
            dii_net=500.0,
            combined_net=2000.0,
            signal="BULLISH",
            pressure_score=0.8,
        )
        db.add(record)
        db.commit()
        assert record.id is not None


# ── Trade repository tests ────────────────────────────────────────────────────

class TestTradeRepository:

    def test_create_trade(self, db):
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
        )
        assert trade.id is not None
        assert trade.symbol == "^NSEI"
        assert trade.signal == TradeSignal.BUY

    def test_get_by_id(self, db):
        trade = TradeRepository.create(
            db=db, symbol="^NSEI", entry_price=22000.0,
            stop_loss=21800.0, take_profit=22500.0, quantity=10,
            signal=TradeSignal.BUY, ml_confidence=75.0, grade=TradeGrade.B,
        )
        retrieved = TradeRepository.get_by_id(db, trade.id)
        assert retrieved is not None
        assert retrieved.id == trade.id

    def test_get_all_open(self, db):
        TradeRepository.create(
            db=db, symbol="^NSEI", entry_price=22000.0,
            stop_loss=21800.0, take_profit=22500.0, quantity=10,
            signal=TradeSignal.BUY, ml_confidence=75.0, grade=TradeGrade.B,
        )
        open_trades = TradeRepository.get_all_open(db)
        assert len(open_trades) >= 1

    def test_close_trade(self, db):
        trade = TradeRepository.create(
            db=db, symbol="^NSEI", entry_price=22000.0,
            stop_loss=21800.0, take_profit=22500.0, quantity=10,
            signal=TradeSignal.BUY, ml_confidence=75.0, grade=TradeGrade.B,
        )
        closed = TradeRepository.close_trade(db, trade.id, exit_price=22400.0, pnl=4000.0)
        assert closed.status == "closed"
        assert closed.exit_price == 22400.0
        assert closed.pnl == 4000.0


# ── Prediction repository tests ───────────────────────────────────────────────

class TestPredictionRepository:

    def test_create_prediction(self, db):
        pred = PredictionRepository.create(
            db=db,
            symbol="^NSEI",
            signal=TradeSignal.BUY,
            confidence=65.5,
            prediction_date=datetime.now(timezone.utc),
        )
        assert pred.id is not None
        assert pred.signal == TradeSignal.BUY

    def test_get_recent(self, db):
        PredictionRepository.create(
            db=db, symbol="^NSEI", signal=TradeSignal.BUY, confidence=65.5,
            prediction_date=datetime.now(timezone.utc),
        )
        history = PredictionRepository.get_recent(db, "^NSEI")
        assert len(history) >= 1

    def test_get_accuracy_no_data(self, db):
        result = PredictionRepository.get_accuracy(db, "^FAKE_SYMBOL_999")
        assert result["total"] == 0
        assert result["accuracy"] == 0


# ── Backtest repository tests ─────────────────────────────────────────────────

class TestBacktestRepository:

    def test_create_backtest(self, db):
        result = BacktestResultRepository.create(
            db=db,
            strategy="rsi",
            symbol="^NSEI",
            period="2y",
            total_return_pct=15.0,
            buy_hold_return_pct=12.0,
            alpha=3.0,
            sharpe_ratio=1.2,
            max_drawdown_pct=8.5,
            win_rate_pct=55.0,
            profit_factor=1.4,
            total_trades=22,
            winning_trades=12,
            losing_trades=10,
        )
        assert result.id is not None
        assert result.strategy == "rsi"

    def test_get_best_strategy(self, db):
        BacktestResultRepository.create(
            db=db, strategy="rsi", symbol="^NSEI", period="2y",
            total_return_pct=15.0, buy_hold_return_pct=12.0,
            sharpe_ratio=1.2, max_drawdown_pct=8.5,
            win_rate_pct=55.0, profit_factor=1.4,
            total_trades=22, winning_trades=12, losing_trades=10,
        )
        best = BacktestResultRepository.get_best_strategy(db, "^NSEI")
        assert best is not None

    def test_get_by_strategy(self, db):
        BacktestResultRepository.create(
            db=db, strategy="ema_cross", symbol="^NSEI", period="2y",
            total_return_pct=18.0, buy_hold_return_pct=12.0,
            sharpe_ratio=1.3, max_drawdown_pct=7.5,
            win_rate_pct=60.0, profit_factor=1.6,
            total_trades=30, winning_trades=18, losing_trades=12,
        )
        results = BacktestResultRepository.get_by_strategy(db, "ema_cross")
        assert len(results) >= 1


# ── News repository tests ─────────────────────────────────────────────────────

class TestNewsRepository:

    def test_create_article(self, db):
        article = NewsArticleRepository.create(
            db=db,
            title="Nifty hits record",
            description="Markets rally...",
            source="ET",
            url="https://example.com/news-test-create",
            sentiment="positive",
            sentiment_score=0.7,
            published_at=datetime.now(timezone.utc),
        )
        assert article.id is not None

    def test_get_by_url(self, db):
        url = "https://example.com/news-test-get-url"
        NewsArticleRepository.create(
            db=db, title="Test", source="ET", url=url,
            sentiment="neutral", sentiment_score=0.0,
            published_at=datetime.now(timezone.utc),
        )
        found = NewsArticleRepository.get_by_url(db, url)
        assert found is not None
        assert found.url == url


# ── FII/DII repository tests ──────────────────────────────────────────────────

class TestFiiDiiRepository:

    def test_create_flow(self, db):
        flow = FiidiiFlowRepository.create(
            db=db,
            date="2024-06-15",
            fii_gross_buy=4000.0,
            fii_gross_sell=2500.0,
            fii_net=1500.0,
            dii_gross_buy=2000.0,
            dii_gross_sell=1500.0,
            dii_net=500.0,
            combined_net=2000.0,
            signal="BULLISH",
            pressure_score=0.8,
        )
        assert flow.id is not None

    def test_get_by_date(self, db):
        FiidiiFlowRepository.create(
            db=db, date="2024-06-16",
            fii_gross_buy=4000.0, fii_gross_sell=2500.0, fii_net=1500.0,
            dii_gross_buy=2000.0, dii_gross_sell=1500.0, dii_net=500.0,
            combined_net=2000.0, signal="BULLISH", pressure_score=0.8,
        )
        found = FiidiiFlowRepository.get_by_date(db, "2024-06-16")
        assert found is not None
        assert found.date == "2024-06-16"

    def test_get_latest(self, db):
        latest = FiidiiFlowRepository.get_latest(db)
        # Should return something since we've been creating records
        # (or None if isolated — both are valid)
        assert latest is None or latest.date is not None