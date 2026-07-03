import numpy as np
import pandas as pd

from django.test import SimpleTestCase

from analytics.services.feature_engineering import (
    FEATURE_COLUMNS,
    TARGET_COLUMN,
    build_feature_frame,
)


def _synthetic_series(n=120):
    index = pd.bdate_range("2025-01-01", periods=n)
    values = 100.0 + np.cumsum(np.sin(np.arange(n) / 5.0)) + np.arange(n) * 0.1
    return pd.Series(values, index=index)


class BuildFeatureFrameTests(SimpleTestCase):
    def test_all_feature_and_target_columns_present(self):
        frame = build_feature_frame(_synthetic_series())
        for column in FEATURE_COLUMNS + [TARGET_COLUMN]:
            self.assertIn(column, frame.columns)

    def test_target_is_next_day_pct_change(self):
        frame = build_feature_frame(_synthetic_series())
        # target on row i equals pct_1d on row i+1
        for i in (60, 80, 100):
            self.assertAlmostEqual(
                frame[TARGET_COLUMN].iloc[i], frame["pct_1d"].iloc[i + 1], places=12
            )

    def test_last_row_target_is_nan_but_features_are_not(self):
        frame = build_feature_frame(_synthetic_series())
        self.assertTrue(np.isnan(frame[TARGET_COLUMN].iloc[-1]))
        self.assertFalse(frame[FEATURE_COLUMNS].iloc[-1].isna().any())

    def test_dropna_leaves_only_finite_rows(self):
        frame = build_feature_frame(_synthetic_series())
        clean = frame.dropna(subset=FEATURE_COLUMNS + [TARGET_COLUMN])
        self.assertGreater(len(clean), 0)
        self.assertLess(len(clean), len(frame))  # warm-up rows and last row dropped
        self.assertTrue(np.isfinite(clean[FEATURE_COLUMNS + [TARGET_COLUMN]].to_numpy()).all())
