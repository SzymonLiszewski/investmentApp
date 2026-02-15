# Tests for base app
from datetime import date
from decimal import Decimal
from unittest.mock import Mock

import pandas as pd

from django.test import TestCase

from base.infrastructure.interfaces.market_data_fetcher import StockDataFetcher
from base.infrastructure.db.price_repository import PriceRepository


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
