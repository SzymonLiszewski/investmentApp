"""
Data fetchers for retrieving stock market data.
"""
import logging
from abc import ABC, abstractmethod
from datetime import date, timedelta
from typing import Dict, List, Optional, Any
from decimal import Decimal

import pandas as pd
import yfinance as yf

logger = logging.getLogger(__name__)


class StockDataFetcher(ABC):
    """
    Abstract base class for fetching stock market data.
    """

    @abstractmethod
    def get_current_price(self, symbol: str) -> Optional[Decimal]:
        """
        Get the current price of a stock.

        Args:
            symbol: Stock symbol (ticker)

        Returns:
            Current price as Decimal or None if not available
        """
        pass

    @abstractmethod
    def get_stock_info(self, symbol: str) -> Optional[Dict[str, Any]]:
        """
        Get detailed information about a stock.

        Args:
            symbol: Stock symbol (ticker)

        Returns:
            Dictionary with stock information or None if not available
        """
        pass

    @abstractmethod
    def get_currency(self, symbol: str) -> Optional[str]:
        """
        Get the currency of a stock.

        Args:
            symbol: Stock symbol (ticker)

        Returns:
            Currency code (e.g., 'USD', 'PLN') or None if not available
        """
        pass

    @abstractmethod
    def get_historical_prices(
        self,
        symbols: List[str],
        start_date: date,
        end_date: date,
    ) -> Dict[str, pd.Series]:
        """
        Batch-download historical Close prices for multiple stock symbols.

        Args:
            symbols: List of stock ticker symbols (e.g. ``['AAPL', 'MSFT.WA']``).
            start_date: Start of date range (inclusive).
            end_date: End of date range (inclusive).

        Returns:
            Dict mapping each symbol to a ``pd.Series`` indexed by
            ``datetime.date`` with Close prices.  Missing trading days
            are forward-filled.
        """
        pass


class YfinanceStockDataFetcher(StockDataFetcher):
    """
    Implementation of StockDataFetcher using yfinance library.
    """

    def __init__(self):
        self._cache = {}

    def get_current_price(self, symbol: str) -> Optional[Decimal]:
        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info
            
            # Try to get the current price from various fields
            price = info.get('currentPrice') or info.get('regularMarketPrice')
            
            if price is None:
                # Fallback to historical data
                hist = ticker.history(period='1d')
                if not hist.empty:
                    price = hist['Close'].iloc[-1]
            
            if price is not None:
                return Decimal(str(price))
            
            return None
        except Exception as e:
            # Log error in production
            print(f"Error fetching price for {symbol}: {str(e)}")
            return None

    def get_stock_info(self, symbol: str) -> Optional[Dict[str, Any]]:
        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info
            
            return {
                'symbol': symbol,
                'name': info.get('longName', ''),
                'current_price': self.get_current_price(symbol),
                'currency': info.get('currency', 'USD'),
                'market_cap': info.get('marketCap'),
                'sector': info.get('sector', ''),
                'industry': info.get('industry', ''),
            }
        except Exception as e:
            # Log error in production
            print(f"Error fetching info for {symbol}: {str(e)}")
            return None

    def get_currency(self, symbol: str) -> Optional[str]:
        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info
            return info.get('currency', 'USD')
        except Exception as e:
            print(f"Error fetching currency for {symbol}: {str(e)}")
            return None

    def get_historical_prices(
        self,
        symbols: List[str],
        start_date: date,
        end_date: date,
    ) -> Dict[str, pd.Series]:
        if not symbols:
            return {}

        try:
            data = yf.download(
                symbols,
                start=start_date.isoformat(),
                end=(end_date + timedelta(days=1)).isoformat(),
                progress=False,
            )
        except Exception:
            logger.exception("yfinance download failed for %s", symbols)
            return {}

        if data is None or data.empty:
            return {}

        # Extract Close prices
        try:
            close = data["Close"]
        except KeyError:
            return {}

        # Single ticker → Series; convert to DataFrame
        if isinstance(close, pd.Series):
            close = close.to_frame(name=symbols[0])

        # Handle MultiIndex columns produced by newer yfinance
        if isinstance(close.columns, pd.MultiIndex):
            close.columns = close.columns.get_level_values(-1)

        # Normalise index to datetime.date and forward-fill gaps
        close.index = pd.to_datetime(close.index).date
        close = close.ffill()

        result: Dict[str, pd.Series] = {}
        for sym in symbols:
            if sym in close.columns:
                result[sym] = close[sym].dropna()

        return result


class CryptoDataFetcher(ABC):
    """
    Abstract base class for fetching cryptocurrency market data.
    """

    @abstractmethod
    def get_current_price(self, symbol: str) -> Optional[Decimal]:
        """
        Get the current price of a cryptocurrency pair.

        Args:
            symbol: Crypto pair symbol (e.g. 'BTC-USD', 'ETH-USD')

        Returns:
            Current price as Decimal or None if not available
        """
        pass

    @abstractmethod
    def get_currency(self, symbol: str) -> Optional[str]:
        """
        Get the quote currency of the pair (e.g. 'USD' for BTC-USD).

        Args:
            symbol: Crypto pair symbol

        Returns:
            Currency code (e.g. 'USD') or None if not available
        """
        pass

    @abstractmethod
    def get_historical_prices(
        self,
        symbols: List[str],
        start_date: date,
        end_date: date,
    ) -> Dict[str, pd.Series]:
        """
        Batch-download historical Close prices for crypto symbols.

        Args:
            symbols: List of crypto symbols in DB format
                     (e.g. ``['BTC', 'ETH']``).  The implementation is
                     responsible for mapping to the provider's format.
            start_date: Start of date range (inclusive).
            end_date: End of date range (inclusive).

        Returns:
            Dict mapping each **input** symbol to a ``pd.Series``
            indexed by ``datetime.date`` with Close prices.
        """
        pass

    def get_crypto_info(self, symbol: str) -> Optional[Dict[str, Any]]:
        """
        Get detailed information about a cryptocurrency (optional).

        Args:
            symbol: Crypto pair symbol

        Returns:
            Dictionary with crypto information or None if not available
        """
        price = self.get_current_price(symbol)
        currency = self.get_currency(symbol)
        if price is None or currency is None:
            return None
        return {
            'symbol': symbol,
            'current_price': price,
            'currency': currency,
        }


class YfinanceCryptoDataFetcher(CryptoDataFetcher):
    """
    Implementation of CryptoDataFetcher using yfinance library.
    DB stores only crypto symbol (e.g. BTC); pair with USD (e.g. BTC-USD) is built when fetching.
    """

    def __init__(self):
        self._cache = {}

    def _yfinance_symbol(self, symbol: str) -> str:
        """Return symbol in yfinance format (pair with USD if not already a pair)."""
        if '-' in symbol:
            return symbol
        return f"{symbol}-USD"

    def get_current_price(self, symbol: str) -> Optional[Decimal]:
        try:
            yf_symbol = self._yfinance_symbol(symbol)
            ticker = yf.Ticker(yf_symbol)
            info = ticker.info

            price = info.get('regularMarketPrice') or info.get('currentPrice')

            if price is None:
                hist = ticker.history(period='1d')
                if not hist.empty:
                    price = hist['Close'].iloc[-1]

            if price is not None:
                return Decimal(str(price))

            return None
        except Exception as e:
            print(f"Error fetching crypto price for {symbol}: {str(e)}")
            return None

    def get_currency(self, symbol: str) -> Optional[str]:
        try:
            # Symbol from DB is crypto only (e.g. BTC) -> we use USD pair
            if '-' in symbol:
                return symbol.split('-')[-1].upper()
            return 'USD'
        except Exception as e:
            print(f"Error fetching crypto currency for {symbol}: {str(e)}")
            return None

    def get_historical_prices(
        self,
        symbols: List[str],
        start_date: date,
        end_date: date,
    ) -> Dict[str, pd.Series]:
        if not symbols:
            return {}

        # Map DB symbols → yfinance symbols
        yf_to_orig: Dict[str, str] = {}
        for sym in symbols:
            yf_to_orig[self._yfinance_symbol(sym)] = sym

        yf_symbols = list(yf_to_orig.keys())

        try:
            data = yf.download(
                yf_symbols,
                start=start_date.isoformat(),
                end=(end_date + timedelta(days=1)).isoformat(),
                progress=False,
            )
        except Exception:
            logger.exception("yfinance crypto download failed for %s", yf_symbols)
            return {}

        if data is None or data.empty:
            return {}

        try:
            close = data["Close"]
        except KeyError:
            return {}

        if isinstance(close, pd.Series):
            close = close.to_frame(name=yf_symbols[0])

        if isinstance(close.columns, pd.MultiIndex):
            close.columns = close.columns.get_level_values(-1)

        close.index = pd.to_datetime(close.index).date
        close = close.ffill()

        # Map back to original DB symbols
        result: Dict[str, pd.Series] = {}
        for yf_sym, orig_sym in yf_to_orig.items():
            if yf_sym in close.columns:
                result[orig_sym] = close[yf_sym].dropna()

        return result
