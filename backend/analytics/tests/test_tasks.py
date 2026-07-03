import os
import shutil
import tempfile
from unittest.mock import patch

from django.test import TestCase, override_settings

from analytics.models import SarimaForecast
from analytics.services import regression_model
from analytics.tasks import train_regression_model_task, train_sarima_forecasts


@override_settings(USE_MOCK_DATA_FETCHER=True)
class CeleryTaskTests(TestCase):
    """settings_test sets CELERY_TASK_ALWAYS_EAGER, so .delay() runs in-process."""

    def test_sarima_task_stores_forecasts(self):
        with patch(
            "analytics.services.forecast_service.get_top_stock_symbols",
            return_value=["AAPL"],
        ):
            train_sarima_forecasts.delay()

        self.assertEqual(SarimaForecast.objects.filter(symbol="AAPL").count(), 30)

    def test_regression_task_persists_model_file(self):
        tmp_dir = tempfile.mkdtemp(prefix="test_task_models_")
        self.addCleanup(shutil.rmtree, tmp_dir, ignore_errors=True)
        regression_model._cached_payload = None
        regression_model._cached_key = None

        with override_settings(ML_MODELS_DIR=tmp_dir):
            train_regression_model_task.delay()
            self.assertTrue(os.path.exists(regression_model._model_path()))
