from datetime import date, timedelta
from decimal import Decimal
from unittest.mock import patch

from django.test import TestCase

from analytics.models import SarimaForecast
from analytics.services.forecast_service import (
    generate_sarima_forecast_for_symbol,
    run_sarima_batch,
)


def _fake_forecast(days=30, base=100.0):
    start = date(2026, 7, 4)
    return [
        {
            "date": (start + timedelta(days=i)).isoformat(),
            "predicted": base + i,
            "lower": base + i - 1.0,
            "upper": base + i + 1.0,
        }
        for i in range(days)
    ]


class GenerateSarimaForecastTests(TestCase):
    @patch("analytics.services.forecast_service.sarima_forecast")
    def test_writes_forecast_rows(self, mock_sarima):
        mock_sarima.return_value = _fake_forecast()

        count = generate_sarima_forecast_for_symbol("AAPL")

        self.assertEqual(count, 30)
        rows = list(SarimaForecast.objects.filter(symbol="AAPL").order_by("forecast_date"))
        self.assertEqual(len(rows), 30)
        self.assertEqual(rows[0].forecast_date, date(2026, 7, 4))
        self.assertEqual(rows[0].predicted_price, Decimal("100.0"))
        self.assertEqual(rows[0].lower_bound, Decimal("99.0"))
        self.assertEqual(rows[0].upper_bound, Decimal("101.0"))

    @patch("analytics.services.forecast_service.sarima_forecast")
    def test_rerun_replaces_rows(self, mock_sarima):
        mock_sarima.return_value = _fake_forecast(base=100.0)
        generate_sarima_forecast_for_symbol("AAPL")

        mock_sarima.return_value = _fake_forecast(base=200.0)
        generate_sarima_forecast_for_symbol("AAPL")

        rows = list(SarimaForecast.objects.filter(symbol="AAPL").order_by("forecast_date"))
        self.assertEqual(len(rows), 30)
        self.assertEqual(rows[0].predicted_price, Decimal("200.0"))


class RunSarimaBatchTests(TestCase):
    @patch("analytics.services.forecast_service.sarima_forecast")
    def test_one_failing_symbol_does_not_abort_batch(self, mock_sarima):
        def side_effect(symbol, *args, **kwargs):
            if symbol == "BAD":
                raise ValueError("Not enough price history")
            return _fake_forecast()

        mock_sarima.side_effect = side_effect

        result = run_sarima_batch(["GOOD", "BAD", "ALSOGOOD"])

        self.assertEqual(result["succeeded"], ["GOOD", "ALSOGOOD"])
        self.assertIn("BAD", result["failed"])
        self.assertEqual(SarimaForecast.objects.filter(symbol="GOOD").count(), 30)
        self.assertEqual(SarimaForecast.objects.filter(symbol="BAD").count(), 0)

    @patch("analytics.services.forecast_service.sarima_forecast")
    def test_defaults_to_top_stock_symbols(self, mock_sarima):
        mock_sarima.return_value = _fake_forecast()
        with patch(
            "analytics.services.forecast_service.get_top_stock_symbols",
            return_value=["AAPL", "MSFT"],
        ):
            result = run_sarima_batch()
        self.assertEqual(result["succeeded"], ["AAPL", "MSFT"])
