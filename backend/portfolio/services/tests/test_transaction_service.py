"""
Unit tests for transaction_service (get_or_create_asset, resolve_price_for_date, update_user_asset).
"""
from datetime import date, timedelta
from unittest.mock import Mock

import pandas as pd
from django.test import TestCase

from portfolio.services.transaction_service import (
    _PRICE_RESOLVE_DAYS_BACK,
    _PRICE_RESOLVE_DAYS_FORWARD,
    resolve_price_for_date,
)


def _make_price_series(dates, prices):
    return pd.Series(prices, index=pd.Index(dates))


class ResolvePriceForDateTests(TestCase):
    """Tests for resolving missing transaction price via data fetchers."""

    def test_returns_none_for_bonds(self):
        """Bonds are not priced by this resolver."""
        result = resolve_price_for_date(
            "PL123", "bonds", date(2026, 1, 15),
            stock_fetcher=Mock(), crypto_fetcher=Mock(),
        )
        self.assertIsNone(result)

    def test_returns_none_for_empty_symbol(self):
        """Empty symbol yields None."""
        mock_stock = Mock()
        mock_stock.get_historical_prices.return_value = {}
        result = resolve_price_for_date(
            "", "stocks", date(2026, 1, 15),
            stock_fetcher=mock_stock, crypto_fetcher=Mock(),
        )
        self.assertIsNone(result)
        mock_stock.get_historical_prices.assert_not_called()

    def test_stocks_fetches_range_and_returns_close_on_date(self):
        """Stocks: fetcher is called with date range and close on target date is returned."""
        target = date(2026, 1, 15)
        start = target - timedelta(days=_PRICE_RESOLVE_DAYS_BACK)
        end = target + timedelta(days=_PRICE_RESOLVE_DAYS_FORWARD)
        series = _make_price_series([target], [150.5])
        mock_stock = Mock()
        mock_stock.get_historical_prices.return_value = {"AAPL": series}

        result = resolve_price_for_date(
            "AAPL", "stocks", target,
            stock_fetcher=mock_stock, crypto_fetcher=Mock(),
        )

        self.assertEqual(result, 150.5)
        mock_stock.get_historical_prices.assert_called_once_with(["AAPL"], start, end)

    def test_stocks_uses_most_recent_earlier_price_if_no_data_on_date(self):
        """When there is no quote on the exact date, use latest earlier date."""
        target = date(2026, 1, 15)
        series = _make_price_series([date(2026, 1, 14)], [148.0])
        mock_stock = Mock()
        mock_stock.get_historical_prices.return_value = {"CDR.WA": series}

        result = resolve_price_for_date(
            "CDR.WA", "stocks", target,
            stock_fetcher=mock_stock, crypto_fetcher=Mock(),
        )

        self.assertEqual(result, 148.0)

    def test_stocks_returns_none_when_fetcher_returns_empty(self):
        """When fetcher returns no data, result is None."""
        mock_stock = Mock()
        mock_stock.get_historical_prices.return_value = {}

        result = resolve_price_for_date(
            "UNKNOWN", "stocks", date(2026, 1, 15),
            stock_fetcher=mock_stock, crypto_fetcher=Mock(),
        )

        self.assertIsNone(result)

    def test_crypto_fetches_range_and_returns_close_on_date(self):
        """Crypto: fetcher is called with date range and close on target date is returned."""
        target = date(2026, 1, 15)
        start = target - timedelta(days=_PRICE_RESOLVE_DAYS_BACK)
        end = target + timedelta(days=_PRICE_RESOLVE_DAYS_FORWARD)
        series = _make_price_series([target], [50000.0])
        mock_crypto = Mock()
        mock_crypto.get_historical_prices.return_value = {"BTC-USD": series}

        result = resolve_price_for_date(
            "BTC-USD", "cryptocurrencies", target,
            stock_fetcher=Mock(), crypto_fetcher=mock_crypto,
        )

        self.assertEqual(result, 50000.0)
        mock_crypto.get_historical_prices.assert_called_once_with(["BTC-USD"], start, end)

    def test_crypto_returns_none_when_fetcher_returns_empty(self):
        """When crypto fetcher returns no data, result is None."""
        mock_crypto = Mock()
        mock_crypto.get_historical_prices.return_value = {}

        result = resolve_price_for_date(
            "ETH-USD", "cryptocurrencies", date(2026, 1, 15),
            stock_fetcher=Mock(), crypto_fetcher=mock_crypto,
        )

        self.assertIsNone(result)

    def test_uses_next_day_when_no_earlier_data(self):
        """When target date is before first available quote (e.g. weekend), use next trading day."""
        target = date(2026, 1, 17)  # Saturday
        next_trading = date(2026, 1, 19)  # Monday
        series = _make_price_series([next_trading], [152.0])
        mock_stock = Mock()
        mock_stock.get_historical_prices.return_value = {"AAPL": series}

        result = resolve_price_for_date(
            "AAPL", "stocks", target,
            stock_fetcher=mock_stock, crypto_fetcher=Mock(),
        )

        self.assertEqual(result, 152.0)
