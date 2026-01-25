"""
Unit tests for AssetManager.
"""
from django.test import TestCase
from django.contrib.auth.models import User
from unittest.mock import Mock, patch
from decimal import Decimal
from api.models import Asset, UserAsset
from analytics.services.asset_manager import AssetManager
from analytics.services.calculators import StockCalculator


class TestAssetManager(TestCase):
    """Test the AssetManager class."""

    def setUp(self):
        """Set up test fixtures."""
        # Create a test user
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )

        # Create test assets
        self.stock1 = Asset.objects.create(
            symbol='AAPL',
            name='Apple Inc.',
            asset_type='stocks'
        )
        self.stock2 = Asset.objects.create(
            symbol='GOOGL',
            name='Alphabet Inc.',
            asset_type='stocks'
        )

        # Create user assets
        self.user_asset1 = UserAsset.objects.create(
            owner=self.user,
            ownedAsset=self.stock1,
            quantity=10
        )
        self.user_asset2 = UserAsset.objects.create(
            owner=self.user,
            ownedAsset=self.stock2,
            quantity=5
        )

        # Create asset manager with default currency
        self.manager = AssetManager(default_currency='USD')

    def test_initialization(self):
        """Test that AssetManager initializes correctly."""
        self.assertIsNotNone(self.manager.stock_data_fetcher)
        self.assertIsNotNone(self.manager.currency_converter)
        self.assertEqual(self.manager.default_currency, 'USD')
        self.assertIn('stocks', self.manager.calculators)
        self.assertIsInstance(self.manager.calculators['stocks'], StockCalculator)

    @patch('analytics.services.data_fetchers.yf.Ticker')
    def test_get_portfolio_composition_success(self, mock_ticker):
        """Test getting portfolio composition successfully."""
        # Mock yfinance responses
        def mock_ticker_side_effect(symbol):
            mock_instance = Mock()
            if symbol == 'AAPL':
                mock_instance.info = {'currentPrice': 150.00}
            elif symbol == 'GOOGL':
                mock_instance.info = {'currentPrice': 100.00}
            return mock_instance

        mock_ticker.side_effect = mock_ticker_side_effect

        # Test
        composition = self.manager.get_portfolio_composition(self.user)

        # Assert
        self.assertIsNotNone(composition)
        self.assertEqual(composition['total_value'], 2000.00)  # 10*150 + 5*100
        self.assertEqual(composition['currency'], 'USD')
        self.assertEqual(len(composition['assets']), 2)
        
        # Check composition by type
        self.assertIn('stocks', composition['composition_by_type'])
        self.assertEqual(
            composition['composition_by_type']['stocks']['value'],
            2000.00
        )
        self.assertEqual(
            composition['composition_by_type']['stocks']['percentage'],
            100.00
        )

        # Check composition by asset
        self.assertEqual(len(composition['composition_by_asset']), 2)
        
        # Find AAPL in composition
        aapl_asset = next(
            (a for a in composition['composition_by_asset'] if a['symbol'] == 'AAPL'),
            None
        )
        self.assertIsNotNone(aapl_asset)
        self.assertEqual(aapl_asset['current_value'], 1500.00)
        self.assertEqual(aapl_asset['percentage'], 75.00)

        # Find GOOGL in composition
        googl_asset = next(
            (a for a in composition['composition_by_asset'] if a['symbol'] == 'GOOGL'),
            None
        )
        self.assertIsNotNone(googl_asset)
        self.assertEqual(googl_asset['current_value'], 500.00)
        self.assertEqual(googl_asset['percentage'], 25.00)

    def test_get_portfolio_composition_empty_portfolio(self):
        """Test getting composition for user with no assets."""
        # Create a new user with no assets
        empty_user = User.objects.create_user(
            username='emptyuser',
            email='empty@example.com',
            password='testpass123'
        )

        # Test
        composition = self.manager.get_portfolio_composition(empty_user)

        # Assert
        self.assertEqual(composition['total_value'], 0.0)
        self.assertEqual(composition['currency'], 'USD')
        self.assertEqual(len(composition['assets']), 0)
        self.assertEqual(len(composition['composition_by_type']), 0)
        self.assertEqual(len(composition['composition_by_asset']), 0)

    @patch('analytics.services.data_fetchers.yf.Ticker')
    def test_get_portfolio_composition_skips_unavailable_prices(self, mock_ticker):
        """Test that assets with unavailable prices are skipped."""
        # Mock yfinance to return price for AAPL but not GOOGL
        def mock_ticker_side_effect(symbol):
            mock_instance = Mock()
            if symbol == 'AAPL':
                mock_instance.info = {'currentPrice': 150.00}
            elif symbol == 'GOOGL':
                mock_instance.info = {}
                import pandas as pd
                mock_instance.history.return_value = pd.DataFrame()
            return mock_instance

        mock_ticker.side_effect = mock_ticker_side_effect

        # Test
        composition = self.manager.get_portfolio_composition(self.user)

        # Assert - only AAPL should be included
        self.assertEqual(composition['total_value'], 1500.00)  # Only 10*150
        self.assertEqual(len(composition['assets']), 1)
        self.assertEqual(composition['assets'][0]['symbol'], 'AAPL')

    def test_get_calculator_for_asset_type(self):
        """Test getting calculator for asset type."""
        # Test getting stock calculator
        calculator = self.manager._get_calculator_for_asset_type('stocks')
        self.assertIsNotNone(calculator)
        self.assertIsInstance(calculator, StockCalculator)

        # Test getting calculator for unsupported type
        calculator = self.manager._get_calculator_for_asset_type('bonds')
        self.assertIsNone(calculator)

    def test_add_calculator(self):
        """Test adding a new calculator."""
        # Create a mock calculator
        mock_calculator = Mock()
        
        # Add calculator
        self.manager.add_calculator('bonds', mock_calculator)

        # Assert
        self.assertEqual(self.manager.get_calculator('bonds'), mock_calculator)

    def test_get_calculator(self):
        """Test getting calculator by type."""
        # Test getting existing calculator
        calculator = self.manager.get_calculator('stocks')
        self.assertIsNotNone(calculator)

        # Test getting non-existing calculator
        calculator = self.manager.get_calculator('nonexistent')
        self.assertIsNone(calculator)

    @patch('analytics.services.data_fetchers.yf.Ticker')
    @patch('analytics.services.currency_converter.CurrencyRates')
    def test_get_portfolio_composition_with_currency_conversion(
        self, mock_currency_rates, mock_ticker
    ):
        """Test portfolio composition with currency conversion to PLN."""
        # Mock yfinance responses
        def mock_ticker_side_effect(symbol):
            mock_instance = Mock()
            if symbol == 'AAPL':
                mock_instance.info = {
                    'currentPrice': 150.00,
                    'currency': 'USD'
                }
            elif symbol == 'GOOGL':
                mock_instance.info = {
                    'currentPrice': 100.00,
                    'currency': 'USD'
                }
            return mock_instance

        mock_ticker.side_effect = mock_ticker_side_effect

        # Mock currency converter (1 USD = 4 PLN)
        mock_rates = Mock()
        mock_rates.get_rate.return_value = 4.0
        mock_currency_rates.return_value = mock_rates

        # Create new manager to use mocked currency rates
        manager = AssetManager(default_currency='PLN')

        # Test with PLN as target currency
        composition = manager.get_portfolio_composition(self.user, target_currency='PLN')

        # Assert - values should be converted to PLN
        self.assertIsNotNone(composition)
        self.assertEqual(composition['currency'], 'PLN')
        # 10*150*4 + 5*100*4 = 6000 + 2000 = 8000 PLN
        self.assertEqual(composition['total_value'], 8000.00)

    @patch('analytics.services.data_fetchers.yf.Ticker')
    def test_get_portfolio_composition_uses_default_currency(self, mock_ticker):
        """Test that portfolio composition uses default currency when not specified."""
        # Mock yfinance responses
        def mock_ticker_side_effect(symbol):
            mock_instance = Mock()
            mock_instance.info = {'currentPrice': 100.00, 'currency': 'USD'}
            return mock_instance

        mock_ticker.side_effect = mock_ticker_side_effect

        # Create manager with PLN as default
        manager = AssetManager(default_currency='PLN')

        # Test without specifying target currency
        composition = manager.get_portfolio_composition(self.user)

        # Assert - should use default currency
        self.assertEqual(composition['currency'], 'PLN')
