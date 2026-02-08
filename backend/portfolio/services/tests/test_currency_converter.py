"""
Unit tests for CurrencyConverter.
"""
from django.test import TestCase
from unittest.mock import Mock, patch
from decimal import Decimal

import pandas as pd

from portfolio.services.currency_converter import CurrencyConverter


class TestCurrencyConverter(TestCase):
    """Test the CurrencyConverter class."""

    def setUp(self):
        """Set up test fixtures."""
        self.converter = CurrencyConverter()

    def test_convert_same_currency(self):
        """Test converting between same currencies returns original amount."""
        amount = Decimal('100.00')
        result = self.converter.convert(amount, 'USD', 'USD')

        self.assertEqual(result, amount)

    @patch('portfolio.services.currency_converter.yf.Ticker')
    def test_convert_different_currencies(self, mock_ticker_cls):
        """Test converting between different currencies."""
        mock_ticker = Mock()
        mock_ticker.history.return_value = pd.DataFrame(
            {'Close': [4.0]},
            index=pd.to_datetime(['2026-01-01']),
        )
        mock_ticker_cls.return_value = mock_ticker

        converter = CurrencyConverter()

        amount = Decimal('100.00')
        result = converter.convert(amount, 'USD', 'PLN')

        self.assertIsNotNone(result)
        self.assertEqual(result, Decimal('400.00'))
        mock_ticker_cls.assert_called_with('USDPLN=X')

    @patch('portfolio.services.currency_converter.yf.Ticker')
    def test_convert_caches_exchange_rate(self, mock_ticker_cls):
        """Test that exchange rates are cached."""
        mock_ticker = Mock()
        mock_ticker.history.return_value = pd.DataFrame(
            {'Close': [4.0]},
            index=pd.to_datetime(['2026-01-01']),
        )
        mock_ticker_cls.return_value = mock_ticker

        converter = CurrencyConverter()

        converter.convert(Decimal('100.00'), 'USD', 'PLN')
        converter.convert(Decimal('50.00'), 'USD', 'PLN')

        # yf.Ticker should be called only once due to caching
        mock_ticker_cls.assert_called_once()

    @patch('portfolio.services.currency_converter.yf.Ticker')
    def test_convert_returns_none_on_error(self, mock_ticker_cls):
        """Test that convert returns None when rate is not available."""
        mock_ticker = Mock()
        mock_ticker.history.return_value = pd.DataFrame()
        mock_ticker_cls.return_value = mock_ticker

        converter = CurrencyConverter()

        result = converter.convert(Decimal('100.00'), 'USD', 'INVALID')

        self.assertIsNone(result)

    @patch('portfolio.services.currency_converter.yf.Ticker')
    def test_get_exchange_rate_same_currency(self, mock_ticker_cls):
        """Test getting exchange rate for same currency returns 1."""
        rate = self.converter.get_exchange_rate('USD', 'USD')

        self.assertEqual(rate, Decimal('1.0'))
        mock_ticker_cls.assert_not_called()

    @patch('portfolio.services.currency_converter.yf.Ticker')
    def test_get_exchange_rate_different_currencies(self, mock_ticker_cls):
        """Test getting exchange rate for different currencies."""
        mock_ticker = Mock()
        mock_ticker.history.return_value = pd.DataFrame(
            {'Close': [0.85]},
            index=pd.to_datetime(['2026-01-01']),
        )
        mock_ticker_cls.return_value = mock_ticker

        converter = CurrencyConverter()
        rate = converter.get_exchange_rate('USD', 'EUR')

        self.assertIsNotNone(rate)
        self.assertEqual(rate, Decimal('0.85'))

    @patch('portfolio.services.currency_converter.yf.Ticker')
    def test_clear_cache(self, mock_ticker_cls):
        """Test that clear_cache empties the cache."""
        mock_ticker = Mock()
        mock_ticker.history.return_value = pd.DataFrame(
            {'Close': [4.0]},
            index=pd.to_datetime(['2026-01-01']),
        )
        mock_ticker_cls.return_value = mock_ticker

        converter = CurrencyConverter()
        converter.convert(Decimal('100.00'), 'USD', 'PLN')

        self.assertEqual(mock_ticker_cls.call_count, 1)

        converter.clear_cache()
        converter.convert(Decimal('100.00'), 'USD', 'PLN')

        # After clearing cache, yf.Ticker is called again
        self.assertEqual(mock_ticker_cls.call_count, 2)

    @patch('portfolio.services.currency_converter.yf.Ticker')
    def test_convert_returns_none_on_exception(self, mock_ticker_cls):
        """Test that convert returns None when yfinance raises an exception."""
        mock_ticker_cls.side_effect = Exception('Network error')

        converter = CurrencyConverter()
        result = converter.convert(Decimal('100.00'), 'USD', 'PLN')

        self.assertIsNone(result)
