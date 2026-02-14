"""
Legacy / on-demand portfolio profit calculation.

WARNING: This module is kept for backward-compatibility and potential future
on-demand analysis with custom time intervals.  For the daily portfolio value
chart, use portfolio.services.portfolio_snapshots.PortfolioSnapshotService
and the /portfolio/value-history/ endpoint instead.
"""
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import date, datetime, timedelta
from typing import Iterable, Optional, Tuple, TYPE_CHECKING

import time

from base.services import get_default_stock_fetcher

if TYPE_CHECKING:
    from base.infrastructure.interfaces.market_data_fetcher import StockDataFetcher

DEFAULT_BENCHMARK_TICKER = '^GSPC'
ANNUALIZATION_DAYS = 252
RISK_FREE_RATE = 0.01  # 1% per year


def _to_date(d):
    """Convert to date for fetcher API (accepts date or datetime or YYYY-MM-DD string)."""
    if isinstance(d, date) and not isinstance(d, datetime):
        return d
    if isinstance(d, datetime):
        return d.date()
    return datetime.strptime(str(d)[:10], '%Y-%m-%d').date()


def get_benchmark_series(
    start_date,
    end_date,
    ticker: str = DEFAULT_BENCHMARK_TICKER,
    stock_data_fetcher: Optional['StockDataFetcher'] = None,
) -> Optional[pd.Series]:
    """
    Fetch benchmark (e.g. S&P 500) price series for the given date range.

    Uses StockDataFetcher (default implementation if not provided). Returns a
    pandas Series with DatetimeIndex and close prices, or None if fetch fails
    or returns empty.
    """
    fetcher = stock_data_fetcher or get_default_stock_fetcher()
    start = _to_date(start_date)
    end = _to_date(end_date)
    try:
        result = fetcher.get_historical_prices(symbols=[ticker], start_date=start, end_date=end)
    except Exception:
        return None
    if not result or ticker not in result:
        return None
    series = result[ticker].dropna()
    if series.empty:
        return None
    series.index = pd.DatetimeIndex(series.index)
    return series


def calculateProfit(portfolio, userID, passwd):
    """
    Legacy function - computes short-window (30-day) profit using live
    yfinance data.  Retained for on-demand / custom-interval analysis.
    For daily value history prefer PortfolioSnapshotService.
    """
    now = datetime.now()- timedelta(days=1)
    one_month_ago = now - timedelta(days=30)
    #* downloading historical data
    if portfolio==None:
        return None, None
    tickers = [stock.product.symbol for stock in portfolio if stock.product.symbol]

    #* split between available (yfinance) and unavailable tickers; only yfinance is used
    available_tickers = []
    for ticker in tickers:
        if check_ticker_availability(ticker):
            available_tickers.append(ticker)

    if not available_tickers:
        return None, None

    #* filter portfolio to stocks with available data only
    portfolio = [s for s in portfolio if s.product.symbol in available_tickers]
    tickers = available_tickers

    #* finding first transaction date
    earliest_purchase_date = min(pd.to_datetime(stock.date) for stock in portfolio)

    data = yf.download(available_tickers, start=str(one_month_ago.strftime('%Y-%m-%d')), end=str(now.strftime('%Y-%m-%d')))['Adj Close']
    if isinstance(data, pd.Series):
        data = pd.DataFrame({available_tickers[0]: data})

    portfolio_value = pd.Series(index=data.index, dtype=np.float64)
    initial_value = 0

    #* sum of money spend every day
    money_spent = pd.Series(0, index=data.index, dtype=np.float64)

    for stock in portfolio:
        ticker = stock.product.symbol
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
    
    benchmark_data = yf.download(benchmark_ticker, start=str(one_month_ago.strftime('%Y-%m-%d')), end=str(now.strftime('%Y-%m-%d')))['Adj Close']

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
    #*create full dates dataframe
    full_index = pd.date_range(start=str(one_month_ago.strftime('%Y-%m-%d')), 
                           end=str(now.strftime('%Y-%m-%d')), freq='D')
    #* reindexing dataframes
    portfolio_value = portfolio_value.reindex(full_index)
    benchmark_value = benchmark_value.reindex(full_index)

    #*fill missing values using forward fill
    portfolio_value = portfolio_value.ffill()
    benchmark_value = benchmark_value.ffill()
    return portfolio_value, benchmark_value


def _simulate_benchmark_value(
    cash_flow_series: pd.Series,
    benchmark_price_series: pd.Series,
) -> pd.Series:
    """
    Simulate benchmark portfolio value over time with the same cash flows.

    On each day, CF_t is invested in (or withdrawn from) the benchmark at that day's
    price. Returns a Series of portfolio value (units * price) aligned to
    cash_flow_series index.
    """
    idx = cash_flow_series.index
    bench = benchmark_price_series.reindex(idx).ffill()
    # Division by 0 or NaN in price can result in inf/-inf, so we replace them with zero to avoid distorting the number of units.
    units = (cash_flow_series.fillna(0) / bench).replace([np.inf, -np.inf], 0).fillna(0).cumsum()
    return units * bench


def snapshots_to_value_series(
    snapshots: Iterable,
) -> Tuple[pd.Series, pd.Series]:
    """
    Build portfolio value and total invested pandas Series from snapshot iterable.
    Each snapshot must have .date, .total_value, .total_invested.
    Returns (portfolio_value_series, total_invested_series) with DatetimeIndex.
    """
    snapshots = list(snapshots)
    if not snapshots:
        return pd.Series(dtype=float), pd.Series(dtype=float)
    index = pd.DatetimeIndex([s.date for s in snapshots])
    portfolio_value_series = pd.Series(
        index=index,
        data=[float(s.total_value) for s in snapshots],
    )
    total_invested_series = pd.Series(
        index=index,
        data=[float(s.total_invested) for s in snapshots],
    )
    return portfolio_value_series, total_invested_series


def calculateIndicators(
    portfolio_value: pd.Series,
    benchmark_data: pd.Series,
    total_invested_series: Optional[pd.Series] = None,
):
    """
    Compute Sharpe, Sortino and Alpha from portfolio and benchmark series.

    When total_invested_series is provided:
    - Returns are cash-flow adjusted: r_t = (V_t - V_{t-1} - CF_t) / V_{t-1},
      so deposits/withdrawals do not distort Sharpe and Sortino.
    - Alpha = (portfolio_profit - benchmark_profit) / total_invested, i.e. excess
      return vs benchmark over the period (point-in-time comparison).

    When total_invested_series is not provided, falls back to pct_change returns
    and CAPM alpha (legacy). Annualization uses 252 trading days.
    """
    if portfolio_value is None or benchmark_data is None:
        return None, None, None, None
    if not isinstance(portfolio_value, pd.Series) or not isinstance(benchmark_data, pd.Series):
        return None, None, None, None
    if portfolio_value.empty or benchmark_data.empty:
        return None, None, None, None

    use_cf_adjusted = (
        total_invested_series is not None
        and isinstance(total_invested_series, pd.Series)
        and not total_invested_series.empty
        and len(total_invested_series) == len(portfolio_value)
        and total_invested_series.index.equals(portfolio_value.index)
    )

    if use_cf_adjusted:
        # Cash flow = change in total_invested; first day CF = total_invested on that day
        cash_flow = total_invested_series.diff()
        cash_flow = cash_flow.fillna(total_invested_series.iloc[0])
        V_prev = portfolio_value.shift(1)
        # r_t = (V_t - V_{t-1} - CF_t) / V_{t-1}; avoid div by zero
        raw_returns = (portfolio_value - V_prev - cash_flow) / V_prev.replace(0, np.nan)
        portfolio_returns = raw_returns.dropna()
        portfolio_returns = portfolio_returns[np.isfinite(portfolio_returns)]
    else:
        portfolio_returns = portfolio_value.pct_change().dropna()

    if len(portfolio_returns) < 2:
        return None, None, None, None

    r_f_daily = RISK_FREE_RATE / ANNUALIZATION_DAYS
    mean_ret = portfolio_returns.mean()
    std_ret = portfolio_returns.std()

    # Sharpe (annualized)
    if std_ret == 0 or np.isnan(std_ret):
        sharpe_ratio = None
    else:
        sharpe_ratio = float((mean_ret - r_f_daily) / std_ret * np.sqrt(ANNUALIZATION_DAYS))

    # Sortino (annualized; downside deviation)
    downside_returns = portfolio_returns[portfolio_returns < 0]
    if downside_returns.empty or downside_returns.std() == 0 or np.isnan(downside_returns.std()):
        sortino_ratio = None
    else:
        sortino_ratio = float(
            (mean_ret - r_f_daily) / downside_returns.std() * np.sqrt(ANNUALIZATION_DAYS)
        )

    # Alpha and benchmark profit (same units as total_invested_series, e.g. USD)
    benchmark_profit = None
    if use_cf_adjusted:
        # Point-in-time: excess profit vs benchmark (same cash flows)
        total_inv = float(total_invested_series.iloc[-1])
        portfolio_profit = float(portfolio_value.iloc[-1]) - total_inv
        cash_flow_series = total_invested_series.diff().fillna(total_invested_series.iloc[0])
        bench_prices = benchmark_data.reindex(portfolio_value.index).ffill()
        benchmark_value_series = _simulate_benchmark_value(cash_flow_series, bench_prices)
        bench_val_last = benchmark_value_series.iloc[-1]
        if pd.isna(bench_val_last) or total_inv <= 0:
            alpha = None
        else:
            benchmark_profit = float(bench_val_last) - total_inv
            alpha = (portfolio_profit - benchmark_profit) / total_inv  # excess return ratio
            alpha = float(alpha)
    else:
        benchmark_returns = benchmark_data.pct_change().dropna()
        common_idx = portfolio_returns.index.intersection(benchmark_returns.index)
        if len(common_idx) < 2:
            alpha = None
        else:
            pr = portfolio_returns.reindex(common_idx).dropna()
            br = benchmark_returns.reindex(common_idx).dropna()
            valid = pr.notna() & br.notna()
            pr, br = pr[valid], br[valid]
            if len(pr) < 2:
                alpha = None
            else:
                try:
                    _, alpha_daily = np.polyfit(br.values, pr.values, 1)
                    alpha = float(alpha_daily * ANNUALIZATION_DAYS)
                except (np.linalg.LinAlgError, ValueError, TypeError):
                    alpha = None
    return sharpe_ratio, sortino_ratio, alpha, benchmark_profit

def check_ticker_availability(ticker):
    try:
        data = yf.Ticker(ticker)
        hist = data.history(period="1d")
        if not hist.empty:
            return True
        else:
           return False
    except:
        return False
