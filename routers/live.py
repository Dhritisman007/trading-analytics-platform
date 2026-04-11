# routers/live.py

import json

from fastapi import APIRouter
from fastapi import HTTPException
from fastapi import WebSocket
from fastapi import WebSocketDisconnect

from services.websocket_manager import get_all_ticks
from services.websocket_manager import get_live_tick
from services.websocket_manager import is_connected
from services.websocket_manager import register_client
from services.websocket_manager import unregister_client

router = APIRouter(prefix="/live", tags=["Live Market Feed"])

# Map your symbol names to instrument keys for the REST endpoint
SYMBOL_TO_KEY = {
    "^NSEI": "NSE_INDEX|Nifty 50",
    "^BSESN": "BSE_INDEX|SENSEX",
    "^NSEBANK": "NSE_INDEX|Nifty Bank",
}


@router.get("/status")
def live_status():
    """Check if the Upstox WebSocket feed is connected."""
    return {
        "connected": is_connected(),
        "symbols": list(SYMBOL_TO_KEY.keys()),
    }


@router.get("/{symbol}")
def get_live_price(symbol: str):
    """
    Get the latest live price for a symbol.
    Returns the most recent tick received from Upstox WebSocket.
    This is a REST snapshot — for streaming, use the /ws endpoint.
    """
    instrument_key = SYMBOL_TO_KEY.get(symbol)
    if not instrument_key:
        raise HTTPException(
            status_code=404,
            detail=f"Symbol '{symbol}' not supported for live feed. "
            f"Use: {list(SYMBOL_TO_KEY.keys())}",
        )

    tick = get_live_tick(instrument_key)
    if not tick:
        raise HTTPException(
            status_code=503,
            detail="No live data yet. WebSocket feed may still be connecting.",
        )

    return {
        "symbol": symbol,
        "instrument": instrument_key,
        **tick,
    }


@router.get("/")
def get_all_live_prices():
    """Get latest tick for all subscribed instruments."""
    ticks = get_all_ticks()
    if not ticks:
        return {"connected": is_connected(), "ticks": {}}

    return {
        "connected": is_connected(),
        "ticks": ticks,
    }


@router.websocket("/ws/feed")
async def websocket_feed(websocket: WebSocket):
    """
    WebSocket endpoint for your React dashboard.
    Connect from React with:
      const ws = new WebSocket('ws://localhost:8000/live/ws/feed')
      ws.onmessage = (e) => console.log(JSON.parse(e.data))

    Each message has shape:
      { "type": "tick", "data": { "NSE_INDEX|Nifty 50": { "ltp": 22450.5, ... } } }
    """
    await websocket.accept()
    await register_client(websocket)

    # Send current snapshot immediately on connect
    current_ticks = get_all_ticks()
    if current_ticks:
        await websocket.send_text(
            json.dumps(
                {
                    "type": "snapshot",
                    "data": current_ticks,
                }
            )
        )

    try:
        # Keep connection alive — client can send pings
        while True:
            await websocket.receive_text()

    except WebSocketDisconnect:
        await unregister_client(websocket)
