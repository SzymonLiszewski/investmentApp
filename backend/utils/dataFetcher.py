import yfinance as yf

def getStockPrice(ticker, start_date, end_date):
    data = yf.download(ticker, start=start_date, end=end_date)
    
    # Przetwórz dane na słownik data:cena zamknięcia
    closing_prices = {}
    for index, row in data.iterrows():
        date_str = index.strftime('%Y-%m-%d')  # Konwersja daty do stringa w formacie 'YYYY-MM-DD'
        closing_price = row['Close']  # Cena zamknięcia
        closing_prices[date_str] = closing_price
    
    return closing_prices

import yfinance as yf

def getFundamentalAnalysis(ticker):
    stock = yf.Ticker(ticker)
    info = stock.info
    
    dividends = stock.dividends
    if not dividends.empty:
        dividends_yearly = dividends.resample('YE').sum()
        dividends_yearly.index = dividends_yearly.index.year.astype(str)
        dividends_yearly = dividends_yearly.to_dict()
    else:
        dividends_yearly = 'N/A'
    
    financials = stock.financials
    if not financials.empty:
        revenue_history = financials.loc['Total Revenue']
        revenue_yearly = revenue_history.resample('YE').sum()
        revenue_yearly.index = revenue_yearly.index.year.astype(str)
        revenue_yearly = revenue_yearly.to_dict()
    else:
        revenue_yearly = 'N/A'
    
    ps_ratio = info.get('priceToSalesTrailing12Months', 'N/A')
    if ps_ratio == 'N/A':
        ps_ratio = info.get('trailingPS', 'N/A')
    if ps_ratio == 'N/A':
        ps_ratio = info.get('forwardPS', 'N/A')
    
    stock_data = {
        'Ticker': ticker,
        'Current Price': info.get('currentPrice', 'N/A'),
        'Market Cap': info.get('marketCap', 'N/A'),
        'P/S Ratio': ps_ratio,
        'P/E Ratio': info.get('forwardPE', 'N/A'),
        'EPS': info.get('trailingEps', 'N/A'),
        'Dividend Yield': info.get('dividendYield', 'N/A'),
        '52 Week High': info.get('fiftyTwoWeekHigh', 'N/A'),
        '52 Week Low': info.get('fiftyTwoWeekLow', 'N/A'),
        'Dividend History': dividends_yearly,
        'Revenue History': revenue_yearly
    }
    return stock_data

def getBasicStockInfo(ticker):
    stock = yf.Ticker(ticker)
    info = stock.info
    
    #current_price = info.get('currentPrice', 'N/A')
    
    hist = stock.history(period='5d')
    current_price = hist['Close'].iloc[-1]
    
    if len(hist) < 2:
        return {
            'Company Name': info.get('shortName', 'N/A'),
            'Current Price': current_price,
            'Price Change': 'N/A',
            'Percent Change': 'N/A'
        }
    
    last_close = hist['Close'].iloc[-1]
    previous_close = hist['Close'].iloc[-2]
    
    price_change = last_close - previous_close
    percent_change = (price_change / previous_close) * 100
    
    basic_info = {
        'Company Name': info.get('shortName', 'N/A'),
        'Current Price': current_price,
        'Price Change': round(price_change, 2),
        'Percent Change': round(percent_change, 2)
    }
    return basic_info