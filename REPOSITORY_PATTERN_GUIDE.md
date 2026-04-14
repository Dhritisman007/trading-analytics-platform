# REPOSITORY_PATTERN_GUIDE.md

## Repository Pattern Implementation

**Date**: April 14, 2026  
**Status**: ✅ Production Ready  
**Database**: PostgreSQL 15+ with SQLAlchemy ORM

---

## What is the Repository Pattern?

The repository pattern creates a **clean separation of concerns**:

- **Services** contain business logic (calculations, predictions, decisions)
- **Repositories** handle all database access (queries, inserts, updates)
- **Models** represent database tables (ORM models)

This keeps your code testable, maintainable, and decoupled from database specifics.

### Before (Anti-pattern)
```python
# ❌ Service directly queries database - hard to test, database logic mixed with business logic
def get_risk_analysis(symbol: str, db: Session):
    trades = db.query(Trade).filter(Trade.symbol == symbol).all()  # DB access here
    pnl = sum(t.pnl for t in trades)                               # Business logic mixed
    return calculate_risk(pnl)
```

### After (Repository Pattern)
```python
# ✅ Service uses repository - clean separation, easy to test
def get_risk_analysis(symbol: str, db: Session):
    trades = TradeRepository.get_by_symbol(db, symbol)  # Repository handles DB
    pnl = sum(t.pnl for t in trades)                     # Business logic only
    return calculate_risk(pnl)
```

---

## Architecture

```
┌──────────────────────────────────────────────────────────────┐
│ FastAPI Routers (/routers/)                                  │
│ - Handle HTTP requests                                       │
│ - Parse query/body parameters                                │
│ - Call services                                              │
└──────────────────┬───────────────────────────────────────────┘
                   │
┌──────────────────▼───────────────────────────────────────────┐
│ Business Logic (/services/)                                  │
│ - ML predictions                                             │
│ - Risk calculations                                          │
│ - Backtesting                                                │
│ - News sentiment analysis                                    │
└──────────────────┬───────────────────────────────────────────┘
                   │
┌──────────────────▼───────────────────────────────────────────┐
│ Data Access Layer (/repositories/)                           │
│ - TradeRepository                                            │
│ - PredictionRepository                                       │
│ - BacktestResultRepository                                   │
│ - NewsArticleRepository                                      │
│ - FiidiiFlowRepository                                       │
│ - UserPreferenceRepository                                   │
└──────────────────┬───────────────────────────────────────────┘
                   │
┌──────────────────▼───────────────────────────────────────────┐
│ SQLAlchemy ORM (/models/trade.py)                            │
│ - Trade                                                      │
│ - Prediction                                                 │
│ - BacktestResult                                             │
│ - NewsArticle                                                │
│ - FiidiiFlow                                                 │
│ - UserPreference                                             │
└──────────────────┬───────────────────────────────────────────┘
                   │
┌──────────────────▼───────────────────────────────────────────┐
│ PostgreSQL Database                                          │
│ - Concurrent write support                                   │
│ - ACID transactions                                          │
│ - Production-ready                                           │
└──────────────────────────────────────────────────────────────┘
```

---

## Available Repositories

### 1. TradeRepository
Manages trade records and analysis.

```python
from repositories import TradeRepository
from core.database import get_db

# Create a trade
trade = TradeRepository.create(
    db=db_session,
    symbol="^NSEI",
    entry_price=22000.0,
    stop_loss=21800.0,
    take_profit=22500.0,
    quantity=10,
    signal="BUY",
    ml_confidence=78.5,
    grade="A"
)

# Get all open trades
open_trades = TradeRepository.get_all_open(db_session)

# Get trades by symbol
nsei_trades = TradeRepository.get_by_symbol(db_session, "^NSEI")

# Get trades by grade
grade_a_trades = TradeRepository.get_by_grade(db_session, "A")

# Get recent trades (last 30 days)
recent = TradeRepository.get_recent(db_session, days=30)

# Close a trade
closed_trade = TradeRepository.close_trade(
    db_session, 
    trade_id=1, 
    exit_price=22400.0, 
    pnl=4000.0
)

# Get statistics
stats = TradeRepository.get_statistics(db_session, symbol="^NSEI")
# Returns: {
#   "total": 25,
#   "winning": 18,
#   "losing": 7,
#   "win_rate": 72.0,
#   "total_pnl": 45000.0,
#   "avg_pnl": 1800.0
# }
```

### 2. PredictionRepository
Manages ML prediction records for backtesting and accuracy tracking.

```python
from repositories import PredictionRepository

# Create a prediction
pred = PredictionRepository.create(
    db=db_session,
    symbol="^NSEI",
    signal="BUY",
    confidence=78.5,
    prediction_date=datetime.utcnow(),
    top_feature_1="RSI Momentum",
    top_feature_1_contribution=0.34
)

# Get recent predictions
recent_preds = PredictionRepository.get_recent(db_session, symbol="^NSEI", days=7)

# Get accuracy metrics
accuracy = PredictionRepository.get_accuracy(db_session, symbol="^NSEI")
# Returns: {
#   "total": 50,
#   "correct": 36,
#   "accuracy": 72.0
# }
```

### 3. BacktestResultRepository
Manages backtesting results for strategy comparison.

```python
from repositories import BacktestResultRepository

# Save a backtest result
result = BacktestResultRepository.create(
    db=db_session,
    strategy="rsi",
    symbol="^NSEI",
    period="2y",
    total_return_pct=28.5,
    buy_hold_return_pct=15.2,
    sharpe_ratio=1.45,
    max_drawdown_pct=12.3,
    win_rate_pct=68.0,
    profit_factor=2.1,
    total_trades=45,
    winning_trades=31,
    losing_trades=14
)

# Get best strategy for a symbol
best = BacktestResultRepository.get_best_strategy(db_session, "^NSEI")

# Get results for a strategy
rsi_results = BacktestResultRepository.get_by_strategy(db_session, "rsi")
```

### 4. NewsArticleRepository
Manages news articles with sentiment analysis.

```python
from repositories import NewsArticleRepository

# Create a news article
article = NewsArticleRepository.create(
    db=db_session,
    title="RBI raises rates to 6.5%",
    description="Reserve Bank of India...",
    source="Reuters",
    url="https://example.com/news",
    sentiment="negative",
    sentiment_score=-0.45,
    is_market_news=True,
    market_impact="high",
    impact_score=0.85,
    published_at=datetime.utcnow()
)

# Get recent news
recent_news = NewsArticleRepository.get_recent(db_session, days=7, limit=50)

# Get news by sentiment
negative_news = NewsArticleRepository.get_by_sentiment(db_session, "negative", days=7)

# Get market news
market_news = NewsArticleRepository.get_market_news(db_session, days=7)

# Get high-impact news
important = NewsArticleRepository.get_high_impact(db_session, days=7, min_score=0.7)

# Get sentiment aggregate
sentiment = NewsArticleRepository.get_sentiment_aggregate(db_session, days=7)
# Returns: {
#   "total": 45,
#   "positive": 18,
#   "negative": 22,
#   "neutral": 5,
#   "avg_sentiment_score": -0.12
# }

# Archive old articles (delete >90 days old)
deleted = NewsArticleRepository.delete_old(db_session, days=90)
```

### 5. FiidiiFlowRepository
Manages FII/DII flow data for institutional tracking.

```python
from repositories import FiidiiFlowRepository

# Create flow record
flow = FiidiiFlowRepository.create(
    db=db_session,
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

# Get latest flow
latest = FiidiiFlowRepository.get_latest(db_session)

# Get recent flows (30 days)
flows = FiidiiFlowRepository.get_recent(db_session, days=30)

# Get bullish flows only
bullish = FiidiiFlowRepository.get_by_signal(db_session, "BULLISH", days=30)

# Get net trends
trends = FiidiiFlowRepository.get_net_trend(db_session, days=30)
# Returns: {
#   "days": 30,
#   "total_records": 22,
#   "avg_fii_net": 350.5,
#   "avg_dii_net": -125.3,
#   "avg_combined_net": 225.2,
#   "fii_trend": "BULLISH",
#   "dii_trend": "BEARISH"
# }

# Check if latest flow is bullish
is_bullish = FiidiiFlowRepository.is_bullish(db_session, threshold=100.0)
```

### 6. UserPreferenceRepository
Manages user settings and preferences.

```python
from repositories import UserPreferenceRepository

# Create or update preferences
prefs = UserPreferenceRepository.create_or_update(
    db=db_session,
    user_id="user123",
    default_symbol="^NSEI",
    default_risk_pct=1.5,
    default_capital=100000.0,
    notify_strong_signals=True
)

# Get preferences
prefs = UserPreferenceRepository.get_by_user_id(db_session, "user123")

# Get specific settings
symbol = UserPreferenceRepository.get_default_symbol(db_session, "user123")
capital = UserPreferenceRepository.get_default_capital(db_session, "user123")
risk = UserPreferenceRepository.get_risk_preference(db_session, "user123")

# Update preferences
updated = UserPreferenceRepository.update_preferences(
    db=db_session,
    user_id="user123",
    notify_high_impact_news=False,
    default_capital=200000.0
)

# Delete preferences
deleted = UserPreferenceRepository.delete(db_session, "user123")
```

---

## How to Use in Services

### Example 1: Risk Analysis Service

**Before (anti-pattern)**:
```python
def analyze_risk(symbol: str, db: Session):
    # Direct database access - hard to test
    trades = db.query(Trade).filter(Trade.symbol == symbol).all()
    ...
```

**After (repository pattern)**:
```python
from repositories import TradeRepository

def analyze_risk(symbol: str, db: Session):
    # Use repository - clean and testable
    trades = TradeRepository.get_by_symbol(db, symbol)
    
    if not trades:
        return {"risk": "low", "reason": "no_history"}
    
    # Calculate risk metrics
    pnl_data = [t.pnl for t in trades if t.pnl]
    win_rate = len([t for t in trades if t.pnl > 0]) / len(trades)
    
    return {
        "win_rate": win_rate * 100,
        "total_trades": len(trades),
        "avg_pnl": sum(pnl_data) / len(pnl_data) if pnl_data else 0
    }
```

### Example 2: ML Prediction Service

```python
from repositories import PredictionRepository, TradeRepository
from services.ml.predictor import predict

def save_and_analyze_prediction(symbol: str, db: Session):
    # Get prediction
    prediction = predict(symbol=symbol, auto_train=True)
    
    # Save to database
    saved_pred = PredictionRepository.create(
        db=db,
        symbol=symbol,
        signal=prediction["signal"],
        confidence=prediction["confidence"],
        prediction_date=datetime.utcnow(),
        top_feature_1=prediction["top_features"][0]["name"],
        top_feature_1_contribution=prediction["top_features"][0]["contribution"]
    )
    
    # Get recent accuracy
    accuracy = PredictionRepository.get_accuracy(db, symbol)
    
    return {
        "prediction": prediction,
        "saved": True,
        "model_accuracy": accuracy["accuracy"]
    }
```

### Example 3: Backtesting Results Service

```python
from repositories import BacktestResultRepository
from services.backtest.engine import run_backtest

def backtest_and_store(strategy: str, symbol: str, db: Session):
    # Run backtest
    result = run_backtest(
        strategy_name=strategy,
        symbol=symbol,
        period="2y"
    )
    
    # Save result
    saved = BacktestResultRepository.create(
        db=db,
        strategy=strategy,
        symbol=symbol,
        period="2y",
        total_return_pct=result["performance"]["total_return_pct"],
        sharpe_ratio=result["performance"]["sharpe_ratio"],
        max_drawdown_pct=result["performance"]["max_drawdown_pct"],
        win_rate_pct=result["performance"]["win_rate_pct"],
        profit_factor=result["performance"]["profit_factor"],
        total_trades=result["total_trades"],
        winning_trades=len([t for t in result["trades"] if t["pnl"] > 0]),
        losing_trades=len([t for t in result["trades"] if t["pnl"] <= 0])
    )
    
    return saved
```

---

## Database Setup for PostgreSQL

### 1. Install PostgreSQL (Mac)
```bash
brew install postgresql@15
brew services start postgresql@15
export PATH="/opt/homebrew/opt/postgresql@15/bin:$PATH"

# Verify
psql --version
```

### 2. Create Database
```bash
createdb trading_db
psql trading_db -c "SELECT version();"
```

### 3. Configure .env
```bash
# .env
DATABASE_URL="postgresql://localhost/trading_db"
DEBUG="true"
DATA_PROVIDER="yfinance"
```

### 4. Initialize Tables
```python
# Run once at startup (done automatically in main.py)
from core.database import init_db
init_db()
```

---

## Testing Repositories

### Unit Test Example
```python
import pytest
from repositories import TradeRepository
from models.trade import Trade, TradeSignal, TradeGrade
from core.database import SessionLocal

@pytest.fixture
def db():
    db = SessionLocal()
    yield db
    db.close()

def test_create_trade(db):
    trade = TradeRepository.create(
        db=db,
        symbol="^NSEI",
        entry_price=22000.0,
        stop_loss=21800.0,
        take_profit=22500.0,
        quantity=10,
        signal=TradeSignal.BUY,
        ml_confidence=78.5,
        grade=TradeGrade.A
    )
    
    assert trade.id is not None
    assert trade.symbol == "^NSEI"
    
    # Retrieve and verify
    retrieved = TradeRepository.get_by_id(db, trade.id)
    assert retrieved.id == trade.id

def test_get_by_symbol(db):
    # Create multiple trades
    TradeRepository.create(db, symbol="^NSEI", entry_price=22000.0, ...)
    TradeRepository.create(db, symbol="^BSESN", entry_price=73000.0, ...)
    
    nsei_trades = TradeRepository.get_by_symbol(db, "^NSEI")
    assert len(nsei_trades) == 1
    assert nsei_trades[0].symbol == "^NSEI"
```

---

## Migration Path from SQLite to PostgreSQL

### Step 1: Set up PostgreSQL (see above)

### Step 2: Update .env
```bash
# Before
DATABASE_URL="sqlite:///./trading_analytics.db"

# After
DATABASE_URL="postgresql://localhost/trading_db"
```

### Step 3: Verify SQLAlchemy is installed
```bash
pip install sqlalchemy psycopg2-binary
```

### Step 4: Run application
```bash
uvicorn main:app --reload
# Tables are created automatically via init_db()
```

### Step 5: Migrate existing data (if using SQLite)
```python
# migrations/migrate_sqlite_to_postgres.py
from sqlalchemy import create_engine
from core.database import SessionLocal, Base

sqlite_engine = create_engine("sqlite:///./trading_analytics.db")
postgres_session = SessionLocal()

# Query from SQLite, insert into PostgreSQL
# (implementation depends on existing SQLite data)
```

---

## Best Practices

### ✅ DO

- Use repositories for all database access
- Keep services free of database queries
- Use dependency injection (`get_db` dependency)
- Handle exceptions gracefully
- Log repository operations
- Test repositories with real database session
- Use transactions for multi-step operations

### ❌ DON'T

- Query database directly in services
- Mix business logic with database access
- Hardcode database URLs
- Skip error handling
- Create new sessions everywhere (use `get_db`)
- Modify repositories without updating tests

---

## Monitoring & Performance

### Query Performance
```python
# Check slow queries
from core.database import engine
engine.echo = True  # Logs all SQL queries

# Production: use logging instead
import logging
logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)
```

### Connection Pool Status
```python
from core.database import engine
pool = engine.pool
print(f"Connections checked out: {pool.checkedout()}")
print(f"Pool size: {pool.size()}")
print(f"Overflow: {pool.overflow()}")
```

---

## Troubleshooting

### Issue: "No module named 'repositories'"
```python
# Add to sys.path if needed
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
```

### Issue: Database connection error
```bash
# Check PostgreSQL is running
psql -l

# Verify .env DATABASE_URL
cat .env | grep DATABASE_URL

# Test connection
psql trading_db -c "SELECT 1"
```

### Issue: Tables not created
```python
# Force table creation
from core.database import drop_db, init_db
drop_db()
init_db()
```

---

## Next Steps

1. ✅ Create repositories for all models
2. ✅ Update main.py to initialize database
3. 🔄 **Integrate repositories into existing services** (in progress)
4. 🔄 Create service integration examples
5. Create comprehensive test suite for repositories
6. Add Alembic migrations for schema versioning
7. Document repository usage in developer guide
8. Create database backup/restore utilities

---

**Status**: Repository pattern foundation is complete. Ready for service integration and production deployment. 🚀
