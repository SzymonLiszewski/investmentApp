import os
import shutil
import tempfile

import joblib

from django.test import TestCase, override_settings

from analytics.services import regression_model
from analytics.services.regression_model import (
    predict_with_regression,
    train_and_save_regression_model,
)


class RegressionModelTests(TestCase):
    def setUp(self):
        self.tmp_dir = tempfile.mkdtemp(prefix="test_reg_models_")
        self.addCleanup(shutil.rmtree, self.tmp_dir, ignore_errors=True)
        self.settings_override = override_settings(
            ML_MODELS_DIR=self.tmp_dir, USE_MOCK_DATA_FETCHER=True
        )
        self.settings_override.enable()
        self.addCleanup(self.settings_override.disable)
        # reset the module-level payload cache between tests
        regression_model._cached_payload = None
        regression_model._cached_key = None

    def test_train_persists_payload_with_expected_keys(self):
        meta = train_and_save_regression_model(history_days=730)

        path = regression_model._model_path()
        self.assertTrue(os.path.exists(path))
        payload = joblib.load(path)
        for key in ("model", "scaler", "feature_columns", "trained_at", "symbol", "n_samples"):
            self.assertIn(key, payload)
        self.assertEqual(payload["symbol"], "^GSPC")
        self.assertGreater(meta["n_samples"], 100)

    def test_predict_returns_price_path_with_expected_dates(self):
        train_and_save_regression_model(history_days=730)

        result = predict_with_regression("AAPL", "2025-01-01", "2025-12-31", predicted_days=10)

        self.assertEqual(len(result), 10)
        self.assertIn("2026-01-01", result)
        self.assertIn("2026-01-10", result)
        for price in result.values():
            self.assertGreater(price, 0.0)

    def test_predict_trains_on_demand_when_model_file_missing(self):
        path = regression_model._model_path()
        self.assertFalse(os.path.exists(path))

        result = predict_with_regression("MSFT", "2025-01-01", "2025-12-31", predicted_days=5)

        self.assertTrue(os.path.exists(path))
        self.assertEqual(len(result), 5)

    def test_predict_rejects_short_history(self):
        train_and_save_regression_model(history_days=730)
        with self.assertRaises(ValueError):
            predict_with_regression("AAPL", "2025-12-01", "2025-12-31", predicted_days=5)
