import yfinance as yf
from typing import Dict, Any, List
from datetime import datetime
import logging

class MarketClient:
    """Market client fetching live data via yfinance for the MVP."""
    
    def fetch_end_of_day_prices(self, tickers: List[str]) -> Dict[str, Any]:
        results = {}
        for ticker in tickers:
            try:
                t = yf.Ticker(ticker)
                price = t.info.get('currentPrice')
                if price is None:
                    hist_1d = t.history(period="1d")
                    if not hist_1d.empty:
                        price = float(hist_1d['Close'].iloc[-1])
                        
                prev_close = t.info.get('previousClose')
                if not prev_close and price:
                    hist_5d = t.history(period="5d")
                    if len(hist_5d) > 1:
                        prev_close = float(hist_5d['Close'].iloc[-2])
                        
                if price and prev_close:
                    change_percent = ((price - prev_close) / prev_close) * 100
                else:
                    change_percent = 0.0
                    
                hist = t.history(period="1mo")
                if not hist.empty:
                    support = float(hist['Low'].min())
                    resistance = float(hist['High'].max())
                else:
                    support = price * 0.95 if price else 0.0
                    resistance = price * 1.05 if price else 0.0
                    
                results[ticker] = {
                    "price": round(price, 2) if price else 0.0,
                    "change_percent": round(change_percent, 2),
                    "support_zone": round(support, 2),
                    "resistance_zone": round(resistance, 2),
                    "trend": "up" if change_percent > 0 else "down"
                }
            except Exception as e:
                logging.error(f"Error fetching MarketClient data for {ticker}: {e}")
                results[ticker] = {
                    "price": 0.0,
                    "change_percent": 0.0,
                    "support_zone": 0.0,
                    "resistance_zone": 0.0,
                    "trend": "flat"
                }
        return results

    def fetch_sector_performance(self, sectors: List[str]) -> Dict[str, Any]:
        SECTOR_ETF_MAP = {
            "technology": "XLK",
            "ai": "BOTZ",
            "healthcare": "XLV",
            "financials": "XLF",
            "energy": "XLE",
            "consumer": "XLY",
            "gaming": "GAMR",
            "real estate": "XLRE",
            "utilities": "XLU",
            "materials": "XLB",
            "industrials": "XLI",
            "communication": "XLC"
        }
        
        results = {}
        for sector in sectors:
            # Map sector to ETF or default to SPY (overall market)
            etf_ticker = None
            for key, val in SECTOR_ETF_MAP.items():
                if key in sector.lower():
                    etf_ticker = val
                    break
            
            if not etf_ticker:
                etf_ticker = "SPY"
                
            try:
                t = yf.Ticker(etf_ticker)
                price = t.info.get('currentPrice')
                prev_close = t.info.get('previousClose')
                if not price or not prev_close:
                    hist_5d = t.history(period="5d")
                    if len(hist_5d) > 1:
                        price = float(hist_5d['Close'].iloc[-1])
                        prev_close = float(hist_5d['Close'].iloc[-2])
                
                if price and prev_close:
                    change_percent = ((price - prev_close) / prev_close) * 100
                else:
                    change_percent = 0.0
                    
                results[sector] = {
                    "change_percent": round(change_percent, 2),
                    "proxy_etf": etf_ticker
                }
            except Exception as e:
                logging.error(f"Error fetching MarketClient sector data for {sector}: {e}")
                results[sector] = {
                    "change_percent": 0.0,
                    "proxy_etf": etf_ticker
                }
        return results
