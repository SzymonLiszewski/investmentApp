import logging
import os
import threading
from datetime import date, datetime, timedelta, timezone

import joblib
import pandas as pd
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import StandardScaler

from django.conf import settings

from analytics.services.feature_engineering import (
    FEATURE_COLUMNS,
    TARGET_COLUMN,
    build_feature_frame,
)
from analytics.services.predictions import (
    MIN_HISTORY_POINTS,
    _get_historical_close_series,
)

logger = logging.getLogger(__name__)

INDEX_SYMBOL = "^GSPC"
MODEL_FILENAME = "gspc_regression.joblib"

_cache_lock = threading.Lock()
_cached_payload = None
_cached_key = None


def _model_path() -> str:
    return os.path.join(settings.ML_MODELS_DIR, "regression", MODEL_FILENAME)


def train_and_save_regression_model(history_days: int = 1825) -> dict:
    """Train the shared next-day pct-change regression on index history and
    persist model + scaler as one joblib payload. Returns metadata only."""
    end = date.today()
    start = end - timedelta(days=history_days)
    close = _get_historical_close_series(INDEX_SYMBOL, start.isoformat(), end.isoformat())
    if len(close) < MIN_HISTORY_POINTS:
        raise ValueError(
            f"Not enough {INDEX_SYMBOL} history to train regression: "
            f"{len(close)} points, need at least {MIN_HISTORY_POINTS}"
        )

    frame = build_feature_frame(close).dropna(subset=FEATURE_COLUMNS + [TARGET_COLUMN])
    X = frame[FEATURE_COLUMNS].to_numpy()
    y = frame[TARGET_COLUMN].to_numpy()

    scaler = StandardScaler().fit(X)
    model = LinearRegression().fit(scaler.transform(X), y)

    payload = {
        "model": model,
        "scaler": scaler,
        "feature_columns": FEATURE_COLUMNS,
        "trained_at": datetime.now(timezone.utc).isoformat(),
        "symbol": INDEX_SYMBOL,
        "n_samples": len(y),
    }

    path = _model_path()
    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmp_path = path + ".tmp"
    joblib.dump(payload, tmp_path)
    os.replace(tmp_path, path)
    logger.info(
        "Regression model trained on %s (%d samples) and saved to %s",
        INDEX_SYMBOL, len(y), path,
    )
    return {
        "path": path,
        "symbol": INDEX_SYMBOL,
        "n_samples": len(y),
        "trained_at": payload["trained_at"],
    }


def _load_payload() -> dict:
    """Load the persisted model payload, caching by file mtime so long-lived
    web workers pick up the nightly retrain without a restart. Trains on
    demand when the file does not exist yet (fresh/demo environments)."""
    global _cached_payload, _cached_key
    path = _model_path()
    if not os.path.exists(path):
        logger.info("Regression model missing at %s; training on demand", path)
        train_and_save_regression_model()
    cache_key = (path, os.path.getmtime(path))
    with _cache_lock:
        if _cached_payload is None or _cached_key != cache_key:
            _cached_payload = joblib.load(path)
            _cached_key = cache_key
        return _cached_payload


def predict_with_regression(ticker, start_date, end_date, predicted_days=30) -> dict:
    """Predict a forward price path for any ticker using the shared model.

    Iterative roll-forward: predict next-day pct change from the ticker's own
    features, extend the price series, recompute features, repeat. Dates are
    labeled end_date+1 .. end_date+predicted_days (calendar days, existing
    convention). Returns a flat {iso_date: price} dict.
    """
    payload = _load_payload()
    model = payload["model"]
    scaler = payload["scaler"]
    columns = payload["feature_columns"]

    series = _get_historical_close_series(ticker, start_date, end_date)
    if len(series) < MIN_HISTORY_POINTS:
        raise ValueError(
            f"Not enough price history for {ticker}: "
            f"{len(series)} points, need at least {MIN_HISTORY_POINTS}"
        )

    predicted_prices = []
    for _ in range(predicted_days):
        # Feature rows only (the target column is NaN on the newest row, so a
        # frame-wide dropna would discard exactly the row we predict from).
        features = build_feature_frame(series)[columns].dropna()
        next_pct = float(model.predict(scaler.transform(features.iloc[[-1]].to_numpy()))[0])
        next_price = float(series.iloc[-1]) * (1.0 + next_pct)
        predicted_prices.append(next_price)
        next_index = series.index[-1] + pd.Timedelta(days=1)
        series = pd.concat([series, pd.Series([next_price], index=[next_index])])

    last_date = datetime.strptime(end_date, "%Y-%m-%d")
    return {
        (last_date + timedelta(days=i + 1)).strftime("%Y-%m-%d"): predicted_prices[i]
        for i in range(predicted_days)
    }
