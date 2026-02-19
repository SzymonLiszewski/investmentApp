"""
Abstract base class for asset lookup and basic info resolution.
"""
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional


class AbstractAssetRepository(ABC):
    """Abstract base class for asset persistence and basic info retrieval."""

    @abstractmethod
    def get_asset_by_symbol(self, symbol: str) -> Optional[Any]:
        """Return Asset for symbol or None if not found."""
        pass

    @abstractmethod
    def get_basic_info(self, symbol: str, fetcher: Any) -> Dict[str, Any]:
        """
        Return basic info dict: Company Name (from Asset if present),
        Current Price, Price Change, Percent Change (from cache/fetcher).
        """
        pass
