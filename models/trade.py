# models/trade.py
"""
SQLAlchemy models for trading data persistence.
These models store trade history, predictions, and analysis results.
"""

from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, Text, Enum as SQLEnum
from sqlalchemy.sql import func
from core.database import Base
from datetime import datetime
import enum


class TradeSignal(str, enum.Enum):
    """Trade signal types"""
    BUY = "BUY"
    SELL = "SELL"
    HOLD = "HOLD"


class TradeGrade(str, enum.Enum):
    """Trade quality grades"""
    A = "A"
    B = "B"
    C = "C"
    D = "D"
    F = "F"


class Trade(Base):
    """
    Represents a recorded trade or analysis.
    Stores entry, exit, and performance data.
    """
    __tablename__ = "trades"

    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String(20), index=True)
    
    # Trade details
    entry_price = Column(Float)
    exit_price = Column(Float, nullable=True)
    stop_loss = Column(Float)
    take_profit = Column(Float)
    quantity = Column(Integer)
    
    # Trade signals
    signal = Column(SQLEnum(TradeSignal), nullable=True)
    ml_confidence = Column(Float)  # 50-100
    grade = Column(SQLEnum(TradeGrade), nullable=True)  # A-F
    
    # Analysis data
    risk_pct = Column(Float)  # Risk as % of capital
    reward_pct = Column(Float)  # Reward as % of capital
    rr_ratio = Column(Float)  # Risk/reward ratio
    
    # Result tracking
    pnl = Column(Float, nullable=True)  # Profit/loss
    pnl_pct = Column(Float, nullable=True)  # P&L as %
    status = Column(String(20), default="open")  # open, closed, cancelled
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    closed_at = Column(DateTime, nullable=True)
    
    notes = Column(Text, nullable=True)
    
    def __repr__(self):
        return f"<Trade {self.symbol} {self.signal} @ {self.entry_price}>"


class Prediction(Base):
    """
    Stores ML model predictions for historical tracking.
    Allows backtesting predictions against actual prices.
    """
    __tablename__ = "predictions"
    
    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String(20), index=True)
    
    # Prediction data
    signal = Column(SQLEnum(TradeSignal))
    confidence = Column(Float)  # 50-100
    prediction_date = Column(DateTime, index=True)
    
    # Top features
    top_feature_1 = Column(String(100), nullable=True)
    top_feature_1_contribution = Column(Float, nullable=True)
    
    top_feature_2 = Column(String(100), nullable=True)
    top_feature_2_contribution = Column(Float, nullable=True)
    
    top_feature_3 = Column(String(100), nullable=True)
    top_feature_3_contribution = Column(Float, nullable=True)
    
    # Outcome
    actual_signal = Column(SQLEnum(TradeSignal), nullable=True)
    correct = Column(Boolean, nullable=True)  # True/False/None(pending)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    model_version = Column(String(50), nullable=True)
    
    def __repr__(self):
        return f"<Prediction {self.symbol} {self.signal} @ {self.confidence}%>"


class BacktestResult(Base):
    """
    Stores backtesting results for strategy comparison.
    """
    __tablename__ = "backtest_results"
    
    id = Column(Integer, primary_key=True, index=True)
    strategy = Column(String(50), index=True)
    symbol = Column(String(20), index=True)
    period = Column(String(20))  # 1y, 2y, 5y
    
    # Performance metrics
    total_return_pct = Column(Float)
    buy_hold_return_pct = Column(Float)
    alpha = Column(Float)
    
    sharpe_ratio = Column(Float)
    max_drawdown_pct = Column(Float)
    win_rate_pct = Column(Float)
    profit_factor = Column(Float)
    
    # Trade statistics
    total_trades = Column(Integer)
    winning_trades = Column(Integer)
    losing_trades = Column(Integer)
    
    # Parameters
    params = Column(Text, nullable=True)  # JSON string of parameters
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    
    def __repr__(self):
        return f"<BacktestResult {self.strategy} {self.symbol} {self.total_return_pct:.1f}%>"


class NewsArticle(Base):
    """
    Stores news articles for sentiment analysis tracking.
    """
    __tablename__ = "news_articles"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Article details
    title = Column(String(500))
    description = Column(Text)
    source = Column(String(100))
    url = Column(String(500), unique=True, index=True)
    
    # Sentiment
    sentiment = Column(String(20))  # positive, negative, neutral
    sentiment_score = Column(Float)  # -1 to 1
    
    # Topics
    is_market_news = Column(Boolean, default=False)
    is_rbi_news = Column(Boolean, default=False)
    is_earnings_news = Column(Boolean, default=False)
    
    market_impact = Column(String(20), nullable=True)  # high, medium, low
    impact_score = Column(Float, nullable=True)
    
    # Metadata
    published_at = Column(DateTime)
    fetched_at = Column(DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f"<NewsArticle {self.sentiment} - {self.title[:50]}...>"


class FiidiiFlow(Base):
    """
    Stores FII/DII flow data for institutional tracking.
    """
    __tablename__ = "fiidii_flows"
    
    id = Column(Integer, primary_key=True, index=True)
    date = Column(String(10), index=True)  # YYYY-MM-DD
    
    # FII data
    fii_gross_buy = Column(Float)
    fii_gross_sell = Column(Float)
    fii_net = Column(Float, index=True)
    
    # DII data
    dii_gross_buy = Column(Float)
    dii_gross_sell = Column(Float)
    dii_net = Column(Float, index=True)
    
    # Combined
    combined_net = Column(Float)
    
    # Signals
    signal = Column(String(50))  # BULLISH, BEARISH, etc.
    pressure_score = Column(Float)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    
    def __repr__(self):
        return f"<FiidiiFlow {self.date} FII:{self.fii_net} DII:{self.dii_net}>"


class UserPreference(Base):
    """
    Stores user preferences and settings.
    """
    __tablename__ = "user_preferences"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String(50), unique=True, index=True)
    
    # Trading preferences
    default_symbol = Column(String(20), default="^NSEI")
    default_risk_pct = Column(Float, default=1.0)
    default_capital = Column(Float, nullable=True)
    
    # Notification preferences
    notify_strong_signals = Column(Boolean, default=True)
    notify_market_mood_change = Column(Boolean, default=True)
    notify_high_impact_news = Column(Boolean, default=True)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f"<UserPreference {self.user_id}>"
