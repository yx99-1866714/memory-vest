from typing import Dict, Any, List
from datetime import datetime
import random

class MarketClient:
    """Mock market client for the MVP."""
    
    def fetch_end_of_day_prices(self, tickers: List[str]) -> Dict[str, Any]:
        results = {}
        for ticker in tickers:
            # Mock some reasonable price and change
            base_price = sum([ord(c) for c in ticker])
            change_percent = random.uniform(-3.0, 3.0)
            
            # Simple heuristic for mock support/resistance
            support = base_price * 0.95
            resistance = base_price * 1.05
            
            results[ticker] = {
                "price": base_price,
                "change_percent": round(change_percent, 2),
                "support_zone": round(support, 2),
                "resistance_zone": round(resistance, 2),
                "trend": "up" if change_percent > 0 else "down"
            }
        return results

    def fetch_sector_performance(self, sectors: List[str]) -> Dict[str, Any]:
        results = {}
        for sector in sectors:
            change_percent = random.uniform(-1.5, 1.5)
            results[sector] = {
                "change_percent": round(change_percent, 2)
            }
        return results
