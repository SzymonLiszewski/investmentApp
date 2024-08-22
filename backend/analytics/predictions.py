import numpy as np
import pandas as pd
from sklearn.preprocessing import MinMaxScaler
from sklearn.linear_model import LinearRegression
import yfinance as yf
from datetime import timedelta
from datetime import datetime


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


#* prepare time series for regression
def create_dataset(data, time_step=1):
    X, y = [], []
    for i in range(len(data) - time_step):
        X.append(data[i:(i + time_step), 0])
        y.append(data[i + time_step, 0])
    return np.array(X), np.array(y)
