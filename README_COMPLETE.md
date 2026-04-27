# Trading Analytics Platform

![CI](https://github.com/YOUR_USERNAME/trading-analytics-platform/actions/workflows/ci.yml/badge.svg)
![Python](https://img.shields.io/badge/Python-3.12-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-0.11-green)
![React](https://img.shields.io/badge/React-18-61DAFB)
![Tests](https://img.shields.io/badge/tests-270%2B%20passing-brightgreen)
![Docker](https://img.shields.io/badge/Docker-ready-2496ED)

An AI-powered trading analytics platform for Indian markets (Nifty 50,
Sensex, Bank Nifty) — built with FastAPI, React, and scikit-learn.

---

## Live features

| Feature | Description |
|---|---|
| Candlestick charts | OHLCV with EMA overlay, volume bars, FVG zones |
| Technical indicators | RSI, EMA, MACD, ATR with beginner tooltips |
| ML predictions | Random Forest buy/sell signals with SHAP-style explainability |
| Risk management | Position sizing, R:R calculator, trade grade (A–F) |
| Backtesting | RSI/EMA/MACD strategies with Sharpe, drawdown, equity curve |
| News sentiment | VADER-scored financial news with market mood gauge |
| FII/DII flows | Institutional flow tracker with pressure score |
| Smart Money Concepts | Fair Value Gap detection with fill status |
| Live price feed | Upstox WebSocket real-time tick data |

## Tech stack

| Layer | Technology |
|---|---|
| Backend | Python 3.12, FastAPI, SQLAlchemy, Alembic |
| ML | scikit-learn (Random Forest), VADER sentiment |
| Data | Upstox API, yfinance (fallback) |
| Database | PostgreSQL |
| Cache | In-memory (Redis-ready) |
| Scheduler | APScheduler |
| Frontend | React 18, Vite, Lightweight Charts, Recharts |
| Testing | pytest — 270+ tests |
| DevOps | Docker, Docker Compose, GitHub Actions |

## Quick start

### Option A — Docker (recommended)

```bash
git clone https://github.com/YOUR_USERNAME/trading-analytics-platform.git
cd trading-analytics-platform

cp .env.example .env
# Edit .env with your credentials

docker compose up --build
```

Open:
- Frontend: http://localhost:3000
- API docs: http://localhost:8000/docs

### Option B — Local development

```bash
# Backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload

# Frontend (new terminal)
cd frontend
npm install
npm run dev
```

## API endpoints