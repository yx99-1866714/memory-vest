from typing import List, Dict, Any
from app.infra.news_client import NewsClient
import logging


class NewsService:
    def __init__(self):
        self.client = NewsClient()

    def get_relevant_news(
        self,
        tickers: List[str],
        memory_context: str = "",
        market_data: Dict[str, Any] = None,
        max_articles: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Fetches news for the top 5 most relevant tickers.

        Prioritization strategy:
        1. Score each ticker by how often it appears in EverMemOS memory context
           (conversation history / episodic memories). Higher = user cares more.
        2. If a ticker has zero memory mentions, use its absolute price change %
           as a secondary score so the most volatile holdings get coverage.
        3. Select top 5 and fetch news per-ticker individually.
        """
        market_data = market_data or {}
        memory_upper = memory_context.upper()

        def ticker_score(ticker: str) -> tuple:
            t = ticker.upper()
            # Primary: count occurrences in EverMemOS context
            memory_mentions = memory_upper.count(t)
            # Secondary: absolute day change % from market data
            ticker_market = market_data.get(ticker, {})
            change_pct = ticker_market.get("change_percent", 0.0) or 0.0
            abs_change = abs(change_pct)
            return (memory_mentions, abs_change)

        scored = sorted(tickers, key=ticker_score, reverse=True)
        top_tickers = scored[:5]

        logging.info(
            f"NewsService ranked tickers: "
            + ", ".join(f"{t}(mem={memory_upper.count(t.upper())}, Δ={abs(market_data.get(t,{}).get('change_percent',0) or 0):.2f}%)" for t in top_tickers)
        )

        return self.client.fetch_news(top_tickers, max_articles=max_articles)
