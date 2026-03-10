import yfinance as yf
from typing import List, Dict, Any
import logging

class NewsClient:
    """News client fetching real news via yfinance for the MVP."""
    
    def fetch_news(self, topics: List[str], max_articles: int = 5) -> List[Dict[str, Any]]:
        articles = []
        for topic in topics:
            try:
                # If topic is a recognized ticker or short string, try yfinance news
                if len(topic) <= 6 and topic.isalnum():
                    t = yf.Ticker(topic)
                    news_items = t.news
                    # Just grab top 2 per topic
                    for item in news_items[:2]:
                        articles.append({
                            "title": item.get("title", ""),
                            "summary": "Click the link to read the full article context.",
                            "url": item.get("link", ""),
                            "topic": topic
                        })
            except Exception as e:
                logging.error(f"Error fetching news for {topic}: {e}")
                
        # If no articles were fetched, fallback to a generic SPY news for overall market context
        if not articles:
            try:
                t = yf.Ticker("SPY")
                for item in t.news[:max_articles]:
                    articles.append({
                        "title": item.get("title", ""),
                        "summary": "General market news.",
                        "url": item.get("link", ""),
                        "topic": "General Market"
                    })
            except Exception as e:
                logging.error(f"Error fetching generic market news: {e}")
                
        # Fill in generic mock if we have absolutely nothing
        if not articles:
            articles.append({
                "title": f"Market Overview",
                "summary": "General market news could not be loaded via real APIs.",
                "url": "https://finance.yahoo.com/",
                "topic": "General"
            })
            
        return articles[:max_articles]
