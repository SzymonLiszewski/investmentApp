"""
Data fetchers for retrieving stock market data.
"""
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any
from decimal import Decimal
import yfinance as yf


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
