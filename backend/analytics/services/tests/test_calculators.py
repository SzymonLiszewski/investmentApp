"""
Unit tests for asset calculators.
"""
from django.test import TestCase
from unittest.mock import Mock, patch
from decimal import Decimal
from analytics.services.calculators import AssetCalculator, StockCalculator
from analytics.services.data_fetchers import StockDataFetcher
from analytics.services.currency_converter import CurrencyConverter


class TestAssetCalculator(TestCase):
    """Test the abstract AssetCalculator class."""

    def test_is_abstract(self):
        """Test that AssetCalculator cannot be instantiated."""
        with self.assertRaises(TypeError):
            AssetCalculator()


class TestStockCalculator(TestCase):
    """Test the StockCalculator implementation."""

    def setUp(self):
        """Set up test fixtures."""
        # Create a mock data fetcher
        self.mock_fetcher = Mock(spec=StockDataFetcher)
        # Create a mock currency converter
        self.mock_converter = Mock(spec=CurrencyConverter)
        self.calculator = StockCalculator(self.mock_fetcher, self.mock_converter)

    def test_get_asset_type(self):
        """Test that get_asset_type returns 'stock'."""
        self.assertEqual(self.calculator.get_asset_type(), 'stock')

    def test_get_current_value_success(self):
        """Test calculating current value successfully."""
        # Mock the data fetcher to return a price
        self.mock_fetcher.get_current_price.return_value = Decimal('150.50')

        # Test data
        asset_data = {
            'symbol': 'AAPL',
            'quantity': 10,
        }

        # Test
        value = self.calculator.get_current_value(asset_data)

        # Assert
        self.assertIsNotNone(value)
        self.assertEqual(value, Decimal('1505.00'))
        self.mock_fetcher.get_current_price.assert_called_once_with('AAPL')

    def test_get_current_value_with_decimal_quantity(self):
        """Test calculating current value with Decimal quantity."""
        # Mock the data fetcher to return a price
        self.mock_fetcher.get_current_price.return_value = Decimal('100.00')

        # Test data with Decimal quantity
        asset_data = {
            'symbol': 'GOOGL',
            'quantity': Decimal('5.5'),
        }

        # Test
        value = self.calculator.get_current_value(asset_data)

        # Assert
        self.assertIsNotNone(value)
        self.assertEqual(value, Decimal('550.00'))

    def test_get_current_value_with_currency_conversion(self):
        """Test calculating current value with currency conversion."""
        # Mock the data fetcher
        self.mock_fetcher.get_current_price.return_value = Decimal('100.00')
        self.mock_fetcher.get_currency.return_value = 'USD'
        
        # Mock currency converter
        self.mock_converter.convert.return_value = Decimal('400.00')

        # Test data
        asset_data = {
            'symbol': 'AAPL',
            'quantity': 10,
        }

        # Test with target currency
        value = self.calculator.get_current_value(asset_data, target_currency='PLN')

        # Assert
        self.assertIsNotNone(value)
        self.assertEqual(value, Decimal('400.00'))
        self.mock_converter.convert.assert_called_once_with(
            Decimal('1000.00'),  # 10 * 100
            'USD',
            'PLN'
        )

    def test_get_current_value_without_currency_conversion(self):
        """Test calculating current value without currency conversion."""
        # Mock the data fetcher
        self.mock_fetcher.get_current_price.return_value = Decimal('100.00')

        # Test data
        asset_data = {
            'symbol': 'AAPL',
            'quantity': 10,
        }

        # Test without target currency
        value = self.calculator.get_current_value(asset_data)

        # Assert
        self.assertIsNotNone(value)
        self.assertEqual(value, Decimal('1000.00'))
        self.mock_converter.convert.assert_not_called()

    def test_get_current_value_same_currency(self):
        """Test calculating current value when currencies match."""
        # Mock the data fetcher
        self.mock_fetcher.get_current_price.return_value = Decimal('100.00')
        self.mock_fetcher.get_currency.return_value = 'USD'

        # Test data
        asset_data = {
            'symbol': 'AAPL',
            'quantity': 10,
        }

        # Test with same currency
        value = self.calculator.get_current_value(asset_data, target_currency='USD')

        # Assert
        self.assertIsNotNone(value)
        self.assertEqual(value, Decimal('1000.00'))
        # Converter should NOT be called when currencies are the same
        self.mock_converter.convert.assert_not_called()
