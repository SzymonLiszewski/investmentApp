import os
import pickle
from datetime import datetime, timedelta

import numpy as np
import pandas as pd
from statsmodels.tsa.statespace.sarimax import SARIMAX

from django.conf import settings

from base.infrastructure.db import PriceRepository
from base.services import get_default_stock_fetcher

# SMA-50 is the longest feature lookback; SARIMA needs a comparable minimum to fit.
MIN_HISTORY_POINTS = 60


def _get_historical_close_series(symbol: str, start_date: str, end_date: str) -> pd.Series:
    """Fetch historical close prices from PriceRepository and return as pandas Series."""
    start = datetime.strptime(start_date, "%Y-%m-%d").date()
    end = datetime.strptime(end_date, "%Y-%m-%d").date()
    repo = PriceRepository()
    fetcher = get_default_stock_fetcher()
    prices = repo.get_price_history(symbol, start, end, fetcher)
    if not prices:
        return pd.Series(dtype=float)
    sorted_dates = sorted(prices.keys())
    return pd.Series(
        {d: float(prices[d]) for d in sorted_dates},
        index=pd.DatetimeIndex(sorted_dates),
    ).sort_index()


def load_lstm_model(ticker, start_date, end_date, predicted_days=30):
    if not getattr(settings, 'ENABLE_ML_FUNCTIONS', False):
        raise ValueError(
            'LSTM predictions are disabled. Set ENABLE_ML_FUNCTIONS=true to enable.'
        )
    from tensorflow import keras

    close_prices = _get_historical_close_series(ticker, start_date, end_date)

    # __file__ is analytics/services/predictions.py -> parent = analytics
    _analytics_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    scaler_path = os.path.join(_analytics_dir, 'saved_models', 'GSPC', 'scaler.pkl')
    with open(scaler_path, 'rb') as scaler_file:
        scaler = pickle.load(scaler_file)

    scaled_data = scaler.transform(close_prices.values.reshape(-1, 1))
    model_path = os.path.join(_analytics_dir, 'saved_models', 'GSPC', 'my_model.h5')
    model = keras.models.load_model(model_path)

    # Przewidywanie na przyszłość
    look_back = 100
    future_days = predicted_days
    last_sequence = scaled_data[-look_back:]
    predictions = []

    for _ in range(future_days):
        pred = model.predict(last_sequence.reshape(1, look_back, 1))
        predictions.append(pred[0, 0])
        last_sequence = np.append(last_sequence[1:], pred, axis=0)

    # Denormalizacja przewidywanych danych
    predictions = scaler.inverse_transform(np.array(predictions).reshape(-1, 1))

    # Tworzenie DataFrame dla przewidywanych danych
    future_dates = pd.date_range(start=close_prices.index[-1] + pd.Timedelta(days=1), periods=future_days)
    predicted_df = pd.DataFrame(predictions, columns=['Predicted_Close'], index=future_dates)
    return predicted_df


def sarima_forecast(ticker, start_date, end_date, predicted_days=30):
    """Fit SARIMAX on close prices and return the full forecast path.

    Forecast steps are the next observations on the business-day history index,
    labeled with consecutive calendar days after end_date (existing convention).

    Returns a list of dicts:
    [{"date": "YYYY-MM-DD", "predicted": float, "lower": float, "upper": float}, ...]
    """
    close_prices = _get_historical_close_series(ticker, start_date, end_date)
    if len(close_prices) < MIN_HISTORY_POINTS:
        raise ValueError(
            f"Not enough price history for {ticker}: "
            f"{len(close_prices)} points, need at least {MIN_HISTORY_POINTS}"
        )

    model = SARIMAX(close_prices, order=(1, 1, 1), seasonal_order=(1, 1, 1, 12))
    model_fit = model.fit(disp=False)

    forecast = model_fit.get_forecast(steps=predicted_days)
    # conf_int() column names depend on the series name -> access positionally.
    forecast_ci = forecast.conf_int()
    forecast_values = forecast.predicted_mean

    last_date = datetime.strptime(end_date, "%Y-%m-%d")
    return [
        {
            "date": (last_date + timedelta(days=i + 1)).strftime("%Y-%m-%d"),
            "predicted": float(forecast_values.iloc[i]),
            "lower": float(forecast_ci.iloc[i, 0]),
            "upper": float(forecast_ci.iloc[i, 1]),
        }
        for i in range(predicted_days)
    ]
