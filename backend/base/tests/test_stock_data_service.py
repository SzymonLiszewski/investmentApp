# Tests for get_stock_data (stock_data_service)
from datetime import datetime, timezone, timedelta
from unittest.mock import Mock

from django.test import TestCase

from base.models import StockDataCache
from base.services.stock_data_service import get_stock_data


class TestGetStockData(TestCase):
    """Tests for get_stock_data."""

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
        result = get_stock_data(symbol, data_type, fetcher)
        self.assertEqual(result, cached_data)
        fetcher.get_basic_stock_info.assert_not_called()

    def test_fetches_and_caches_when_missing(self):
        """When no cache, fetches from fetcher, saves to DB and returns."""
        symbol = "MSFT"
        data_type = "fundamental_analysis"
        fetched = {"pe_ratio": 28.5, "dividend_yield": 0.8}
        fetcher = Mock()
        fetcher.get_fundamental_analysis.return_value = fetched

        result = get_stock_data(symbol, data_type, fetcher)

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

        result = get_stock_data(symbol, data_type, fetcher)

        fetcher.get_technical_indicators.assert_called_once_with(symbol)
        self.assertEqual(result, new_data)
        cached = StockDataCache.objects.get(symbol=symbol, data_type=data_type)
        self.assertEqual(cached.data, new_data)
