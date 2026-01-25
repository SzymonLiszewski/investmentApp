"""
Unit tests for CurrencyConverter.
"""
from django.test import TestCase
from unittest.mock import Mock, patch
from decimal import Decimal
from forex_python.converter import RatesNotAvailableError
from analytics.services.currency_converter import CurrencyConverter


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

    @patch('analytics.services.currency_converter.CurrencyRates')
    def test_convert_different_currencies(self, mock_rates_class):
        """Test converting between different currencies."""
        # Mock the CurrencyRates instance
        mock_rates = Mock()
        mock_rates.get_rate.return_value = 4.0  # 1 USD = 4 PLN
        mock_rates_class.return_value = mock_rates

        # Create new converter with mocked rates
        converter = CurrencyConverter()
        
        # Test conversion
        amount = Decimal('100.00')
        result = converter.convert(amount, 'USD', 'PLN')
        
        self.assertIsNotNone(result)
        self.assertEqual(result, Decimal('400.00'))

    @patch('analytics.services.currency_converter.CurrencyRates')
    def test_convert_caches_exchange_rate(self, mock_rates_class):
        """Test that exchange rates are cached."""
        # Mock the CurrencyRates instance
        mock_rates = Mock()
        mock_rates.get_rate.return_value = 4.0
        mock_rates_class.return_value = mock_rates

        # Create new converter with mocked rates
        converter = CurrencyConverter()
        
        # Convert twice
        converter.convert(Decimal('100.00'), 'USD', 'PLN')
        converter.convert(Decimal('50.00'), 'USD', 'PLN')
        
        # get_rate should be called only once due to caching
        mock_rates.get_rate.assert_called_once()

    @patch('analytics.services.currency_converter.CurrencyRates')
    def test_convert_returns_none_on_error(self, mock_rates_class):
        """Test that convert returns None when rate is not available."""
        # Mock the CurrencyRates instance to raise exception
        mock_rates = Mock()
        mock_rates.get_rate.side_effect = RatesNotAvailableError('Rate not available')
        mock_rates_class.return_value = mock_rates

        # Create new converter with mocked rates
        converter = CurrencyConverter()
        
        # Test conversion
        result = converter.convert(Decimal('100.00'), 'USD', 'INVALID')
        
        self.assertIsNone(result)

    @patch('analytics.services.currency_converter.CurrencyRates')
    def test_get_exchange_rate_different_currencies(self, mock_rates_class):
        """Test getting exchange rate for different currencies."""
        mock_rates = Mock()
        mock_rates.get_rate.return_value = 0.85
        mock_rates_class.return_value = mock_rates

        converter = CurrencyConverter()
        rate = converter.get_exchange_rate('USD', 'EUR')
        
        self.assertIsNotNone(rate)
        self.assertEqual(rate, Decimal('0.85'))
