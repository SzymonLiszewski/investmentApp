"""
Abstract base class for persisting and querying price history.
"""
from abc import ABC, abstractmethod
from datetime import date
from decimal import Decimal
from typing import Any, Dict, List, Optional


class AbstractPriceRepository(ABC):
    """Abstract base class for price history persistence and retrieval."""

    @abstractmethod
    def save_prices(
        self,
        symbol: str,
        prices: List[Dict[str, Optional[Decimal]]],
        asset: Optional[Any] = None,
    ) -> int:
        """
        Save or update price history for a symbol.
        Each dict in prices should have 'date' and 'close'; may include 'open', 'high', 'low', 'volume'.
        Returns the number of records created or updated.
        """
        pass

    @abstractmethod
    def get_by_symbol_and_date_range(
        self,
        symbol: str,
        start_date: date,
        end_date: date,
    ):
        """Return price history for symbol within [start_date, end_date], ordered by date."""
        pass

    @abstractmethod
    def get_latest_date(self, symbol: str) -> Optional[date]:
        """Return the most recent date we have data for this symbol, or None."""
        pass

    @abstractmethod
    def get_close_prices(
        self,
        symbol: str,
        start_date: date,
        end_date: date,
    ) -> Dict[date, Decimal]:
        """Return mapping of date -> close price for the given symbol and range."""
        pass
