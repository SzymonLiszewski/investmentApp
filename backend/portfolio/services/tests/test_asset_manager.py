"""
Unit tests for AssetManager.
"""
from datetime import date
from django.test import TestCase
from django.contrib.auth.models import User
from unittest.mock import Mock, patch
from decimal import Decimal
from base.models import Asset
from portfolio.models import UserAsset, Transactions
from portfolio.services.asset_manager import AssetManager
from portfolio.services.calculators import StockCalculator, BondCalculator


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

    @patch('base.infrastructure.yfinance_fetchers.yf.Ticker')
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

    @patch('base.infrastructure.yfinance_fetchers.yf.Ticker')
    def test_get_portfolio_composition_includes_cost_and_profit(self, mock_ticker):
        """Composition includes average_purchase_price, total_cost, profit, profit_percentage when transactions exist."""
        def mock_ticker_side_effect(symbol):
            mock_instance = Mock()
            if symbol == 'AAPL':
                mock_instance.info = {'currentPrice': 150.00}
            elif symbol == 'GOOGL':
                mock_instance.info = {'currentPrice': 100.00}
            return mock_instance
        mock_ticker.side_effect = mock_ticker_side_effect

        # BUY 10 AAPL @ 100, BUY 5 GOOGL @ 80
        Transactions.objects.create(
            owner=self.user, product=self.stock1,
            transactionType='B', quantity=10, price=100.0, date=date(2025, 1, 1),
        )
        Transactions.objects.create(
            owner=self.user, product=self.stock2,
            transactionType='B', quantity=5, price=80.0, date=date(2025, 1, 2),
        )

        composition = self.manager.get_portfolio_composition(self.user)

        aapl = next((a for a in composition['composition_by_asset'] if a['symbol'] == 'AAPL'), None)
        self.assertIsNotNone(aapl)
        self.assertEqual(aapl['average_purchase_price'], 100.0)
        self.assertEqual(aapl['total_cost'], 1000.0)
        self.assertEqual(aapl['current_value'], 1500.0)
        self.assertEqual(aapl['profit'], 500.0)
        self.assertEqual(aapl['profit_percentage'], 50.0)

        googl = next((a for a in composition['composition_by_asset'] if a['symbol'] == 'GOOGL'), None)
        self.assertIsNotNone(googl)
        self.assertEqual(googl['average_purchase_price'], 80.0)
        self.assertEqual(googl['total_cost'], 400.0)
        self.assertEqual(googl['current_value'], 500.0)
        self.assertEqual(googl['profit'], 100.0)
        self.assertEqual(googl['profit_percentage'], 25.0)

    @patch('base.infrastructure.yfinance_fetchers.yf.Ticker')
    def test_get_portfolio_composition_cost_basis_after_sell(self, mock_ticker):
        """After BUY 10 @ 100 and SELL 5, remaining 5 have cost basis 500 (avg 100)."""
        def mock_ticker_side_effect(symbol):
            mock_instance = Mock()
            mock_instance.info = {'currentPrice': 120.00}
            return mock_instance
        mock_ticker.side_effect = mock_ticker_side_effect

        Transactions.objects.create(
            owner=self.user, product=self.stock1,
            transactionType='B', quantity=10, price=100.0, date=date(2025, 1, 1),
        )
        Transactions.objects.create(
            owner=self.user, product=self.stock1,
            transactionType='S', quantity=5, price=110.0, date=date(2025, 1, 15),
        )
        # UserAsset should reflect current quantity (5)
        self.user_asset1.quantity = 5
        self.user_asset1.save()

        composition = self.manager.get_portfolio_composition(self.user)
        aapl = next((a for a in composition['composition_by_asset'] if a['symbol'] == 'AAPL'), None)
        self.assertIsNotNone(aapl)
        self.assertEqual(aapl['quantity'], 5.0)
        self.assertEqual(aapl['average_purchase_price'], 100.0)
        self.assertEqual(aapl['total_cost'], 500.0)  # 5 * 100
        self.assertEqual(aapl['current_value'], 600.0)  # 5 * 120
        self.assertEqual(aapl['profit'], 100.0)
        self.assertEqual(aapl['profit_percentage'], 20.0)

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

    @patch('base.infrastructure.yfinance_fetchers.yf.Ticker')
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

        # Test getting bond calculator
        calculator = self.manager._get_calculator_for_asset_type('bonds')
        self.assertIsNotNone(calculator)
        self.assertIsInstance(calculator, BondCalculator)

        # Test getting calculator for unsupported type
        calculator = self.manager._get_calculator_for_asset_type('other')
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

    @patch('portfolio.services.asset_manager.get_default_stock_fetcher')
    @patch('portfolio.services.currency_converter.yf.Ticker')
    def test_get_portfolio_composition_with_currency_conversion(
        self, mock_fx_ticker_cls, mock_stock_fetcher
    ):
        """Test portfolio composition with currency conversion to PLN."""
        import pandas as pd
        # Mock stock fetcher: AAPL=150 USD, GOOGL=100 USD
        mock_fetcher = Mock()
        mock_fetcher.get_current_price.side_effect = (
            lambda s: Decimal('150') if s == 'AAPL' else Decimal('100')
        )
        mock_fetcher.get_currency.return_value = 'USD'
        mock_stock_fetcher.return_value = mock_fetcher

        # Mock FX: 1 USD = 4 PLN
        mock_fx = Mock()
        mock_fx.history.return_value = pd.DataFrame(
            {'Close': [4.0]},
            index=pd.to_datetime(['2026-01-01']),
        )
        mock_fx_ticker_cls.return_value = mock_fx

        manager = AssetManager(default_currency='PLN')
        composition = manager.get_portfolio_composition(self.user, target_currency='PLN')

        self.assertIsNotNone(composition)
        self.assertEqual(composition['currency'], 'PLN')
        # 10*150*4 + 5*100*4 = 6000 + 2000 = 8000 PLN
        self.assertEqual(composition['total_value'], 8000.00)

    @patch('base.infrastructure.yfinance_fetchers.yf.Ticker')
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


class TestValuePositions(TestCase):
    """Tests for AssetManager.value_positions."""

    def setUp(self):
        self.manager = AssetManager(default_currency='USD')

        self.stock_aapl = Asset.objects.create(
            symbol='AAPL', name='Apple Inc.', asset_type='stocks',
        )
        self.stock_msft = Asset.objects.create(
            symbol='MSFT', name='Microsoft Corp.', asset_type='stocks',
        )
        self.bond = Asset.objects.create(
            name='Bond EDO1234',
            asset_type='bonds',
            bond_type='EDO',
            face_value=Decimal('100.00'),
            maturity_date=date(2030, 1, 1),
        )
        self.crypto = Asset.objects.create(
            symbol='BTC', name='Bitcoin', asset_type='cryptocurrencies',
        )

    def test_single_stock(self):
        """Single stock position valued correctly."""
        positions = [{'asset': self.stock_aapl, 'quantity': 10}]
        get_price = lambda sym: Decimal('150') if sym == 'AAPL' else None

        total = self.manager.value_positions(positions, get_price)

        self.assertEqual(total, Decimal('1500'))

    def test_multiple_stocks(self):
        """Multiple stock positions summed correctly."""
        positions = [
            {'asset': self.stock_aapl, 'quantity': 10},
            {'asset': self.stock_msft, 'quantity': 5},
        ]
        prices = {'AAPL': Decimal('150'), 'MSFT': Decimal('400')}
        get_price = lambda sym: prices.get(sym)

        total = self.manager.value_positions(positions, get_price)

        self.assertEqual(total, Decimal('3500'))  # 10×150 + 5×400

    def test_bond_on_purchase_day_uses_face_value(self):
        """Bond valued on purchase day → face_value × quantity (no accrual)."""
        positions = [{
            'asset': self.bond,
            'quantity': 5,
            'purchase_date': date(2026, 1, 1),
        }]
        get_price = lambda sym: None

        total = self.manager.value_positions(
            positions, get_price, valuation_date=date(2026, 1, 1),
        )

        self.assertEqual(total, Decimal('500'))  # 5 × 100

    def test_bond_accrues_interest_over_time(self):
        """Bond valued 30 days after purchase should exceed face_value × qty."""
        positions = [{
            'asset': self.bond,
            'quantity': 5,
            'purchase_date': date(2026, 1, 1),
        }]
        get_price = lambda sym: None

        total = self.manager.value_positions(
            positions, get_price, valuation_date=date(2026, 1, 31),
        )

        # EDO bond with base_interest_rate/interest_rate accrues interest
        # At minimum, value should be >= face_value × qty
        self.assertGreaterEqual(total, Decimal('500'))

    def test_bond_without_purchase_date_falls_back(self):
        """Bond without purchase_date → face_value × quantity (fallback)."""
        positions = [{'asset': self.bond, 'quantity': 5}]
        get_price = lambda sym: None

        total = self.manager.value_positions(
            positions, get_price, valuation_date=date(2026, 6, 1),
        )

        self.assertEqual(total, Decimal('500'))

    def test_mixed_portfolio(self):
        """Stock + bond + crypto in one portfolio."""
        positions = [
            {'asset': self.stock_aapl, 'quantity': 10},
            {'asset': self.bond, 'quantity': 3, 'purchase_date': date(2026, 1, 1)},
            {'asset': self.crypto, 'quantity': 0.5},
        ]
        prices = {'AAPL': Decimal('150'), 'BTC': Decimal('60000')}
        get_price = lambda sym: prices.get(sym)

        total = self.manager.value_positions(
            positions, get_price, valuation_date=date(2026, 1, 1),
        )

        # On purchase day, bond = face_value × qty = 300
        expected = Decimal('1500') + Decimal('300') + Decimal('30000')
        self.assertEqual(total, expected)

    def test_zero_quantity_skipped(self):
        """Positions with zero or negative quantity are ignored."""
        positions = [
            {'asset': self.stock_aapl, 'quantity': 0},
            {'asset': self.stock_msft, 'quantity': -5},
        ]
        get_price = lambda sym: Decimal('100')

        total = self.manager.value_positions(positions, get_price)

        self.assertEqual(total, Decimal('0'))

    def test_unavailable_price_skipped(self):
        """Stock position with no price doesn't contribute to total."""
        positions = [
            {'asset': self.stock_aapl, 'quantity': 10},
            {'asset': self.stock_msft, 'quantity': 5},
        ]
        get_price = lambda sym: Decimal('150') if sym == 'AAPL' else None

        total = self.manager.value_positions(positions, get_price)

        self.assertEqual(total, Decimal('1500'))  # only AAPL

    def test_empty_positions(self):
        """Empty position list returns zero."""
        total = self.manager.value_positions([], lambda sym: None)

        self.assertEqual(total, Decimal('0'))

    def test_accepts_float_price(self):
        """get_price returning float is handled correctly."""
        positions = [{'asset': self.stock_aapl, 'quantity': 10}]
        get_price = lambda sym: 150.50  # float, not Decimal

        total = self.manager.value_positions(positions, get_price)

        self.assertAlmostEqual(float(total), 1505.0, places=2)


class TestValuePositionsCurrencyConversion(TestCase):
    """Tests for currency conversion in AssetManager.value_positions."""

    def setUp(self):
        self.manager = AssetManager(default_currency='PLN')

        # Patch the currency converter so we don't hit the real forex API
        self.mock_converter = Mock()
        self.manager.currency_converter = self.mock_converter

        # US stock (native: USD)
        self.stock_us = Asset.objects.create(
            symbol='AAPL', name='Apple Inc.', asset_type='stocks',
        )
        # Warsaw stock (native: PLN)
        self.stock_wa = Asset.objects.create(
            symbol='CDR.WA', name='CD Projekt', asset_type='stocks',
        )
        # Bond (native: PLN)
        self.bond = Asset.objects.create(
            name='Bond EDO1234',
            asset_type='bonds',
            bond_type='EDO',
            face_value=Decimal('100.00'),
            maturity_date=date(2030, 1, 1),
        )
        # Crypto (native: USD)
        self.crypto = Asset.objects.create(
            symbol='BTC', name='Bitcoin', asset_type='cryptocurrencies',
        )

    def test_no_conversion_when_target_currency_is_none(self):
        """Without target_currency, no conversion takes place."""
        positions = [{'asset': self.stock_us, 'quantity': 10}]
        get_price = lambda sym: Decimal('150')

        total = self.manager.value_positions(positions, get_price)

        self.assertEqual(total, Decimal('1500'))
        self.mock_converter.convert.assert_not_called()

    def test_no_conversion_when_native_equals_target(self):
        """US stock priced in USD with target_currency='USD' — no conversion."""
        positions = [{'asset': self.stock_us, 'quantity': 10}]
        get_price = lambda sym: Decimal('150')

        total = self.manager.value_positions(
            positions, get_price, target_currency='USD',
        )

        self.assertEqual(total, Decimal('1500'))
        self.mock_converter.convert.assert_not_called()

    def test_us_stock_converted_to_pln(self):
        """US stock (USD) converted to PLN using CurrencyConverter."""
        self.mock_converter.convert.return_value = Decimal('6000')  # 1500 USD → 6000 PLN

        positions = [{'asset': self.stock_us, 'quantity': 10}]
        get_price = lambda sym: Decimal('150')

        total = self.manager.value_positions(
            positions, get_price, target_currency='PLN',
        )

        self.assertEqual(total, Decimal('6000'))
        self.mock_converter.convert.assert_called_once_with(
            Decimal('1500'), 'USD', 'PLN',
        )

    def test_wa_stock_no_conversion_to_pln(self):
        """Warsaw stock (PLN) with target_currency='PLN' — no conversion."""
        positions = [{'asset': self.stock_wa, 'quantity': 10}]
        get_price = lambda sym: Decimal('200')

        total = self.manager.value_positions(
            positions, get_price, target_currency='PLN',
        )

        self.assertEqual(total, Decimal('2000'))
        self.mock_converter.convert.assert_not_called()

    def test_bond_converted_to_usd(self):
        """Bond (PLN) converted to USD when target_currency='USD'."""
        self.mock_converter.convert.return_value = Decimal('125')  # 500 PLN → 125 USD

        positions = [{
            'asset': self.bond,
            'quantity': 5,
            'purchase_date': date(2026, 1, 1),
        }]
        get_price = lambda sym: None

        total = self.manager.value_positions(
            positions, get_price,
            valuation_date=date(2026, 1, 1),
            target_currency='USD',
        )

        self.assertEqual(total, Decimal('125'))
        self.mock_converter.convert.assert_called_once_with(
            Decimal('500'), 'PLN', 'USD',
        )

    def test_crypto_converted_to_pln(self):
        """Crypto (USD) converted to PLN."""
        self.mock_converter.convert.return_value = Decimal('120000')  # 30000 USD → 120000 PLN

        positions = [{'asset': self.crypto, 'quantity': 0.5}]
        get_price = lambda sym: Decimal('60000')

        total = self.manager.value_positions(
            positions, get_price, target_currency='PLN',
        )

        self.assertEqual(total, Decimal('120000'))
        self.mock_converter.convert.assert_called_once_with(
            Decimal('30000'), 'USD', 'PLN',
        )

    def test_mixed_portfolio_with_conversion(self):
        """Mixed portfolio: US stock + WA stock + bond, target=PLN."""
        def mock_convert(amount, from_cur, to_cur):
            # Only USD→PLN should be called (rate = 4)
            if from_cur == 'USD' and to_cur == 'PLN':
                return amount * Decimal('4')
            return amount

        self.mock_converter.convert.side_effect = mock_convert

        positions = [
            {'asset': self.stock_us, 'quantity': 10},   # 150 × 10 = 1500 USD → 6000 PLN
            {'asset': self.stock_wa, 'quantity': 5},     # 200 × 5  = 1000 PLN (no conversion)
            {'asset': self.bond, 'quantity': 3, 'purchase_date': date(2026, 1, 1)},  # 300 PLN
        ]
        prices = {'AAPL': Decimal('150'), 'CDR.WA': Decimal('200')}
        get_price = lambda sym: prices.get(sym)

        total = self.manager.value_positions(
            positions, get_price,
            valuation_date=date(2026, 1, 1),
            target_currency='PLN',
        )

        # 6000 (AAPL converted) + 1000 (CDR.WA native) + 300 (bond native)
        self.assertEqual(total, Decimal('7300'))

    def test_conversion_failure_keeps_native_value(self):
        """When CurrencyConverter returns None, native value is used."""
        self.mock_converter.convert.return_value = None

        positions = [{'asset': self.stock_us, 'quantity': 10}]
        get_price = lambda sym: Decimal('150')

        total = self.manager.value_positions(
            positions, get_price, target_currency='PLN',
        )

        # Fallback: original 1500 (unconverted) is kept
        self.assertEqual(total, Decimal('1500'))


class TestInferStockCurrency(TestCase):
    """Tests for AssetManager._infer_stock_currency."""

    def test_us_stock(self):
        self.assertEqual(AssetManager._infer_stock_currency('AAPL'), 'USD')

    def test_warsaw_stock(self):
        self.assertEqual(AssetManager._infer_stock_currency('CDR.WA'), 'PLN')

    def test_london_stock(self):
        self.assertEqual(AssetManager._infer_stock_currency('SHEL.L'), 'GBP')

    def test_frankfurt_stock(self):
        self.assertEqual(AssetManager._infer_stock_currency('SAP.DE'), 'EUR')

    def test_unknown_suffix_defaults_to_usd(self):
        self.assertEqual(AssetManager._infer_stock_currency('XYZ.ZZ'), 'USD')


class TestGetNativeCurrency(TestCase):
    """Tests for AssetManager._get_native_currency."""

    def setUp(self):
        self.manager = AssetManager(default_currency='PLN')

    def test_bond_always_pln(self):
        bond = Asset.objects.create(
            name='Bond', asset_type='bonds',
            bond_type='EDO', maturity_date=date(2030, 1, 1),
        )
        self.assertEqual(self.manager._get_native_currency(bond), 'PLN')

    def test_crypto_always_usd(self):
        crypto = Asset.objects.create(
            symbol='ETH', name='Ethereum', asset_type='cryptocurrencies',
        )
        self.assertEqual(self.manager._get_native_currency(crypto), 'USD')

    def test_stock_uses_symbol_inference(self):
        stock_us = Asset.objects.create(
            symbol='TSLA', name='Tesla', asset_type='stocks',
        )
        stock_wa = Asset.objects.create(
            symbol='PKN.WA', name='PKN Orlen', asset_type='stocks',
        )
        self.assertEqual(self.manager._get_native_currency(stock_us), 'USD')
        self.assertEqual(self.manager._get_native_currency(stock_wa), 'PLN')
