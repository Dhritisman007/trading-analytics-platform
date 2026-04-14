# database/models.py

from datetime import datetime, timezone
from sqlalchemy import (
    Column, Integer, Float, String, Boolean,
    DateTime, Date, Text, JSON, Index,
    UniqueConstraint,
)
from database.engine import Base


def utcnow():
    return datetime.now(timezone.utc)


class MarketDataRecord(Base):
    """
    Stores daily OHLCV candles.
    One row per symbol per date.
    """
    __tablename__ = "market_data"

    id         = Column(Integer, primary_key=True, index=True)
    symbol     = Column(String(20),  nullable=False)
    date       = Column(Date,        nullable=False)
    open       = Column(Float,       nullable=False)
    high       = Column(Float,       nullable=False)
    low        = Column(Float,       nullable=False)
    close      = Column(Float,       nullable=False)
    volume     = Column(Float,       nullable=False)
    interval   = Column(String(10),  nullable=False, default="1d")
    created_at = Column(DateTime(timezone=True), default=utcnow)

    __table_args__ = (
        UniqueConstraint("symbol", "date", "interval", name="uq_market_symbol_date"),
        Index("ix_market_symbol_date", "symbol", "date"),
    )

    def __repr__(self):
        return f"<MarketData {self.symbol} {self.date} close={self.close}>"


class PredictionRecord(Base):
    """
    Stores every ML prediction made by /predict endpoint.
    Used to track real-world accuracy over time.
    """
    __tablename__ = "predictions"

    id                  = Column(Integer,     primary_key=True, index=True)
    symbol              = Column(String(20),  nullable=False)
    signal              = Column(String(10),  nullable=False)   # BUY or SELL
    confidence          = Column(Float,       nullable=False)
    strength            = Column(String(20),  nullable=True)    # strong/moderate/weak
    price_at_prediction = Column(Float,       nullable=True)
    predicted_at        = Column(DateTime(timezone=True), default=utcnow)

    # Outcome — filled in later when we know what happened
    outcome_price       = Column(Float,       nullable=True)
    outcome_direction   = Column(String(10),  nullable=True)    # up or down
    correct             = Column(Boolean,     nullable=True)
    evaluated_at        = Column(DateTime(timezone=True), nullable=True)

    # Context at time of prediction
    rsi_at_prediction   = Column(Float,       nullable=True)
    ema_signal          = Column(String(20),  nullable=True)    # above/below
    macd_crossover      = Column(String(20),  nullable=True)

    # Top features as JSON
    top_features        = Column(JSON,        nullable=True)

    __table_args__ = (
        Index("ix_predictions_symbol_date", "symbol", "predicted_at"),
    )

    def __repr__(self):
        return f"<Prediction {self.symbol} {self.signal} {self.confidence}%>"


class BacktestRecord(Base):
    """
    Stores backtest results for every strategy run.
    Allows comparing runs over time and between strategies.
    """
    __tablename__ = "backtest_results"

    id               = Column(Integer,     primary_key=True, index=True)
    strategy         = Column(String(50),  nullable=False)
    symbol           = Column(String(20),  nullable=False)
    period           = Column(String(10),  nullable=False)
    initial_capital  = Column(Float,       nullable=False)
    final_value      = Column(Float,       nullable=False)
    total_return_pct = Column(Float,       nullable=False)
    sharpe_ratio     = Column(Float,       nullable=True)
    max_drawdown_pct = Column(Float,       nullable=True)
    win_rate_pct     = Column(Float,       nullable=True)
    profit_factor    = Column(Float,       nullable=True)
    total_trades     = Column(Integer,     nullable=True)
    grade            = Column(String(5),   nullable=True)
    buy_hold_return  = Column(Float,       nullable=True)
    alpha            = Column(Float,       nullable=True)

    # Store full result as JSON for future reference
    full_result      = Column(JSON,        nullable=True)
    strategy_params  = Column(JSON,        nullable=True)
    run_at           = Column(DateTime(timezone=True), default=utcnow)

    __table_args__ = (
        Index("ix_backtest_strategy_symbol", "strategy", "symbol"),
    )

    def __repr__(self):
        return (
            f"<Backtest {self.strategy} {self.symbol} "
            f"return={self.total_return_pct}% grade={self.grade}>"
        )


class NewsRecord(Base):
    """
    Stores news articles with sentiment scores.
    Allows sentiment trend analysis over time.
    """
    __tablename__ = "news_articles"

    id              = Column(Integer,     primary_key=True, index=True)
    title           = Column(Text,        nullable=False)
    summary         = Column(Text,        nullable=True)
    url             = Column(Text,        nullable=True)
    source          = Column(String(100), nullable=True)
    published_at    = Column(DateTime(timezone=True), nullable=True)
    fetched_at      = Column(DateTime(timezone=True), default=utcnow)

    # Sentiment
    sentiment_score = Column(Float,       nullable=True)
    sentiment_label = Column(String(20),  nullable=True)
    impact          = Column(String(20),  nullable=True)

    # Metadata
    topics          = Column(JSON,        nullable=True)
    keywords        = Column(JSON,        nullable=True)
    is_breaking     = Column(Boolean,     default=False)

    __table_args__ = (
        Index("ix_news_published_at", "published_at"),
        Index("ix_news_source", "source"),
    )

    def __repr__(self):
        return f"<News {self.source}: {self.title[:50]}>"


class FiiDiiRecord(Base):
    """
    Stores daily FII/DII flow data.
    One row per date.
    """
    __tablename__ = "fii_dii_flows"

    id           = Column(Integer, primary_key=True, index=True)
    date         = Column(Date,    nullable=False, unique=True)

    fii_buy      = Column(Float,   nullable=False)
    fii_sell     = Column(Float,   nullable=False)
    fii_net      = Column(Float,   nullable=False)

    dii_buy      = Column(Float,   nullable=False)
    dii_sell     = Column(Float,   nullable=False)
    dii_net      = Column(Float,   nullable=False)

    combined_net = Column(Float,   nullable=False)
    signal       = Column(String(50), nullable=True)
    created_at   = Column(DateTime(timezone=True), default=utcnow)

    __table_args__ = (
        Index("ix_fii_dii_date", "date"),
    )

    def __repr__(self):
        return f"<FiiDii {self.date} fii_net={self.fii_net}>"