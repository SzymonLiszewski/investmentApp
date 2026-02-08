"""
Abstract base class for fetching news.
"""
from abc import ABC, abstractmethod
from typing import Dict, List


class NewsFetcher(ABC):
    """
    Abstract base class for fetching news from external services.
    Each implementation represents one news source.
    """

    @abstractmethod
    def get_news(self, query: str, count: int = 5) -> List[Dict]:
        """
        Fetch news articles for the given query.

        Args:
            query: Search query (e.g. ticker symbol).
            count: Maximum number of articles to return.

        Returns:
            List of dicts, each containing at least: title, link, summary.
        """
        pass
