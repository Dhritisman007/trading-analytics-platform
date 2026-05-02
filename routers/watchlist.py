from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel
from routers.Database.engine import get_db
from routers.Database.models import WatchlistItem

router = APIRouter(prefix="/watchlist", tags=["Watchlist"])

VALID_SYMBOLS = {
    "^NSEI":    "Nifty 50",
    "^BSESN":   "BSE Sensex",
    "^NSEBANK": "Bank Nifty",
    "^CNXMIDCAP": "Nifty Midcap 100",
}


class WatchlistAdd(BaseModel):
    symbol: str
    notes:  str = ""


@router.get("/")
def get_watchlist(db: Session = Depends(get_db)):
    """Get all watchlist items."""
    items = db.query(WatchlistItem).order_by(WatchlistItem.added_at).all()
    return {
        "items": [
            {
                "id":       item.id,
                "symbol":   item.symbol,
                "name":     item.name or VALID_SYMBOLS.get(item.symbol, item.symbol),
                "added_at": item.added_at.isoformat() if item.added_at else None,
                "notes":    item.notes,
            }
            for item in items
        ],
        "count": len(items),
    }


@router.post("/")
def add_to_watchlist(payload: WatchlistAdd, db: Session = Depends(get_db)):
    """Add a symbol to watchlist."""
    existing = db.query(WatchlistItem).filter_by(symbol=payload.symbol).first()
    if existing:
        raise HTTPException(status_code=409, detail=f"{payload.symbol} already in watchlist")

    item = WatchlistItem(
        symbol=payload.symbol,
        name=VALID_SYMBOLS.get(payload.symbol, payload.symbol),
        notes=payload.notes,
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    return {"status": "added", "symbol": item.symbol, "id": item.id}


@router.delete("/{symbol}")
def remove_from_watchlist(symbol: str, db: Session = Depends(get_db)):
    """Remove a symbol from watchlist."""
    item = db.query(WatchlistItem).filter_by(symbol=symbol).first()
    if not item:
        raise HTTPException(status_code=404, detail=f"{symbol} not in watchlist")
    db.delete(item)
    db.commit()
    return {"status": "removed", "symbol": symbol}
