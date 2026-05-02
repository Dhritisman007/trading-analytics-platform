from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc
from pydantic import BaseModel
from datetime import datetime, timezone
from typing import Optional
from routers.Database.engine import get_db
from routers.Database.models import TradeJournalEntry
from utils.formatters import format_number

router = APIRouter(prefix="/journal", tags=["Trade Journal"])


class TradeCreate(BaseModel):
    symbol:      str
    direction:   str           # LONG or SHORT
    entry_price: float
    stop_loss:   Optional[float] = None
    target:      Optional[float] = None
    quantity:    Optional[int]   = None
    entry_date:  Optional[str]   = None
    setup:       Optional[str]   = None
    notes:       Optional[str]   = None
    tags:        Optional[list]  = None


class TradeClose(BaseModel):
    exit_price: float
    exit_date:  Optional[str] = None
    notes:      Optional[str] = None


@router.get("/")
def get_trades(
    symbol:    str | None = Query(default=None),
    status:    str | None = Query(default=None),
    limit:     int        = Query(default=50, ge=1, le=200),
    db: Session = Depends(get_db),
):
    """Get all journal entries with optional filters."""
    query = db.query(TradeJournalEntry)
    if symbol:
        query = query.filter_by(symbol=symbol)
    if status:
        query = query.filter_by(status=status)

    trades = query.order_by(desc(TradeJournalEntry.entry_date)).limit(limit).all()

    result = []
    for t in trades:
        result.append({
            "id":          t.id,
            "symbol":      t.symbol,
            "direction":   t.direction,
            "entry_price": t.entry_price,
            "exit_price":  t.exit_price,
            "stop_loss":   t.stop_loss,
            "target":      t.target,
            "quantity":    t.quantity,
            "entry_date":  t.entry_date.isoformat() if t.entry_date else None,
            "exit_date":   t.exit_date.isoformat()  if t.exit_date  else None,
            "pnl":         t.pnl,
            "pnl_pct":     t.pnl_pct,
            "status":      t.status,
            "setup":       t.setup,
            "notes":       t.notes,
            "tags":        t.tags or [],
        })

    # Stats
    closed      = [t for t in result if t["status"] == "closed"]
    winners     = [t for t in closed if (t["pnl"] or 0) > 0]
    total_pnl   = sum(t["pnl"] or 0 for t in closed)
    win_rate    = round(len(winners) / len(closed) * 100, 1) if closed else 0

    return {
        "trades": result,
        "count":  len(result),
        "stats": {
            "total_trades": len(closed),
            "open_trades":  len([t for t in result if t["status"] == "open"]),
            "winners":      len(winners),
            "losers":       len(closed) - len(winners),
            "win_rate_pct": win_rate,
            "total_pnl":    format_number(total_pnl),
        },
    }


@router.post("/")
def add_trade(payload: TradeCreate, db: Session = Depends(get_db)):
    """Log a new trade."""
    entry_date = (
        datetime.fromisoformat(payload.entry_date)
        if payload.entry_date
        else datetime.now(timezone.utc)
    )

    trade = TradeJournalEntry(
        symbol=payload.symbol,
        direction=payload.direction.upper(),
        entry_price=payload.entry_price,
        stop_loss=payload.stop_loss,
        target=payload.target,
        quantity=payload.quantity,
        entry_date=entry_date,
        setup=payload.setup,
        notes=payload.notes,
        tags=payload.tags or [],
        status="open",
    )
    db.add(trade)
    db.commit()
    db.refresh(trade)
    return {"status": "created", "id": trade.id}


@router.patch("/{trade_id}/close")
def close_trade(
    trade_id: int,
    payload:  TradeClose,
    db: Session = Depends(get_db),
):
    """Close an open trade and calculate P&L."""
    trade = db.query(TradeJournalEntry).filter_by(id=trade_id).first()
    if not trade:
        raise HTTPException(status_code=404, detail="Trade not found")

    trade.exit_price = payload.exit_price
    trade.exit_date  = (
        datetime.fromisoformat(payload.exit_date)
        if payload.exit_date
        else datetime.now(timezone.utc)
    )
    trade.status = "closed"

    if payload.notes:
        trade.notes = f"{trade.notes or ''}\n[Exit] {payload.notes}".strip()

    # Calculate P&L
    if trade.direction == "LONG":
        trade.pnl = (payload.exit_price - trade.entry_price) * (trade.quantity or 1)
    else:
        trade.pnl = (trade.entry_price - payload.exit_price) * (trade.quantity or 1)

    trade.pnl_pct = round(trade.pnl / (trade.entry_price * (trade.quantity or 1)) * 100, 2)

    db.commit()
    return {
        "status":  "closed",
        "pnl":     format_number(trade.pnl),
        "pnl_pct": trade.pnl_pct,
    }


@router.delete("/{trade_id}")
def delete_trade(trade_id: int, db: Session = Depends(get_db)):
    """Delete a trade entry."""
    trade = db.query(TradeJournalEntry).filter_by(id=trade_id).first()
    if not trade:
        raise HTTPException(status_code=404, detail="Trade not found")
    db.delete(trade)
    db.commit()
    return {"status": "deleted"}
