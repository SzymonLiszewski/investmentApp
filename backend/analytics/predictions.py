import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.preprocessing import MinMaxScaler
from sklearn.linear_model import LinearRegression
import yfinance as yf
from datetime import timedelta
from datetime import datetime


def linear_regression_predict(ticker, start_date, end_date, predicted_days):
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
    return future_predictions


#* prepare time series for regression
def create_dataset(data, time_step=1):
    X, y = [], []
    for i in range(len(data) - time_step):
        X.append(data[i:(i + time_step), 0])
        y.append(data[i + time_step, 0])
    return np.array(X), np.array(y)


#* use example
'''ticker = "^GSPC"  
start_date = "2020-01-01"
end_date = "2023-12-31"

#* generating future dates
format_string = "%Y-%m-%d"
last_date = datetime.strptime(end_date, format_string)
future_dates = [last_date + timedelta(days=i) for i in range(1, 300 + 1)]

future_predictions = linear_regression_predict(ticker,start_date,end_date,300)

#* plotting results
plt.figure(figsize=(10, 6))
plt.plot(future_dates, future_predictions, label='Przewidywane ceny (przyszłość)')
plt.legend()
plt.show()'''
