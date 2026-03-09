from typing import List, Dict, Any
from app.infra.market_client import MarketClient

class MarketDataService:
    def __init__(self):
        self.client = MarketClient()

    def get_portfolio_market_context(self, tickers: List[str], sectors: List[str]) -> Dict[str, Any]:
        """
        Gathers daily performance and basic support/resistance data for tickers and sectors.
        """
        ticker_data = self.client.fetch_end_of_day_prices(tickers)
        sector_data = self.client.fetch_sector_performance(sectors)
        
        return {
            "tickers": ticker_data,
            "sectors": sector_data
        }
