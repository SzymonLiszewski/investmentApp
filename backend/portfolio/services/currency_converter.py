"""
Currency converter for converting asset values between currencies.

Uses yfinance exchange-rate tickers (e.g. ``USDPLN=X``) so that no
additional API keys or third-party services are required.
"""
import logging
from typing import Optional
from decimal import Decimal

import yfinance as yf

logger = logging.getLogger(__name__)


class CurrencyConverter:
    """
    Handles currency conversion using yfinance FX data.
    """

    def __init__(self):
        """Initialize the currency converter."""
        self._cache: dict[str, Decimal] = {}

    def convert(
        self,
        amount: Decimal,
        from_currency: str,
        to_currency: str,
    ) -> Optional[Decimal]:
        """
        Convert *amount* from one currency to another.

        Args:
            amount: Amount to convert.
            from_currency: Source currency code (e.g. ``'USD'``).
            to_currency: Target currency code (e.g. ``'PLN'``).

        Returns:
            Converted amount or ``None`` if conversion fails.
        """
        if from_currency == to_currency:
            return amount

        rate = self._get_cached_rate(from_currency, to_currency)
        if rate is None:
            return None

        return amount * rate

    def get_exchange_rate(
        self,
        from_currency: str,
        to_currency: str,
    ) -> Optional[Decimal]:
        """
        Get the exchange rate between two currencies.

        Returns:
            Exchange rate as ``Decimal`` or ``None`` if not available.
        """
        if from_currency == to_currency:
            return Decimal('1.0')

        return self._get_cached_rate(from_currency, to_currency)

    def clear_cache(self):
        """Clear the exchange rate cache."""
        self._cache.clear()

    def _get_cached_rate(
        self, from_currency: str, to_currency: str,
    ) -> Optional[Decimal]:
        """Return cached rate or fetch and cache it."""
        cache_key = f"{from_currency}_{to_currency}"
        if cache_key in self._cache:
            return self._cache[cache_key]

        rate = self._fetch_rate(from_currency, to_currency)
        if rate is not None:
            self._cache[cache_key] = rate
        return rate

    def _fetch_rate(
        self, from_currency: str, to_currency: str,
    ) -> Optional[Decimal]:
        """Fetch the current exchange rate from yfinance."""
        ticker_symbol = f"{from_currency}{to_currency}=X"
        try:
            ticker = yf.Ticker(ticker_symbol)
            hist = ticker.history(period='2d')
            if hist is not None and not hist.empty:
                price = float(hist['Close'].iloc[-1])
                return Decimal(str(price))
        except Exception as e:
            logger.warning(
                "Failed to fetch FX rate %s→%s: %s", from_currency, to_currency, e,
            )
        return None
