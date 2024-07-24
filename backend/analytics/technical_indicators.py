import yfinance as yf
import pandas as pd
import ta

def get_technical_indicators(ticker):
    # downloading data
    stock = yf.Ticker(ticker)
    data = stock.history(period="1y")
    
    # check if downloaded
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