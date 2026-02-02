"""
Unit tests for asset calculators.
"""
from django.test import TestCase
from unittest.mock import Mock, patch
from decimal import Decimal
from datetime import date

from analytics.services.calculators import StockCalculator, BondCalculator
from analytics.services.data_fetchers import StockDataFetcher
from analytics.services.currency_converter import CurrencyConverter


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


class TestBondCalculator(TestCase):
    """
    Unit tests for BondCalculator (Polish Treasury Bonds).
    """

    def test_get_asset_type(self):
        """BondCalculator returns 'bonds' as asset type."""
        calculator = BondCalculator()
        self.assertEqual(calculator.get_asset_type(), 'bonds')

    def test_get_current_value_returns_none_for_invalid_data(self):
        """get_current_value returns None when maturity_date is missing or quantity is invalid."""
        calculator = BondCalculator()
        self.assertIsNone(calculator.get_current_value({
            'quantity': 10,
            'face_value': 100,  # common_rules: nominal_value 100
            # no maturity_date
        }))
        self.assertIsNone(calculator.get_current_value({
            'maturity_date': '2026-06-30',
            'quantity': 0,
            'face_value': 100,
        }))
        self.assertIsNone(calculator.get_current_value({
            'maturity_date': '2026-12-31',
            'quantity': None,
            'face_value': 100,
        }))

    @patch('analytics.services.calculators.date')
    def test_get_current_value_inflation_indexed_bond_edo(self, mock_date):
        """EDO (10Y): inflation-indexed, fixed in year 1, inflation+margin later, annual capitalization (Actual/365)."""
        mock_date.today.return_value = date(2025, 6, 15)
        mock_date.side_effect = lambda year, month, day: date(year, month, day)
        calculator = BondCalculator(projected_inflation=Decimal('5'))
        asset_data = {
            'face_value': 100,  # common_rules: nominal_value 100 PLN
            'quantity': Decimal('1'),
            'maturity_date': '2033-01-01',  # EDO maturity = 10 years
            'purchase_date': '2023-01-01',
            'bond_type': 'EDO',
            'interest_rate_type': 'indexed_inflation',
            'base_interest_rate': Decimal('6.25'),   # year 0: fixed
            'inflation_margin': Decimal('2.0'),    # year 1+: inflation 5% + 2.0% = 7.0%
        }
        value = calculator.get_current_value(asset_data)
        self.assertIsNotNone(value)
        # Year 0: capital = 100 * (1 + 6.25/100) = 106.25
        capital = Decimal('100') * (Decimal('1') + Decimal('6.25') / Decimal('100'))
        # Year 1: capital = 106.25 * (1 + 7.0/100) = 113.68
        capital = capital * (Decimal('1') + (Decimal('5') + Decimal('2.0')) / Decimal('100'))
        # Year 2 YTD: from 2025-01-01 to 2025-06-15 = 165 days, rate 7.0%
        days_ytd = (date(2025, 6, 15) - date(2025, 1, 1)).days
        interest_ytd = (
            capital * (Decimal('5') + Decimal('2.0')) * Decimal(str(days_ytd))
            / Decimal('365') / Decimal('100')
        )
        expected_value = (capital + interest_ytd) * Decimal('1')
        self.assertEqual(value, expected_value)

    @patch('analytics.services.calculators.date')
    def test_get_current_value_fixed_bond_tos(self, mock_date):
        """TOS (3Y): fixed, annual capitalization - capital after last anniversary + interest YTD (capital_annual * rate * days/365)."""
        mock_date.today.return_value = date(2024, 6, 15)
        mock_date.side_effect = lambda year, month, day: date(year, month, day)
        calculator = BondCalculator()
        asset_data = {
            'face_value': 100,
            'quantity': Decimal('1'),
            'maturity_date': '2026-01-01',  # TOS = 3 years
            'purchase_date': '2023-01-01',
            'bond_type': 'TOS',
            'interest_rate_type': 'fixed',
            'interest_rate': Decimal('5.65'),
        }
        value = calculator.get_current_value(asset_data)
        self.assertIsNotNone(value)
        # TOS: annual capitalization. After 1 year: capital = 100 * (1 + 5.65/100) = 105.65
        capital_after_year1 = Decimal('100') * (Decimal('1') + Decimal('5.65') / Decimal('100'))
        # YTD from 2024-01-01 to 2024-06-15 (166 days in leap year)
        days_ytd = (date(2024, 6, 15) - date(2024, 1, 1)).days
        interest_ytd = (
            capital_after_year1 * Decimal('5.65') * Decimal(str(days_ytd))
            / Decimal('365') / Decimal('100')
        )
        expected_value = (capital_after_year1 + interest_ytd) * Decimal('1')
        self.assertEqual(value, expected_value)

    @patch('analytics.services.calculators.date')
    @patch('analytics.services.calculators.get_latest_wibor')
    def test_get_current_value_variable_wibor_bond_ror(self, mock_get_wibor, mock_date):
        """ROR (1Y): variable WIBOR - value = nominal + simple interest from purchase to today (Actual/365)."""
        mock_date.today.return_value = date(2024, 7, 15)
        mock_date.side_effect = lambda year, month, day: date(year, month, day)
        mock_get_wibor.return_value = Decimal('5.75')
        calculator = BondCalculator()
        asset_data = {
            'face_value': 100,
            'quantity': Decimal('1'),
            'maturity_date': '2025-01-01',  # ROR = 1 year
            'purchase_date': '2024-01-01',
            'bond_type': 'ROR',
            'interest_rate_type': 'variable_wibor',
            'wibor_margin': Decimal('1.25'),
            'wibor_type': '3M',
        }
        value = calculator.get_current_value(asset_data)
        self.assertIsNotNone(value)
        total_nominal = Decimal('100')
        days = (date(2024, 7, 15) - date(2024, 1, 1)).days
        rate = Decimal('5.75') + Decimal('1.25')  # WIBOR + margin
        expected_interest = (
            total_nominal * rate * Decimal(str(days))
            / Decimal('365') / Decimal('100')
        )
        expected_value = total_nominal + expected_interest
        self.assertEqual(value, expected_value)
        mock_get_wibor.assert_called_once_with('3M')
