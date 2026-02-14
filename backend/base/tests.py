# Tests for base app
from datetime import date, datetime, timezone, timedelta
from decimal import Decimal
from unittest.mock import Mock

import pandas as pd

from django.test import TestCase

from base.infrastructure.interfaces.market_data_fetcher import StockDataFetcher
from base.infrastructure.db.price_repository import PriceRepository
from base.models import StockDataCache
from base.services.stock_data_cache import get_stock_data_cached


class TestPriceRepositoryGetPriceHistory(TestCase):
    """Tests for PriceRepository.get_price_history."""

    def setUp(self):
        self.repo = PriceRepository()
        self.mock_fetcher = Mock(spec=StockDataFetcher)

    def test_get_price_history_no_missing_does_not_call_fetcher(self):
        """When all business days already exist in DB, returns prices without calling fetcher."""
        symbol = "AAPL"
        start_date = date(2025, 1, 6)
        end_date = date(2025, 1, 10)
        self.repo.save_prices(symbol, [
            {"date": date(2025, 1, 6), "close": Decimal("150")},
            {"date": date(2025, 1, 7), "close": Decimal("151")},
            {"date": date(2025, 1, 8), "close": Decimal("152")},
            {"date": date(2025, 1, 9), "close": Decimal("153")},
            {"date": date(2025, 1, 10), "close": Decimal("154")},
        ])

        result = self.repo.get_price_history(
            symbol, start_date, end_date, self.mock_fetcher
        )

        self.mock_fetcher.get_historical_prices.assert_not_called()
        self.assertEqual(len(result), 5)
        self.assertEqual(result[date(2025, 1, 6)], Decimal("150"))
        self.assertEqual(result[date(2025, 1, 10)], Decimal("154"))

    def test_get_price_history_empty_db_fetches_and_returns_prices(self):
        """When no data in range, fetches from fetcher and returns historical prices."""
        symbol = "AAPL"
        start_date = date(2025, 1, 6)
        end_date = date(2025, 1, 8)
        series = pd.Series({
            pd.Timestamp("2025-01-06"): 100.0,
            pd.Timestamp("2025-01-07"): 101.0,
            pd.Timestamp("2025-01-08"): 102.0,
        })
        self.mock_fetcher.get_historical_prices.return_value = {symbol: series}

        result = self.repo.get_price_history(
            symbol, start_date, end_date, self.mock_fetcher
        )

        self.mock_fetcher.get_historical_prices.assert_called_once_with(
            [symbol], start_date, end_date
        )
        self.assertEqual(len(result), 3)
        self.assertEqual(result[date(2025, 1, 6)], Decimal("100"))
        self.assertEqual(result[date(2025, 1, 8)], Decimal("102"))

    def test_get_price_history_incomplete_data_fills_gap_and_returns_all(self):
        """When some days are missing, fetches missing ones and returns full range."""
        symbol = "GOOGL"
        start_date = date(2025, 1, 6)
        end_date = date(2025, 1, 10)
        self.repo.save_prices(symbol, [
            {"date": date(2025, 1, 6), "close": Decimal("140")},
            {"date": date(2025, 1, 7), "close": Decimal("141")},
        ])
        series = pd.Series({
            pd.Timestamp("2025-01-06"): 140.0,
            pd.Timestamp("2025-01-07"): 141.0,
            pd.Timestamp("2025-01-08"): 142.0,
            pd.Timestamp("2025-01-09"): 143.0,
            pd.Timestamp("2025-01-10"): 144.0,
        })
        self.mock_fetcher.get_historical_prices.return_value = {symbol: series}

        result = self.repo.get_price_history(
            symbol, start_date, end_date, self.mock_fetcher
        )

        self.assertEqual(len(result), 5)
        self.assertEqual(result[date(2025, 1, 10)], Decimal("144"))

    def test_get_price_history_missing_at_start_fetches_beginning(self):
        """When data is missing at the start of the range, fetches and fills it."""
        symbol = "HEAD"
        start_date = date(2025, 1, 6)
        end_date = date(2025, 1, 10)
        self.repo.save_prices(symbol, [
            {"date": date(2025, 1, 8), "close": Decimal("142")},
            {"date": date(2025, 1, 9), "close": Decimal("143")},
            {"date": date(2025, 1, 10), "close": Decimal("144")},
        ])
        series = pd.Series({
            pd.Timestamp("2025-01-06"): 140.0,
            pd.Timestamp("2025-01-07"): 141.0,
        })
        self.mock_fetcher.get_historical_prices.return_value = {symbol: series}

        result = self.repo.get_price_history(
            symbol, start_date, end_date, self.mock_fetcher
        )

        self.mock_fetcher.get_historical_prices.assert_called_once_with(
            [symbol], date(2025, 1, 6), date(2025, 1, 7)
        )
        self.assertEqual(len(result), 5)
        self.assertEqual(result[date(2025, 1, 6)], Decimal("140"))
        self.assertEqual(result[date(2025, 1, 10)], Decimal("144"))

    def test_get_price_history_gap_in_middle_does_not_trigger_fetch(self):
        """Gaps in the middle (e.g. market closed) are not treated as incomplete."""
        symbol = "GAP"
        start_date = date(2025, 1, 6)
        end_date = date(2025, 1, 10)
        self.repo.save_prices(symbol, [
            {"date": date(2025, 1, 6), "close": Decimal("100")},
            {"date": date(2025, 1, 10), "close": Decimal("104")},
        ])

        result = self.repo.get_price_history(
            symbol, start_date, end_date, self.mock_fetcher
        )

        self.mock_fetcher.get_historical_prices.assert_not_called()
        self.assertEqual(len(result), 2)
        self.assertEqual(result[date(2025, 1, 6)], Decimal("100"))
        self.assertEqual(result[date(2025, 1, 10)], Decimal("104"))

    def test_get_price_history_fetcher_returns_empty_returns_whatever_in_db(self):
        """When fetcher returns no data, returns whatever is already in DB (no failure)."""
        symbol = "MISSING"
        start_date = date(2025, 1, 6)
        end_date = date(2025, 1, 8)
        self.mock_fetcher.get_historical_prices.return_value = {}

        result = self.repo.get_price_history(
            symbol, start_date, end_date, self.mock_fetcher
        )

        self.assertEqual(result, {})
        self.mock_fetcher.get_historical_prices.assert_called_once()

    def test_get_price_history_fetcher_raises_returns_whatever_in_db(self):
        """When fetcher raises, returns whatever is in DB and does not propagate."""
        symbol = "ERR"
        start_date = date(2025, 1, 6)
        end_date = date(2025, 1, 8)
        self.mock_fetcher.get_historical_prices.side_effect = RuntimeError("API error")

        result = self.repo.get_price_history(
            symbol, start_date, end_date, self.mock_fetcher
        )

        self.assertEqual(result, {})


class TestGetStockDataCached(TestCase):
    """Tests for get_stock_data_cached."""

    def test_returns_from_cache_when_fresh(self):
        """When cache exists and is within max_age, returns cached data without calling fetcher."""
        symbol = "AAPL"
        data_type = "basic_info"
        cached_data = {"name": "Apple Inc.", "sector": "Technology"}
        StockDataCache.objects.create(
            symbol=symbol,
            data_type=data_type,
            data=cached_data,
        )
        fetcher = Mock()
        result = get_stock_data_cached(symbol, data_type, fetcher)
        self.assertEqual(result, cached_data)
        fetcher.get_basic_stock_info.assert_not_called()

    def test_fetches_and_caches_when_missing(self):
        """When no cache, fetches from fetcher, saves to DB and returns."""
        symbol = "MSFT"
        data_type = "fundamental_analysis"
        fetched = {"pe_ratio": 28.5, "dividend_yield": 0.8}
        fetcher = Mock()
        fetcher.get_fundamental_analysis.return_value = fetched

        result = get_stock_data_cached(symbol, data_type, fetcher)

        fetcher.get_fundamental_analysis.assert_called_once_with(symbol)
        self.assertEqual(result, fetched)
        cached = StockDataCache.objects.get(symbol=symbol, data_type=data_type)
        self.assertEqual(cached.data, fetched)

    def test_fetches_when_cache_stale(self):
        """When cache is older than max_age, refetches and updates cache."""
        symbol = "GOOGL"
        data_type = "technical_indicators"
        old_data = {"rsi": 50}
        StockDataCache.objects.create(
            symbol=symbol,
            data_type=data_type,
            data=old_data,
        )
        StockDataCache.objects.filter(symbol=symbol, data_type=data_type).update(
            updated_at=datetime.now(timezone.utc) - timedelta(minutes=30)
        )
        new_data = {"rsi": 55, "macd": 0.1}
        fetcher = Mock()
        fetcher.get_technical_indicators.return_value = new_data

        result = get_stock_data_cached(symbol, data_type, fetcher)

        fetcher.get_technical_indicators.assert_called_once_with(symbol)
        self.assertEqual(result, new_data)
        cached = StockDataCache.objects.get(symbol=symbol, data_type=data_type)
        self.assertEqual(cached.data, new_data)
