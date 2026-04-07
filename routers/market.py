# routers/market.py
from fastapi import APIRouter, HTTPException, Query
import yfinance as yf

router = APIRouter(prefix="/market", tags=["Market Data"])


@router.get("/")
def get_market_data(
    symbol: str = Query(default="^NSEI", description="^NSEI for Nifty, ^BSESN for Sensex"),
    period: str = Query(default="3mo", description="1mo, 3mo, 6mo, 1y"),
    interval: str = Query(default="1d", description="1d, 1wk"),
):
    """
    Fetch OHLC market data for Nifty 50 or Sensex.
    """
    try:
        ticker = yf.Ticker(symbol)
        df = ticker.history(period=period, interval=interval)

        if df.empty:
            raise HTTPException(status_code=404, detail=f"No data found for symbol: {symbol}")

        df.dropna(inplace=True)

        data = []
        for date, row in df.iterrows():
            data.append({
                "date": str(date.date()),
                "open": round(row["Open"], 2),
                "high": round(row["High"], 2),
                "low": round(row["Low"], 2),
                "close": round(row["Close"], 2),
                "volume": int(row["Volume"]),
            })

        return {
            "symbol": symbol,
            "period": period,
            "interval": interval,
            "count": len(data),
            "data": data,
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch market data: {str(e)}")