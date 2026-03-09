from typing import List, Dict, Any
from app.infra.news_client import NewsClient

class NewsService:
    def __init__(self):
        self.client = NewsClient()

    def get_relevant_news(self, interests: List[str], tickers: List[str]) -> List[Dict[str, Any]]:
        """
        Fetches news relevant to the user's interests and holdings.
        """
        # Combine tickers and interests to fetch news
        topics = tickers + interests
        # deduplicate
        topics = list(set(topics))
        
        return self.client.fetch_news(topics, max_articles=5)
