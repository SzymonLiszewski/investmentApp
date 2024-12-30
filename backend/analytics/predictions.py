import numpy as np
import pandas as pd
from sklearn.preprocessing import MinMaxScaler
from sklearn.linear_model import LinearRegression
import yfinance as yf
from datetime import timedelta
from datetime import datetime
import pickle
from tensorflow import keras
import os
from statsmodels.tsa.statespace.sarimax import SARIMAX


def linear_regression_predict(ticker, start_date, end_date, predicted_days=30):
    data = yf.download(ticker, start=start_date, end=end_date)
    data = data['Close']

    #* standarization
    scaler = MinMaxScaler(feature_range=(0, 1))
    scaled_data = scaler.fit_transform(data.values.reshape(-1, 1))

    time_step = 100
    X_train, y_train = create_dataset(scaled_data[:len(data)], time_step)

    #* build linear regression model
    linear_model = LinearRegression()

    #* model training
    linear_model.fit(X_train, y_train)

    #* Prediction
    future_days = predicted_days  
    last_sequence = scaled_data[-time_step:]

    future_predictions = []
    for _ in range(future_days):
        next_pred = linear_model.predict(last_sequence.reshape(1, -1))
        future_predictions.append(next_pred[0])
        next_pred = next_pred.reshape(-1, 1)  # Ensure next_pred has the same shape as last_sequence
        last_sequence = np.append(last_sequence[1:], next_pred, axis=0)

    future_predictions = scaler.inverse_transform(np.array(future_predictions).reshape(-1, 1))
    
    format_string = "%Y-%m-%d"
    last_date = datetime.strptime(end_date, format_string)
    future_dates = [(last_date + timedelta(days=i)).strftime(format_string) for i in range(1, predicted_days + 1)]
    data_dict = {}

    for i in range(len(future_dates)):
        data_dict[future_dates[i]] = future_predictions[i][0]
    return {list(data_dict.keys())[-1]:list(data_dict.values())[-1]}

def load_lstm_model(ticker, start_date, end_date, predicted_days=30):
    data = yf.download(ticker, start=start_date, end=end_date)
    close_prices = data['Close']

    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    scaler_path = os.path.join(BASE_DIR, 'analytics','saved_models','GSPC', 'scaler.pkl')
    with open(scaler_path, 'rb') as scaler_file:
        scaler = pickle.load(scaler_file)


    scaled_data = scaler.transform(close_prices.values.reshape(-1, 1))
    model_path = os.path.join(BASE_DIR, 'analytics','saved_models','GSPC', 'my_model.h5')
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

def sarima(ticker, start_date, end_date, predicted_days=30):
    data = yf.download(ticker, start=start_date, end=end_date)
    close_prices = data['Close']

    #* Preparing SARIMA model
    model = SARIMAX(close_prices, order=(1, 1, 1), seasonal_order=(1, 1, 1, 12))
    model_fit = model.fit(disp=False)

    #* Prediction
    future_steps = predicted_days
    future_predictions = model_fit.get_forecast(steps=future_steps)
    forecast_ci = future_predictions.conf_int()
    forecast_values = future_predictions.predicted_mean

    format_string = "%Y-%m-%d"
    last_date = datetime.strptime(end_date, format_string)
    future_dates = [(last_date + timedelta(days=i)).strftime(format_string) for i in range(1, predicted_days + 1)]

    # Tworzenie słownika dat i prognozowanych cen
    data_dict = {date: price for date, price in zip(future_dates[-2:-1], forecast_values[-2:-1])}
    print(data_dict)

    return data_dict


#* prepare time series for regression
def create_dataset(data, time_step=1):
    X, y = [], []
    for i in range(len(data) - time_step):
        X.append(data[i:(i + time_step), 0])
        y.append(data[i + time_step, 0])
    return np.array(X), np.array(y)
