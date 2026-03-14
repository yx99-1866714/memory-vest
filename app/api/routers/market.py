from fastapi import APIRouter, HTTPException
import yfinance as yf
import logging

router = APIRouter(
    prefix="/api/market",
    tags=["market"]
)

@router.get("/price/{ticker}")
def get_price(ticker: str):
    try:
        logging.info(f"Fetching current price for {ticker}")
        stock = yf.Ticker(ticker)
        # Fast extraction of current price from info object or fast history
        hist = stock.history(period="1d", timeout=5)
        
        if hist.empty:
             raise HTTPException(status_code=404, detail="No price data found for ticker.")
             
        current_price = float(hist['Close'].iloc[-1])
        return {"ticker": ticker.upper(), "currentPrice": current_price}
        
    except Exception as e:
        logging.error(f"Error fetching price for {ticker}: {e}")
        raise HTTPException(status_code=500, detail=str(e))
