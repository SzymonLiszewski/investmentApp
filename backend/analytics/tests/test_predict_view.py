from datetime import date, timedelta
from decimal import Decimal
from unittest.mock import patch

from django.test import TestCase, override_settings

from analytics.models import SarimaForecast


@override_settings(USE_MOCK_DATA_FETCHER=True)
class PredictViewTests(TestCase):
    url = "/api/analytics/predict/AAPL/"

    def _seed_stored_forecast(self, symbol="AAPL", days=30):
        start = date.today() + timedelta(days=1)
        SarimaForecast.objects.bulk_create(
            SarimaForecast(
                symbol=symbol,
                forecast_date=start + timedelta(days=i),
                predicted_price=Decimal("100.0") + i,
                lower_bound=Decimal("99.0") + i,
                upper_bound=Decimal("101.0") + i,
            )
            for i in range(days)
        )

    def test_invalid_model_returns_400(self):
        response = self.client.get(self.url, {"model": "bogus"})
        self.assertEqual(response.status_code, 400)

    def test_sarima_serves_precomputed_forecast_without_fitting(self):
        self._seed_stored_forecast()
        with patch("analytics.views.sarima_forecast") as mock_fit:
            response = self.client.get(self.url, {"model": "sarima"})

        self.assertEqual(response.status_code, 200)
        mock_fit.assert_not_called()
        body = response.json()
        self.assertEqual(body["source"], "precomputed")
        self.assertEqual(len(body["forecast"]), 30)
        self.assertGreater(len(body["history"]), 0)
        first = body["forecast"][0]
        for key in ("date", "predicted", "lower", "upper"):
            self.assertIn(key, first)

    def test_sarima_falls_back_to_on_demand_fit(self):
        fake = [{"date": "2026-07-04", "predicted": 1.0, "lower": 0.9, "upper": 1.1}]
        with patch("analytics.views.sarima_forecast", return_value=fake) as mock_fit:
            response = self.client.get(
                "/api/analytics/predict/ZZZZ/", {"model": "sarima"}
            )

        self.assertEqual(response.status_code, 200)
        mock_fit.assert_called_once()
        body = response.json()
        self.assertEqual(body["source"], "on_demand")
        self.assertEqual(body["forecast"], fake)

    def test_default_regression_returns_flat_dict(self):
        prediction = {"2026-07-04": 123.0, "2026-07-05": 124.0}
        with patch("analytics.views.predict_with_regression", return_value=prediction):
            response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        body = response.json()
        # flat {date: price} mapping: history merged with prediction, no nesting
        self.assertEqual(body["2026-07-04"], 123.0)
        self.assertNotIn("history", body)
        self.assertNotIn("forecast", body)
        self.assertTrue(all(isinstance(v, float) for v in body.values()))

    def test_regression_short_history_returns_400(self):
        with patch(
            "analytics.views.predict_with_regression",
            side_effect=ValueError("Not enough price history"),
        ):
            response = self.client.get(self.url)
        self.assertEqual(response.status_code, 400)
