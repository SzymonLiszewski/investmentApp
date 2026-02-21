"""
Abstract base classes for fetching market data.
"""
import logging
from abc import ABC, abstractmethod
from datetime import date
from typing import Dict, List, Optional, Any, NamedTuple
from decimal import Decimal

import pandas as pd

logger = logging.getLogger(__name__)


class CurrentPriceResult(NamedTuple):
    """Result of fetching current price: price and its currency in one API response."""

    price: Decimal
    currency: Optional[str]


class StockDataFetcher(ABC):
    """Abstract base class for fetching stock market data."""

    @abstractmethod
    def get_current_price(self, symbol: str) -> Optional[CurrentPriceResult]:
        """Get the current price and currency of a stock (single API call)."""
        pass

    @abstractmethod
    def get_stock_info(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Get detailed information about a stock."""
        pass

    def get_currency(self, symbol: str) -> Optional[str]:
        """Get the currency of a stock. Default: from get_current_price result."""
        result = self.get_current_price(symbol)
        return result.currency if result else None

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
    def get_current_price(self, symbol: str) -> Optional[CurrentPriceResult]:
        """Get the current price and quote currency of a cryptocurrency pair (single API call)."""
        pass

    def get_currency(self, symbol: str) -> Optional[str]:
        """Get the quote currency of the pair. Default: from get_current_price result."""
        result = self.get_current_price(symbol)
        return result.currency if result else None

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
        result = self.get_current_price(symbol)
        if result is None:
            return None
        return {
            'symbol': symbol,
            'current_price': result.price,
            'currency': result.currency or 'USD',
        }


class FXDataFetcher(ABC):
    """Abstract base class for fetching FX (exchange rate) data."""

    @abstractmethod
    def get_historical_fx_series(
        self,
        from_currency: str,
        to_currency: str,
        start_date: date,
        end_date: date,
    ) -> Optional[pd.Series]:
        """
        Return a Series of exchange rates so that amount_in_from * rate = amount_in_to.
        Index: DatetimeIndex (dates). Used for converting time series to another currency.
        """
        pass

    @abstractmethod
    def get_current_rate(self, from_currency: str, to_currency: str) -> Optional[Decimal]:
        """
        Return current exchange rate so that amount_in_from * rate = amount_in_to.
        Used for converting a single value (e.g. benchmark profit) to user currency.
        """
        pass
