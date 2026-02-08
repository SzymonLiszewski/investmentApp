"""
Abstract base classes for fetching market data.
"""
import logging
from abc import ABC, abstractmethod
from datetime import date
from typing import Dict, List, Optional, Any
from decimal import Decimal

import pandas as pd

logger = logging.getLogger(__name__)


class StockDataFetcher(ABC):
    """Abstract base class for fetching stock market data."""

    @abstractmethod
    def get_current_price(self, symbol: str) -> Optional[Decimal]:
        """Get the current price of a stock."""
        pass

    @abstractmethod
    def get_stock_info(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Get detailed information about a stock."""
        pass

    @abstractmethod
    def get_currency(self, symbol: str) -> Optional[str]:
        """Get the currency of a stock."""
        pass

    @abstractmethod
    def get_historical_prices(
        self,
        symbols: List[str],
        start_date: date,
        end_date: date,
    ) -> Dict[str, pd.Series]:
        """Batch-download historical Close prices for multiple stock symbols."""
        pass


class CryptoDataFetcher(ABC):
    """Abstract base class for fetching cryptocurrency market data."""

    @abstractmethod
    def get_current_price(self, symbol: str) -> Optional[Decimal]:
        """Get the current price of a cryptocurrency pair."""
        pass

    @abstractmethod
    def get_currency(self, symbol: str) -> Optional[str]:
        """Get the quote currency of the pair."""
        pass

    @abstractmethod
    def get_historical_prices(
        self,
        symbols: List[str],
        start_date: date,
        end_date: date,
    ) -> Dict[str, pd.Series]:
        """Batch-download historical Close prices for crypto symbols."""
        pass

    def get_crypto_info(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Get detailed information about a cryptocurrency (optional)."""
        price = self.get_current_price(symbol)
        currency = self.get_currency(symbol)
        if price is None or currency is None:
            return None
        return {
            'symbol': symbol,
            'current_price': price,
            'currency': currency,
        }
