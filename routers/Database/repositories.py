# database/repositories.py

import logging
from datetime import date, datetime, timezone
from sqlalchemy.orm import Session
from sqlalchemy import desc, func

from database.models import (
    MarketDataRecord,
    PredictionRecord,
    BacktestRecord,
    NewsRecord,
    FiiDiiRecord,
)

logger = logging.getLogger(__name__)


# ── Market Data Repository ─────────────────────────────────────────────────────

class MarketRepository:

    @staticmethod
    def save_ohlc(db: Session, symbol: str, candles: list[dict], interval: str = "1d") -> int:
        """
        Save OHLC candles to the database.
        Uses upsert — updates existing records, inserts new ones.
        Returns number of records saved.
        """
        saved = 0
        for candle in candles:
            candle_date = date.fromisoformat(candle["date"])

            # Check if record exists
            existing = db.query(MarketDataRecord).filter_by(
                symbol=symbol,
                date=candle_date,
                interval=interval,
            ).first()

            if existing:
                existing.open   = candle["open"]
                existing.high   = candle["high"]
                existing.low    = candle["low"]
                existing.close  = candle["close"]
                existing.volume = candle["volume"]
            else:
                record = MarketDataRecord(
                    symbol=symbol,
                    date=candle_date,
                    open=candle["open"],
                    high=candle["high"],
                    low=candle["low"],
                    close=candle["close"],
                    volume=candle["volume"],
                    interval=interval,
                )
                db.add(record)
                saved += 1

        db.commit()
        logger.info(f"Saved {saved} new OHLC records for {symbol}")
        return saved

    @staticmethod
    def get_latest(db: Session, symbol: str, limit: int = 30) -> list[MarketDataRecord]:
        """Get the most recent N candles for a symbol."""
        return (
            db.query(MarketDataRecord)
            .filter_by(symbol=symbol)
            .order_by(desc(MarketDataRecord.date))
            .limit(limit)
            .all()
        )


# ── Prediction Repository ──────────────────────────────────────────────────────

class PredictionRepository:

    @staticmethod
    def save(
        db: Session,
        symbol: str,
        signal: str,
        confidence: float,
        price: float,
        strength: str | None = None,
        rsi: float | None = None,
        ema_signal: str | None = None,
        top_features: dict | None = None,
    ) -> PredictionRecord:
        """Save a new prediction to the database."""
        record = PredictionRecord(
            symbol=symbol,
            signal=signal,
            confidence=confidence,
            strength=strength,
            price_at_prediction=price,
            rsi_at_prediction=rsi,
            ema_signal=ema_signal,
            top_features=top_features,
        )
        db.add(record)
        db.commit()
        db.refresh(record)
        logger.debug(f"Saved prediction: {signal} for {symbol}")
        return record

    @staticmethod
    def get_history(
        db: Session,
        symbol: str,
        limit: int = 50,
    ) -> list[PredictionRecord]:
        """Get recent predictions for a symbol."""
        return (
            db.query(PredictionRecord)
            .filter_by(symbol=symbol)
            .order_by(desc(PredictionRecord.predicted_at))
            .limit(limit)
            .all()
        )

    @staticmethod
    def get_accuracy(db: Session, symbol: str) -> dict:
        """Calculate real-world prediction accuracy from stored outcomes."""
        evaluated = (
            db.query(PredictionRecord)
            .filter(
                PredictionRecord.symbol == symbol,
                PredictionRecord.correct.isnot(None),
            )
            .all()
        )

        if not evaluated:
            return {
                "symbol":   symbol,
                "evaluated": 0,
                "accuracy": None,
            }

        correct = sum(1 for p in evaluated if p.correct)
        return {
            "symbol":    symbol,
            "evaluated": len(evaluated),
            "correct":   correct,
            "incorrect": len(evaluated) - correct,
            "accuracy":  round(correct / len(evaluated) * 100, 2),
        }

    @staticmethod
    def update_outcome(
        db: Session,
        prediction_id: int,
        outcome_price: float,
        outcome_direction: str,
        correct: bool,
    ) -> PredictionRecord | None:
        """Update a prediction with its actual outcome."""
        record = db.query(PredictionRecord).filter_by(id=prediction_id).first()
        if record:
            record.outcome_price     = outcome_price
            record.outcome_direction = outcome_direction
            record.correct           = correct
            record.evaluated_at      = datetime.now(timezone.utc)
            db.commit()
        return record


# ── Backtest Repository ────────────────────────────────────────────────────────

class BacktestRepository:

    @staticmethod
    def save(
        db: Session,
        strategy: str,
        symbol: str,
        period: str,
        result: dict,
        params: dict | None = None,
    ) -> BacktestRecord:
        """Save a backtest result to the database."""
        perf = result.get("performance", {})
        bh   = result.get("vs_buy_hold", {})

        record = BacktestRecord(
            strategy=strategy,
            symbol=symbol,
            period=period,
            initial_capital=float(perf.get("initial_capital", 0)),
            final_value=float(perf.get("final_value", 0)),
            total_return_pct=float(perf.get("total_return_pct", 0)),
            sharpe_ratio=float(perf.get("sharpe_ratio", 0)),
            max_drawdown_pct=float(perf.get("max_drawdown_pct", 0)),
            win_rate_pct=float(perf.get("win_rate_pct", 0)),
            profit_factor=float(perf.get("profit_factor", 0)),
            total_trades=result.get("total_trades", 0),
            grade=result.get("grade", {}).get("grade"),
            buy_hold_return=float(bh.get("buy_hold_return_pct", 0)),
            alpha=float(bh.get("alpha", 0)),
            strategy_params=params,
            # Store full result but exclude equity curve (too large)
            full_result={
                k: v for k, v in result.items()
                if k not in ["equity_curve", "recent_trades"]
            },
        )
        db.add(record)
        db.commit()
        db.refresh(record)
        logger.info(f"Saved backtest: {strategy} on {symbol} grade={record.grade}")
        return record

    @staticmethod
    def get_history(
        db: Session,
        symbol: str | None = None,
        strategy: str | None = None,
        limit: int = 20,
    ) -> list[BacktestRecord]:
        """Get backtest history with optional filters."""
        query = db.query(BacktestRecord)
        if symbol:
            query = query.filter_by(symbol=symbol)
        if strategy:
            query = query.filter_by(strategy=strategy)
        return query.order_by(desc(BacktestRecord.run_at)).limit(limit).all()

    @staticmethod
    def get_best(
        db: Session,
        symbol: str = "^NSEI",
    ) -> BacktestRecord | None:
        """Get the best-performing backtest for a symbol."""
        return (
            db.query(BacktestRecord)
            .filter_by(symbol=symbol)
            .order_by(desc(BacktestRecord.total_return_pct))
            .first()
        )


# ── News Repository ────────────────────────────────────────────────────────────

class NewsRepository:

    @staticmethod
    def save_articles(db: Session, articles: list[dict]) -> int:
        """
        Save news articles to the database.
        Skips duplicates based on URL.
        """
        saved = 0
        for article in articles:
            url = article.get("url", "")
            if url:
                existing = db.query(NewsRecord).filter_by(url=url).first()
                if existing:
                    continue

            sentiment = article.get("sentiment", {})
            impact    = article.get("impact", {})

            record = NewsRecord(
                title=article.get("title", ""),
                summary=article.get("summary", ""),
                url=url,
                source=article.get("source", ""),
                published_at=datetime.fromisoformat(
                    article["published_at"].replace("Z", "+00:00")
                ) if article.get("published_at") else None,
                sentiment_score=float(sentiment.get("compound", 0)),
                sentiment_label=sentiment.get("label", "neutral"),
                impact=impact.get("impact", "LOW"),
                topics=article.get("topics", []),
                keywords=article.get("keywords", []),
                is_breaking=article.get("is_breaking", False),
            )
            db.add(record)
            saved += 1

        if saved:
            db.commit()
        logger.debug(f"Saved {saved} new news articles")
        return saved

    @staticmethod
    def get_sentiment_trend(db: Session, days: int = 30) -> list[dict]:
        """
        Get daily average sentiment score over the last N days.
        Used for the sentiment trend chart.
        """
        from sqlalchemy import cast, Float
        from datetime import timedelta

        cutoff = datetime.now(timezone.utc) - timedelta(days=days)

        rows = (
            db.query(
                func.date(NewsRecord.published_at).label("date"),
                func.avg(NewsRecord.sentiment_score).label("avg_sentiment"),
                func.count(NewsRecord.id).label("article_count"),
            )
            .filter(NewsRecord.published_at >= cutoff)
            .group_by(func.date(NewsRecord.published_at))
            .order_by("date")
            .all()
        )

        return [
            {
                "date":          str(row.date),
                "avg_sentiment": round(float(row.avg_sentiment), 4),
                "article_count": row.article_count,
            }
            for row in rows
        ]


# ── FII/DII Repository ─────────────────────────────────────────────────────────

class FiiDiiRepository:

    @staticmethod
    def save_flows(db: Session, flows: list[dict]) -> int:
        """Save FII/DII daily flow records. Skip existing dates."""
        saved = 0
        for flow in flows:
            flow_date = date.fromisoformat(flow["date"])
            existing  = db.query(FiiDiiRecord).filter_by(date=flow_date).first()

            if existing:
                continue

            record = FiiDiiRecord(
                date=flow_date,
                fii_buy=float(flow["fii"]["gross_buy"]),
                fii_sell=float(flow["fii"]["gross_sell"]),
                fii_net=float(flow["fii"]["net"]),
                dii_buy=float(flow["dii"]["gross_buy"]),
                dii_sell=float(flow["dii"]["gross_sell"]),
                dii_net=float(flow["dii"]["net"]),
                combined_net=float(flow["combined_net"]),
                signal=flow.get("signal", {}).get("signal") if isinstance(flow.get("signal"), dict) else None,
            )
            db.add(record)
            saved += 1

        if saved:
            db.commit()
        return saved

    @staticmethod
    def get_history(db: Session, days: int = 30) -> list[FiiDiiRecord]:
        """Get last N days of FII/DII flow records."""
        return (
            db.query(FiiDiiRecord)
            .order_by(desc(FiiDiiRecord.date))
            .limit(days)
            .all()
        )