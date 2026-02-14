"""
Unit tests for portfolio_analysis: get_benchmark_series and calculateIndicators.
"""
from datetime import date, timedelta
from unittest.mock import Mock, patch

import numpy as np
import pandas as pd
from django.test import TestCase

from portfolio.services.portfolio_analysis import (
    ANNUALIZATION_DAYS,
    DEFAULT_BENCHMARK_TICKER,
    RISK_FREE_RATE,
    calculateIndicators,
    get_benchmark_series,
    snapshots_to_value_series,
)


def _value_series(dates, values):
    """Build pd.Series with DatetimeIndex from list of dates and values."""
    index = pd.DatetimeIndex([pd.Timestamp(d) for d in dates])
    return pd.Series(values, index=index)


def _price_series(dates, prices):
    """Build pd.Series as returned by fetcher (index = date objects)."""
    return pd.Series(prices, index=pd.Index(dates))


def _mock_snapshot(date_val, total_value, total_invested):
    """Minimal snapshot-like object with .date, .total_value, .total_invested."""
    from types import SimpleNamespace
    return SimpleNamespace(
        date=date_val,
        total_value=total_value,
        total_invested=total_invested,
    )


class SnapshotsToValueSeriesTests(TestCase):
    """Tests for snapshots_to_value_series."""

    def test_returns_two_series_with_datetime_index(self):
        snapshots = [
            _mock_snapshot(date(2025, 1, 1), 1000.0, 900.0),
            _mock_snapshot(date(2025, 1, 2), 1010.0, 900.0),
            _mock_snapshot(date(2025, 1, 3), 1005.0, 950.0),
        ]
        pv_series, inv_series = snapshots_to_value_series(snapshots)
        self.assertIsInstance(pv_series, pd.Series)
        self.assertIsInstance(inv_series, pd.Series)
        self.assertEqual(len(pv_series), 3)
        self.assertEqual(len(inv_series), 3)
        self.assertIsInstance(pv_series.index, pd.DatetimeIndex)
        self.assertIsInstance(inv_series.index, pd.DatetimeIndex)
        self.assertEqual(list(pv_series), [1000.0, 1010.0, 1005.0])
        self.assertEqual(list(inv_series), [900.0, 900.0, 950.0])

    def test_empty_snapshots_returns_empty_series(self):
        pv_series, inv_series = snapshots_to_value_series([])
        self.assertIsInstance(pv_series, pd.Series)
        self.assertIsInstance(inv_series, pd.Series)
        self.assertEqual(len(pv_series), 0)
        self.assertEqual(len(inv_series), 0)

    def test_decimal_snapshot_values_converted_to_float(self):
        from decimal import Decimal
        snapshots = [
            _mock_snapshot(date(2025, 1, 1), Decimal('1000.50'), Decimal('800.25')),
        ]
        pv_series, inv_series = snapshots_to_value_series(snapshots)
        self.assertEqual(list(pv_series), [1000.5])
        self.assertEqual(list(inv_series), [800.25])


class GetBenchmarkSeriesTests(TestCase):
    """Tests for get_benchmark_series (uses StockDataFetcher)."""

    @patch('portfolio.services.portfolio_analysis.get_default_stock_fetcher')
    def test_returns_series_when_fetcher_returns_data(self, mock_get_fetcher):
        dates = [date(2025, 1, 1), date(2025, 1, 2), date(2025, 1, 3)]
        prices = [4000.0, 4010.0, 3995.0]
        mock_fetcher = Mock()
        mock_fetcher.get_historical_prices.return_value = {
            DEFAULT_BENCHMARK_TICKER: _price_series(dates, prices),
        }
        mock_get_fetcher.return_value = mock_fetcher
        result = get_benchmark_series(date(2025, 1, 1), date(2025, 1, 3))
        self.assertIsNotNone(result)
        self.assertIsInstance(result, pd.Series)
        self.assertEqual(len(result), 3)
        mock_fetcher.get_historical_prices.assert_called_once_with(
            [DEFAULT_BENCHMARK_TICKER],
            date(2025, 1, 1),
            date(2025, 1, 3),
        )

    @patch('portfolio.services.portfolio_analysis.get_default_stock_fetcher')
    def test_returns_none_when_fetcher_returns_empty(self, mock_get_fetcher):
        mock_fetcher = Mock()
        mock_fetcher.get_historical_prices.return_value = {}
        mock_get_fetcher.return_value = mock_fetcher
        result = get_benchmark_series(date(2025, 1, 1), date(2025, 1, 3))
        self.assertIsNone(result)

    @patch('portfolio.services.portfolio_analysis.get_default_stock_fetcher')
    def test_returns_none_on_exception(self, mock_get_fetcher):
        mock_fetcher = Mock()
        mock_fetcher.get_historical_prices.side_effect = Exception("network error")
        mock_get_fetcher.return_value = mock_fetcher
        result = get_benchmark_series(date(2025, 1, 1), date(2025, 1, 3))
        self.assertIsNone(result)


class CalculateIndicatorsTests(TestCase):
    """Tests for calculateIndicators (returns-based, annualized)."""

    def test_returns_none_when_portfolio_value_none(self):
        bench = _value_series([date(2025, 1, 1), date(2025, 1, 2)], [100.0, 101.0])
        sharpe, sortino, alpha, _ = calculateIndicators(None, bench)
        self.assertIsNone(sharpe)
        self.assertIsNone(sortino)
        self.assertIsNone(alpha)

    def test_returns_none_when_benchmark_none(self):
        port = _value_series([date(2025, 1, 1), date(2025, 1, 2)], [1000.0, 1010.0])
        sharpe, sortino, alpha, _ = calculateIndicators(port, None)
        self.assertIsNone(sharpe)
        self.assertIsNone(sortino)
        self.assertIsNone(alpha)

    def test_returns_none_when_portfolio_empty(self):
        port = pd.Series(dtype=float)
        bench = _value_series([date(2025, 1, 1), date(2025, 1, 2)], [100.0, 101.0])
        sharpe, sortino, alpha, _ = calculateIndicators(port, bench)
        self.assertIsNone(sharpe)
        self.assertIsNone(sortino)
        self.assertIsNone(alpha)

    def test_returns_none_when_benchmark_empty(self):
        port = _value_series([date(2025, 1, 1), date(2025, 1, 2)], [1000.0, 1010.0])
        bench = pd.Series(dtype=float)
        sharpe, sortino, alpha, _ = calculateIndicators(port, bench)
        self.assertIsNone(sharpe)
        self.assertIsNone(sortino)
        self.assertIsNone(alpha)

    def test_returns_none_when_insufficient_common_dates(self):
        # Only one date in common after pct_change
        port = _value_series([date(2025, 1, 1)], [1000.0])
        bench = _value_series([date(2025, 1, 1)], [100.0])
        sharpe, sortino, alpha, _ = calculateIndicators(port, bench)
        self.assertIsNone(sharpe)
        self.assertIsNone(sortino)
        self.assertIsNone(alpha)

    def test_returns_none_for_only_two_days_after_alignment(self):
        # Two points -> one return; we need at least 2 returns
        port = _value_series([date(2025, 1, 1), date(2025, 1, 2)], [1000.0, 1005.0])
        bench = _value_series([date(2025, 1, 1), date(2025, 1, 2)], [100.0, 101.0])
        sharpe, sortino, alpha, _ = calculateIndicators(port, bench)
        # With 2 value points we get 1 return; len < 2 so we return None, None, None
        self.assertIsNone(sharpe)
        self.assertIsNone(sortino)
        self.assertIsNone(alpha)

    def test_computes_indicators_with_sufficient_returns(self):
        # Four days -> three returns; two negative so downside std is defined
        dates = [date(2025, 1, 1), date(2025, 1, 2), date(2025, 1, 3), date(2025, 1, 4)]
        port = _value_series(dates, [1000.0, 1010.0, 1005.0, 1000.0])   # +1%, -0.5%, -0.5%
        bench = _value_series(dates, [100.0, 101.0, 102.0, 103.0])     # +1%, ~+0.99%, ~+0.98%
        sharpe, sortino, alpha, _ = calculateIndicators(port, bench)
        self.assertIsNotNone(sharpe)
        self.assertIsInstance(sharpe, float)
        self.assertIsNotNone(alpha)
        self.assertIsInstance(alpha, float)
        # Portfolio has negative returns so Sortino should be computed (need 2+ for std)
        self.assertIsNotNone(sortino)
        self.assertIsInstance(sortino, float)

    def test_sortino_none_when_no_negative_returns(self):
        # Portfolio only goes up -> no downside returns
        dates = [date(2025, 1, 1), date(2025, 1, 2), date(2025, 1, 3), date(2025, 1, 4)]
        port = _value_series(dates, [1000.0, 1010.0, 1020.0, 1030.0])
        bench = _value_series(dates, [100.0, 101.0, 102.0, 103.0])
        sharpe, sortino, alpha, _ = calculateIndicators(port, bench)
        self.assertIsNotNone(sharpe)
        self.assertIsNone(sortino)
        self.assertIsNotNone(alpha)

    def test_sharpe_none_when_zero_volatility(self):
        # Constant portfolio value -> zero std
        dates = [date(2025, 1, 1), date(2025, 1, 2), date(2025, 1, 3)]
        port = _value_series(dates, [1000.0, 1000.0, 1000.0])
        bench = _value_series(dates, [100.0, 101.0, 102.0])
        sharpe, sortino, alpha, _ = calculateIndicators(port, bench)
        self.assertIsNone(sharpe)
        self.assertIsNone(sortino)
        self.assertIsNotNone(alpha)  # alpha can still be computed

    def test_uses_returns_not_levels(self):
        # If we used levels, mean would be ~1000 and std would be large.
        # With returns: mean return ~0.005, std small -> Sharpe positive and finite
        dates = [date(2025, 1, 1), date(2025, 1, 2), date(2025, 1, 3), date(2025, 1, 4)]
        port = _value_series(dates, [1000.0, 1005.0, 1002.0, 1010.0])
        bench = _value_series(dates, [100.0, 100.5, 100.2, 101.0])
        sharpe, sortino, alpha, _ = calculateIndicators(port, bench)
        self.assertIsNotNone(sharpe)
        # Sharpe should be in a reasonable range (not huge from level-based mistake)
        self.assertLess(abs(sharpe), 100.0)
        self.assertIsNotNone(alpha)
