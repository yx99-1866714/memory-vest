import requests
import yfinance as yf
from typing import List, Dict, Any
import logging
from app.config import settings

ALPHA_VANTAGE_NEWS_URL = "https://www.alphavantage.co/query"


class NewsClient:
    """News client using yfinance as primary source, Alpha Vantage as fallback.

    Fetches news per-ticker individually to avoid any AND-filter behavior,
    then deduplicates results by URL.
    """

    def fetch_news(self, tickers: List[str], max_articles: int = 5) -> List[Dict[str, Any]]:
        articles = self._yfinance_fetch(tickers, max_articles)
        if articles:
            return articles

        logging.warning("yfinance returned no articles. Trying Alpha Vantage fallback.")
        return self._alpha_vantage_fetch(tickers, max_articles)

    # ── Primary: yfinance ──────────────────────────────────────────────────────

    def _yfinance_fetch(self, tickers: List[str], max_articles: int) -> List[Dict[str, Any]]:
        articles = []
        seen_urls = set()

        for ticker in tickers:
            if not (len(ticker) <= 6 and ticker.isalnum()):
                continue
            if len(articles) >= max_articles:
                break
            try:
                t = yf.Ticker(ticker)
                # get_news() returns a list of dicts with 'title', 'link', etc.
                news_items = t.get_news() or []
                for item in news_items[:3]:
                    content = item.get("content", {})
                    title = content.get("title", item.get("title", "")).strip()
                    url = (
                        content.get("canonicalUrl", {}).get("url")
                        or item.get("link", "")
                    )
                    if not title or not url or url in seen_urls:
                        continue
                    seen_urls.add(url)
                    articles.append({
                        "title": title,
                        "summary": content.get("summary", title).strip() or title,
                        "url": url,
                        "source": content.get("provider", {}).get("displayName", ""),
                        "topic": ticker
                    })
                    if len(articles) >= max_articles:
                        break
            except Exception as e:
                logging.error(f"yfinance news error for {ticker}: {e}")

        return articles

    # ── Fallback: Alpha Vantage ────────────────────────────────────────────────

    def _alpha_vantage_fetch(self, tickers: List[str], max_articles: int) -> List[Dict[str, Any]]:
        api_key = settings.alpha_vantage_api_key
        if not api_key:
            logging.warning("ALPHA_VANTAGE_API_KEY not set; no fallback available.")
            return self._empty_fallback()

        valid_tickers = [t.upper() for t in tickers if len(t) <= 6 and t.isalnum()]
        articles = []
        seen_urls = set()

        for ticker in valid_tickers:
            if len(articles) >= max_articles:
                break
            try:
                params = {
                    "function": "NEWS_SENTIMENT",
                    "tickers": ticker,
                    "sort": "LATEST",
                    "limit": 3,
                    "apikey": api_key
                }
                resp = requests.get(ALPHA_VANTAGE_NEWS_URL, params=params, timeout=10)
                logging.debug(f"Alpha Vantage [{ticker}]: HTTP {resp.status_code}")
                if resp.status_code != 200:
                    continue
                for item in resp.json().get("feed", []):
                    url = item.get("url", "")
                    if url in seen_urls:
                        continue
                    seen_urls.add(url)
                    title = item.get("title", "").strip()
                    articles.append({
                        "title": title,
                        "summary": item.get("summary", title).strip() or title,
                        "url": url,
                        "source": item.get("source", ""),
                        "sentiment": item.get("overall_sentiment_label", ""),
                        "topic": ticker
                    })
                    if len(articles) >= max_articles:
                        break
            except Exception as e:
                logging.error(f"Alpha Vantage news error for {ticker}: {e}")

        return articles if articles else self._empty_fallback()

    def _empty_fallback(self) -> List[Dict[str, Any]]:
        return [{
            "title": "Market Overview",
            "summary": "General market news could not be loaded.",
            "url": "https://finance.yahoo.com/",
            "topic": "General"
        }]
