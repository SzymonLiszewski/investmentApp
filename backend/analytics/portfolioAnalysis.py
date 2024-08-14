import yfinance as yf
import pandas as pd
import numpy as np

def calculateProfit(portfolio):
    #* downloading historical data
    if True:
        return None, None
    tickers = [stock.product.ticker for stock in portfolio]
    tickers.append('XD')
    #* finding first transaction date
    earliest_purchase_date = min(pd.to_datetime(stock.date) for stock in portfolio)
    data = yf.download(tickers, start='2023-05-06', end='2024-05-06')['Adj Close']

    portfolio_value = pd.Series(index=data.index, dtype=np.float64)
    initial_value = 0

    #* sum of money spend every day
    money_spent = pd.Series(0, index=data.index, dtype=np.float64)

    for stock in portfolio:
        ticker = stock.product.ticker
        quantity = stock.quantity
        purchase_date = pd.to_datetime(stock.date)
        
        #* getting price (given by user or get via yfinance)
        if stock.price>0:
            purchase_price = stock.price
        else:
            purchase_price = data[ticker].loc[purchase_date]

        #* update spent money
        money_spent.loc[money_spent.index >= purchase_date] += purchase_price * quantity

        #* calculating purchase price
        initial_value = data[ticker].copy()
        initial_value.loc[initial_value.index < purchase_date] = 0
        initial_value.loc[initial_value.index >= purchase_date] = purchase_price
        
        #* stock value over time
        stock_data = data[ticker].copy()
        stock_data.loc[stock_data.index < purchase_date] = 0
        
        position_value = (stock_data - initial_value) * quantity 
        portfolio_value = portfolio_value.add(position_value, fill_value=0)

    #* downloading benchmark data (s&P500)
    benchmark_ticker = '^GSPC'
    #! change end date
    #todo: change end date, and try to change start date to earliest purchase
    benchmark_data = yf.download(benchmark_ticker, start='2023-05-06', end='2024-05-06')['Adj Close']

    #* simulating investment in benchmark (purchasing in same days and same value as real investments)
    previous_value = 0
    benchmark_quantity = pd.Series(0, index=data.index, dtype=np.float64)
    quantity = 0
    for current_date, current_value in money_spent.items():
        sum_money = 0
        if current_value != previous_value:
            if current_date in benchmark_data.index:
                price = benchmark_data.loc[current_date]
                money = current_value - previous_value
                quantity += money / price
                sum_money+=current_value
            previous_value = current_value
        benchmark_quantity.loc[current_date] = quantity
        
    benchmark_value = benchmark_quantity * benchmark_data
    
    benchmark_value = benchmark_value - money_spent
    return portfolio_value, benchmark_value

def calculateIndicators(portfolio_value, benchmark_data):
    if portfolio_value==None or benchmark_data ==None:
        return None, None, None
    risk_free_rate = 0.01  #* assuming rate of return 1%
    
    portfolio_returns = portfolio_value
    benchmark_returns = benchmark_data

    #* calculating sharpe ratio
    sharpe_ratio = (portfolio_returns.mean() - risk_free_rate / 252) / portfolio_returns.std()

    #* caluclating Sortino ratio
    downside_returns = portfolio_returns[portfolio_returns < 0]
    sortino_ratio = (portfolio_returns.mean() - risk_free_rate / 252) / downside_returns.std()
    if len(downside_returns) == 0:
        sortino_ratio = 5

    #* calculating alpha (CAPM)
    beta, alpha = np.polyfit(benchmark_returns, portfolio_returns, 1)
    alpha = alpha * 252  #* yearly alpha rate
    return sharpe_ratio, sortino_ratio, alpha