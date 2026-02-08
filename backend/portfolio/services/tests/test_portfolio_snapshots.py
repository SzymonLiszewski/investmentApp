"""
Unit tests for PortfolioSnapshotService.
"""
from datetime import date
from decimal import Decimal
from unittest.mock import Mock, patch

import pandas as pd
from django.test import TestCase
from django.contrib.auth.models import User

from base.models import Asset
from portfolio.models import Transactions
from portfolio.models import PortfolioSnapshot
from portfolio.services.asset_manager import AssetManager
from base.services.market_data_fetcher import StockDataFetcher, CryptoDataFetcher
from portfolio.services.portfolio_snapshots import PortfolioSnapshotService


def _make_price_series(dates, prices):
    """Helper — build a pd.Series indexed by ``datetime.date``."""
    return pd.Series(prices, index=dates)


class PortfolioSnapshotServiceTests(TestCase):
    """Tests for building portfolio value snapshots."""

    def setUp(self):
        self.user = User.objects.create_user("testuser", "test@test.com", "pass")
        self.stock = Asset.objects.create(
            symbol="AAPL",
            name="Apple Inc.",
            asset_type="stocks",
        )
        self.bond = Asset.objects.create(
            name="Bond EDO1234",
            asset_type="bonds",
            bond_type="EDO",
            face_value=Decimal("100.00"),
            maturity_date=date(2030, 1, 1),
        )

        # Inject mock fetchers for both stocks and crypto
        self.mock_stock_fetcher = Mock(spec=StockDataFetcher)
        self.mock_crypto_fetcher = Mock(spec=CryptoDataFetcher)

        # Default: return empty so tests that don't need prices work
        self.mock_stock_fetcher.get_historical_prices.return_value = {}
        self.mock_crypto_fetcher.get_historical_prices.return_value = {}

        self.service = PortfolioSnapshotService(
            currency="USD",
            stock_data_fetcher=self.mock_stock_fetcher,
            crypto_data_fetcher=self.mock_crypto_fetcher,
        )

    # ------------------------------------------------------------------
    # Stock tests
    # ------------------------------------------------------------------

    def test_build_snapshots_single_stock(self):
        """BUY 10 AAPL — snapshots should equal price × qty each day."""
        Transactions.objects.create(
            owner=self.user,
            product=self.stock,
            transactionType="B",
            quantity=10,
            price=150.0,
            date=date(2026, 1, 1),
        )

        self.mock_stock_fetcher.get_historical_prices.return_value = {
            "AAPL": _make_price_series(
                [date(2026, 1, 1), date(2026, 1, 2), date(2026, 1, 3)],
                [150.0, 155.0, 152.0],
            ),
        }

        snapshots = self.service.build_snapshots_for_user(
            self.user, date(2026, 1, 1), date(2026, 1, 3), currency="USD",
        )

        self.assertEqual(len(snapshots), 3)
        self.assertAlmostEqual(float(snapshots[0].total_value), 1500.0, places=2)
        self.assertAlmostEqual(float(snapshots[1].total_value), 1550.0, places=2)
        self.assertAlmostEqual(float(snapshots[2].total_value), 1520.0, places=2)

        # Verify stock fetcher was called with stock symbols only
        call_args = self.mock_stock_fetcher.get_historical_prices.call_args
        self.assertEqual(call_args[0][0], ["AAPL"])

    def test_build_snapshots_buy_and_sell(self):
        """BUY 10 on Jan 1, SELL 5 on Jan 2 → quantity at Jan 3 = 5."""
        Transactions.objects.create(
            owner=self.user,
            product=self.stock,
            transactionType="B",
            quantity=10,
            price=150.0,
            date=date(2026, 1, 1),
        )
        Transactions.objects.create(
            owner=self.user,
            product=self.stock,
            transactionType="S",
            quantity=5,
            price=155.0,
            date=date(2026, 1, 2),
        )

        self.mock_stock_fetcher.get_historical_prices.return_value = {
            "AAPL": _make_price_series(
                [date(2026, 1, 1), date(2026, 1, 2), date(2026, 1, 3)],
                [150.0, 155.0, 160.0],
            ),
        }

        snapshots = self.service.build_snapshots_for_user(
            self.user, date(2026, 1, 1), date(2026, 1, 3), currency="USD",
        )

        self.assertEqual(len(snapshots), 3)
        self.assertAlmostEqual(float(snapshots[0].total_value), 1500.0, places=2)
        self.assertAlmostEqual(float(snapshots[1].total_value), 775.0, places=2)
        self.assertAlmostEqual(float(snapshots[2].total_value), 800.0, places=2)

    # ------------------------------------------------------------------
    # Bond tests
    # ------------------------------------------------------------------

    def test_build_snapshots_with_bond(self):
        """Bond valued via BondCalculator with interest accrual (no conversion needed)."""
        Transactions.objects.create(
            owner=self.user,
            product=self.bond,
            transactionType="B",
            quantity=5,
            price=100.0,
            date=date(2026, 1, 1),
        )

        snapshots = self.service.build_snapshots_for_user(
            self.user, date(2026, 1, 1), date(2026, 1, 2), currency="PLN",
        )

        self.assertEqual(len(snapshots), 2)
        # Day 0 (purchase day): purchase_date == valuation_date → face_value × qty
        self.assertAlmostEqual(float(snapshots[0].total_value), 500.0, places=2)
        # Day 1: interest starts accruing → value >= face_value × qty
        self.assertGreaterEqual(float(snapshots[1].total_value), 500.0)

    # ------------------------------------------------------------------
    # Crypto tests
    # ------------------------------------------------------------------

    def test_crypto_uses_crypto_fetcher(self):
        """Crypto symbols are sent to crypto_data_fetcher, not stock_data_fetcher."""
        crypto = Asset.objects.create(
            symbol="BTC",
            name="Bitcoin",
            asset_type="cryptocurrencies",
        )
        Transactions.objects.create(
            owner=self.user,
            product=crypto,
            transactionType="B",
            quantity=1,
            price=50000.0,
            date=date(2026, 1, 1),
        )

        # Crypto fetcher receives DB-format symbol ('BTC'), returns keyed by 'BTC'
        self.mock_crypto_fetcher.get_historical_prices.return_value = {
            "BTC": _make_price_series([date(2026, 1, 1)], [50000.0]),
        }

        snapshots = self.service.build_snapshots_for_user(
            self.user, date(2026, 1, 1), date(2026, 1, 1), currency="USD",
        )

        # Verify crypto fetcher was called with DB-format symbol
        crypto_call = self.mock_crypto_fetcher.get_historical_prices.call_args
        self.assertEqual(crypto_call[0][0], ["BTC"])

        # Verify stock fetcher was NOT called with crypto symbols
        stock_call = self.mock_stock_fetcher.get_historical_prices.call_args
        # stock_data_fetcher should not be called at all (no stocks)
        self.assertIsNone(stock_call)

        self.assertEqual(len(snapshots), 1)
        self.assertAlmostEqual(float(snapshots[0].total_value), 50000.0, places=2)

    def test_mixed_stock_and_crypto(self):
        """Stocks go to stock_fetcher, crypto goes to crypto_fetcher."""
        crypto = Asset.objects.create(
            symbol="ETH",
            name="Ethereum",
            asset_type="cryptocurrencies",
        )
        Transactions.objects.create(
            owner=self.user,
            product=self.stock,
            transactionType="B",
            quantity=10,
            price=150.0,
            date=date(2026, 1, 1),
        )
        Transactions.objects.create(
            owner=self.user,
            product=crypto,
            transactionType="B",
            quantity=2,
            price=3000.0,
            date=date(2026, 1, 1),
        )

        self.mock_stock_fetcher.get_historical_prices.return_value = {
            "AAPL": _make_price_series([date(2026, 1, 1)], [150.0]),
        }
        self.mock_crypto_fetcher.get_historical_prices.return_value = {
            "ETH": _make_price_series([date(2026, 1, 1)], [3000.0]),
        }

        snapshots = self.service.build_snapshots_for_user(
            self.user, date(2026, 1, 1), date(2026, 1, 1), currency="USD",
        )

        # Stock fetcher called with ['AAPL']
        stock_call = self.mock_stock_fetcher.get_historical_prices.call_args
        self.assertEqual(stock_call[0][0], ["AAPL"])

        # Crypto fetcher called with ['ETH']
        crypto_call = self.mock_crypto_fetcher.get_historical_prices.call_args
        self.assertEqual(crypto_call[0][0], ["ETH"])

        # Total = 10×150 + 2×3000 = 7500
        self.assertEqual(len(snapshots), 1)
        self.assertAlmostEqual(float(snapshots[0].total_value), 7500.0, places=2)

    # ------------------------------------------------------------------
    # General tests
    # ------------------------------------------------------------------

    def test_build_snapshots_no_transactions(self):
        """User with no transactions → empty list."""
        other_user = User.objects.create_user("other", "other@test.com", "pass")

        snapshots = self.service.build_snapshots_for_user(
            other_user, date(2026, 1, 1), date(2026, 1, 3),
        )

        self.assertEqual(len(snapshots), 0)

    def test_snapshots_update_or_create(self):
        """Running twice overwrites existing snapshots (no duplicates)."""
        Transactions.objects.create(
            owner=self.user,
            product=self.stock,
            transactionType="B",
            quantity=10,
            price=150.0,
            date=date(2026, 1, 1),
        )

        self.mock_stock_fetcher.get_historical_prices.return_value = {
            "AAPL": _make_price_series([date(2026, 1, 1)], [150.0]),
        }

        self.service.build_snapshots_for_user(
            self.user, date(2026, 1, 1), date(2026, 1, 1), currency="USD",
        )

        # Change price and rebuild
        self.mock_stock_fetcher.get_historical_prices.return_value = {
            "AAPL": _make_price_series([date(2026, 1, 1)], [200.0]),
        }

        self.service.build_snapshots_for_user(
            self.user, date(2026, 1, 1), date(2026, 1, 1), currency="USD",
        )

        count = PortfolioSnapshot.objects.filter(
            user=self.user, date=date(2026, 1, 1), currency="USD",
        ).count()
        self.assertEqual(count, 1)

        snap = PortfolioSnapshot.objects.get(
            user=self.user, date=date(2026, 1, 1), currency="USD",
        )
        self.assertAlmostEqual(float(snap.total_value), 2000.0, places=2)

    def test_weekend_forward_fill(self):
        """When no price on a date, the last known price is used."""
        Transactions.objects.create(
            owner=self.user,
            product=self.stock,
            transactionType="B",
            quantity=10,
            price=150.0,
            date=date(2026, 1, 2),  # Friday
        )

        self.mock_stock_fetcher.get_historical_prices.return_value = {
            "AAPL": _make_price_series([date(2026, 1, 2)], [150.0]),
        }

        snapshots = self.service.build_snapshots_for_user(
            self.user,
            date(2026, 1, 2),
            date(2026, 1, 4),  # Sun
            currency="USD",
        )

        self.assertEqual(len(snapshots), 3)
        for snap in snapshots:
            self.assertAlmostEqual(float(snap.total_value), 1500.0, places=2)


class PortfolioSnapshotCurrencyConversionTests(TestCase):
    """Tests for currency conversion within snapshot building."""

    def setUp(self):
        self.user = User.objects.create_user("testuser", "test@test.com", "pass")
        self.stock_us = Asset.objects.create(
            symbol="AAPL", name="Apple Inc.", asset_type="stocks",
        )
        self.stock_wa = Asset.objects.create(
            symbol="CDR.WA", name="CD Projekt", asset_type="stocks",
        )
        self.bond = Asset.objects.create(
            name="Bond EDO1234",
            asset_type="bonds",
            bond_type="EDO",
            face_value=Decimal("100.00"),
            maturity_date=date(2030, 1, 1),
        )

        self.mock_stock_fetcher = Mock(spec=StockDataFetcher)
        self.mock_crypto_fetcher = Mock(spec=CryptoDataFetcher)
        self.mock_stock_fetcher.get_historical_prices.return_value = {}
        self.mock_crypto_fetcher.get_historical_prices.return_value = {}

    def _make_service(self, currency, mock_converter):
        """Create a PortfolioSnapshotService with a mocked CurrencyConverter."""
        asset_manager = AssetManager(default_currency=currency)
        asset_manager.currency_converter = mock_converter
        return PortfolioSnapshotService(
            currency=currency,
            stock_data_fetcher=self.mock_stock_fetcher,
            crypto_data_fetcher=self.mock_crypto_fetcher,
            asset_manager=asset_manager,
        )

    def test_us_stock_converted_to_pln(self):
        """US stock snapshot in PLN converts from USD."""
        mock_converter = Mock()
        mock_converter.convert.return_value = Decimal('6000')  # 1500 USD → 6000 PLN

        service = self._make_service('PLN', mock_converter)

        Transactions.objects.create(
            owner=self.user, product=self.stock_us,
            transactionType="B", quantity=10, price=150.0,
            date=date(2026, 1, 1),
        )
        self.mock_stock_fetcher.get_historical_prices.return_value = {
            "AAPL": _make_price_series([date(2026, 1, 1)], [150.0]),
        }

        snapshots = service.build_snapshots_for_user(
            self.user, date(2026, 1, 1), date(2026, 1, 1), currency="PLN",
        )

        self.assertEqual(len(snapshots), 1)
        self.assertAlmostEqual(float(snapshots[0].total_value), 6000.0, places=2)
        mock_converter.convert.assert_called_with(
            Decimal('1500'), 'USD', 'PLN',
        )

    def test_wa_stock_no_conversion_in_pln(self):
        """Warsaw stock snapshot in PLN — no conversion needed."""
        mock_converter = Mock()
        service = self._make_service('PLN', mock_converter)

        Transactions.objects.create(
            owner=self.user, product=self.stock_wa,
            transactionType="B", quantity=5, price=200.0,
            date=date(2026, 1, 1),
        )
        self.mock_stock_fetcher.get_historical_prices.return_value = {
            "CDR.WA": _make_price_series([date(2026, 1, 1)], [200.0]),
        }

        snapshots = service.build_snapshots_for_user(
            self.user, date(2026, 1, 1), date(2026, 1, 1), currency="PLN",
        )

        self.assertEqual(len(snapshots), 1)
        self.assertAlmostEqual(float(snapshots[0].total_value), 1000.0, places=2)
        mock_converter.convert.assert_not_called()

    def test_bond_converted_to_usd(self):
        """Bond snapshot in USD converts from PLN."""
        mock_converter = Mock()
        mock_converter.convert.return_value = Decimal('125')  # 500 PLN → 125 USD

        service = self._make_service('USD', mock_converter)

        Transactions.objects.create(
            owner=self.user, product=self.bond,
            transactionType="B", quantity=5, price=100.0,
            date=date(2026, 1, 1),
        )

        snapshots = service.build_snapshots_for_user(
            self.user, date(2026, 1, 1), date(2026, 1, 1), currency="USD",
        )

        self.assertEqual(len(snapshots), 1)
        self.assertAlmostEqual(float(snapshots[0].total_value), 125.0, places=2)
        mock_converter.convert.assert_called_once_with(
            Decimal('500'), 'PLN', 'USD',
        )

    def test_mixed_portfolio_conversion(self):
        """US stock + WA stock + bond with target PLN."""
        def mock_convert(amount, from_cur, to_cur):
            if from_cur == 'USD' and to_cur == 'PLN':
                return amount * Decimal('4')
            return amount

        mock_converter = Mock()
        mock_converter.convert.side_effect = mock_convert

        service = self._make_service('PLN', mock_converter)

        Transactions.objects.create(
            owner=self.user, product=self.stock_us,
            transactionType="B", quantity=10, price=150.0,
            date=date(2026, 1, 1),
        )
        Transactions.objects.create(
            owner=self.user, product=self.stock_wa,
            transactionType="B", quantity=5, price=200.0,
            date=date(2026, 1, 1),
        )
        Transactions.objects.create(
            owner=self.user, product=self.bond,
            transactionType="B", quantity=3, price=100.0,
            date=date(2026, 1, 1),
        )

        self.mock_stock_fetcher.get_historical_prices.return_value = {
            "AAPL": _make_price_series([date(2026, 1, 1)], [150.0]),
            "CDR.WA": _make_price_series([date(2026, 1, 1)], [200.0]),
        }

        snapshots = service.build_snapshots_for_user(
            self.user, date(2026, 1, 1), date(2026, 1, 1), currency="PLN",
        )

        # AAPL: 10×150 = 1500 USD → 6000 PLN
        # CDR.WA: 5×200 = 1000 PLN (no conversion)
        # Bond: 3×100 = 300 PLN (no conversion)
        self.assertEqual(len(snapshots), 1)
        self.assertAlmostEqual(float(snapshots[0].total_value), 7300.0, places=2)
