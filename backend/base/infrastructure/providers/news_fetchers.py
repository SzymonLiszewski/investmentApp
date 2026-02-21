"""
News fetcher implementations using Yahoo RSS and NewsData API.
"""
import feedparser
from decouple import config
from newsdataapi import NewsDataApiClient
from typing import Dict, List

from base.infrastructure.interfaces.news_fetcher import NewsFetcher

_NEWSDATA_API_KEY = config('NEWSDATA_API_KEY', default="").strip()


class YahooNewsFetcher(NewsFetcher):
    """Fetch news from Yahoo Finance RSS feeds."""

    def get_news(self, query: str, count: int = 5) -> List[Dict]:
        rss_url = f"https://finance.yahoo.com/rss/headline?s={query}"
        feed = feedparser.parse(rss_url)
        news = []
        for entry in feed.entries[:count]:
            news.append({
                'title': entry.title,
                'link': entry.link,
                'summary': entry.summary if hasattr(entry, 'summary') else "No summary available.",
            })
        return news


class NewsDataNewsFetcher(NewsFetcher):
    """Fetch news from NewsData API. Requires api_key (e.g. from settings). No-op when key is empty."""

    def __init__(self, api_key: str = None):
        self._api_key = (api_key or _NEWSDATA_API_KEY or "").strip()

    def get_news(self, query: str, count: int = 5) -> List[Dict]:
        if not self._api_key:
            return []
        api = NewsDataApiClient(apikey=self._api_key)
        response = api.news_api(q=query, language="en")
        return response.get('results', [])[:count]
