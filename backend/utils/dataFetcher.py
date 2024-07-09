import yfinance as yf

def getStockPrice(ticker, start_date, end_date):
    data = yf.download(ticker, start=start_date ,end=end_date)
    price = data['Close']
    return price

def getFundamentalAnalysis(ticker):
    stock = yf.Ticker(ticker)
    info = stock.info
   
    dividends = stock.dividends
    if not dividends.empty:
        dividends_yearly = dividends.resample('YE').sum().to_dict()
    else:
        dividends_yearly = 'N/A'
    
    
    financials = stock.financials
    if not financials.empty:
        revenue_history = financials.loc['Total Revenue']
        revenue_yearly = revenue_history.resample('YE').sum().to_dict()
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