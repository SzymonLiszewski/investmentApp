"""
Abstract base class for fetching economic calendar data.
"""
from abc import ABC, abstractmethod
from typing import List


class EconomicCalendarFetcher(ABC):
    """Abstract base class for economic calendar data providers."""

    @abstractmethod
    def get_earnings(self) -> List:
        """Fetch upcoming earnings calendar data."""
        pass

    @abstractmethod
    def get_ipo(self) -> List:
        """Fetch upcoming IPO calendar data."""
        pass
