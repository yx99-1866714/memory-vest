from typing import List, Dict, Any

class NewsClient:
    """Mock news client for the MVP."""
    
    def fetch_news(self, topics: List[str], max_articles: int = 5) -> List[Dict[str, Any]]:
        articles = []
        for topic in topics:
            articles.append({
                "title": f"Major developments in {topic} impact markets",
                "summary": f"Recent announcements regarding {topic} have shown significant momentum. Analysts suggest this trend might continue in the near term.",
                "url": f"https://example.com/news/{topic}",
                "topic": topic
            })
            
        return articles[:max_articles]
