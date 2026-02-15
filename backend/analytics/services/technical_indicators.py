from datetime import date, timedelta

import pandas as pd
import ta

from .predictions import _get_historical_close_series


def get_technical_indicators(ticker):
    # fetch historical data via PriceRepository (same as predictions)
    end_date = date.today()
    start_date = end_date - timedelta(days=365)
    close_series = _get_historical_close_series(
        ticker, start_date.isoformat(), end_date.isoformat()
    )
    data = close_series.to_frame("Close")

    # check if we have data
    if data.empty:
        return {"error": "Brak danych dla podanego tickeru"}

    # calculate technical indicators
    data['SMA_50'] = ta.trend.sma_indicator(data['Close'], window=50)
    data['SMA_200'] = ta.trend.sma_indicator(data['Close'], window=200)
    data['RSI'] = ta.momentum.rsi(data['Close'], window=14)
    data['MACD'] = ta.trend.macd(data['Close'])
    data['MACD_Signal'] = ta.trend.macd_signal(data['Close'])
    data['Bollinger_High'] = ta.volatility.bollinger_hband(data['Close'])
    data['Bollinger_Low'] = ta.volatility.bollinger_lband(data['Close'])

    # creating dataframe
    indicators = {
        "Ticker": ticker,
        "Current Price": data['Close'].iloc[-1],
        "SMA_50": data['SMA_50'].iloc[-1],
        "SMA_200": data['SMA_200'].iloc[-1],
        "RSI": data['RSI'].iloc[-1],
        "MACD": data['MACD'].iloc[-1],
        "MACD_Signal": data['MACD_Signal'].iloc[-1],
        "Bollinger_High": data['Bollinger_High'].iloc[-1],
        "Bollinger_Low": data['Bollinger_Low'].iloc[-1]
    }

    return indicators
