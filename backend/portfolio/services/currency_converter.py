"""
Currency converter for converting asset values between currencies.

Uses an FXDataFetcher (default from base.services) for rates; falls back to
yfinance when no fetcher is provided (backward compatibility).
"""
import logging
from datetime import date
from typing import Optional, TYPE_CHECKING

import pandas as pd
import yfinance as yf
from decimal import Decimal

if TYPE_CHECKING:
    from base.infrastructure.interfaces.market_data_fetcher import FXDataFetcher

logger = logging.getLogger(__name__)


def _get_default_fx_fetcher():
    """Lazy import to avoid circular imports."""
    from base.services import get_default_fx_fetcher
    return get_default_fx_fetcher()


class CurrencyConverter:
    """
    Single entry point for FX: spot conversion, exchange rate, and time-series
    conversion. Uses FXDataFetcher when provided (or default); otherwise
    fetches current rate via yfinance.
    """

    def __init__(self, fx_fetcher: Optional['FXDataFetcher'] = None):
        """
        Args:
            fx_fetcher: Optional. When set, used for current rate and historical
                FX series. When None, uses default from base.services for
                get_historical_fx_series/convert_series, and yfinance for
                _fetch_rate (current rate).
        """
        self._cache: dict[str, Decimal] = {}
        self._fx_fetcher = fx_fetcher

    def _get_fx_fetcher(self) -> Optional['FXDataFetcher']:
        if self._fx_fetcher is not None:
            return self._fx_fetcher
        return _get_default_fx_fetcher()

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
        """Fetch the current exchange rate (via fetcher when set, else yfinance)."""
        fetcher = self._get_fx_fetcher()
        if fetcher is not None:
            rate = fetcher.get_current_rate(from_currency, to_currency)
            if rate is not None:
                return rate
        ticker_symbol = f"{from_currency}{to_currency}=X"
        try:
            ticker = yf.Ticker(ticker_symbol)
            hist = ticker.history(period='2d')
            if hist is not None and not hist.empty and 'Close' in hist.columns:
                price = float(hist['Close'].iloc[-1])
                return Decimal(str(price))
        except Exception as e:
            logger.warning(
                "Failed to fetch FX rate %s→%s: %s", from_currency, to_currency, e,
            )
        return None

    def get_historical_fx_series(
        self,
        from_currency: str,
        to_currency: str,
        start_date: date,
        end_date: date,
    ) -> Optional[pd.Series]:
        """
        Return a Series of exchange rates so that amount_from * rate = amount_to.
        Index: DatetimeIndex (dates). Returns None if fetcher is unavailable or fails.
        """
        if from_currency == to_currency:
            idx = pd.date_range(start=start_date, end=end_date, freq='D')
            return pd.Series(1.0, index=pd.DatetimeIndex(idx))
        fetcher = self._get_fx_fetcher()
        if fetcher is None:
            return None
        return fetcher.get_historical_fx_series(
            from_currency, to_currency, start_date, end_date
        )

    def convert_series(
        self,
        series: pd.Series,
        from_currency: str,
        to_currency: str,
        start_date: date,
        end_date: date,
    ) -> pd.Series:
        """
        Convert a time series of amounts from one currency to another using
        historical FX rates (one rate per date). amount_from * rate = amount_to.

        If conversion fails or same currency, returns the original series unchanged.
        """
        if from_currency == to_currency:
            return series
        fx_series = self.get_historical_fx_series(from_currency, to_currency, start_date, end_date)
        if fx_series is None or fx_series.empty:
            return series
        fx_aligned = fx_series.reindex(series.index).ffill().bfill()
        fx_aligned = fx_aligned.replace(0, float('nan')).fillna(1.0)
        converted = series * fx_aligned
        return converted.fillna(series)
