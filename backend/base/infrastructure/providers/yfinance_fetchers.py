"""
Yfinance implementations of data fetcher abstractions.
"""
import logging
from datetime import date, timedelta
from typing import Dict, List, Optional, Any
from decimal import Decimal

import pandas as pd
import yfinance as yf

from base.infrastructure.interfaces.market_data_fetcher import StockDataFetcher, CryptoDataFetcher, FXDataFetcher

logger = logging.getLogger(__name__)


class YfinanceStockDataFetcher(StockDataFetcher):
    """Implementation of StockDataFetcher using yfinance library."""

    def __init__(self):
        self._cache = {}

    def get_current_price(self, symbol: str) -> Optional[Decimal]:
        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info
            price = info.get('currentPrice') or info.get('regularMarketPrice')
            if price is None:
                hist = ticker.history(period='1d')
                if not hist.empty:
                    price = hist['Close'].iloc[-1]
            if price is not None:
                return Decimal(str(price))
            return None
        except Exception as e:
            logger.warning("Error fetching price for %s: %s", symbol, e)
            return None

    def get_stock_info(self, symbol: str) -> Optional[Dict[str, Any]]:
        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info
            return {
                'symbol': symbol,
                'name': info.get('longName', ''),
                'current_price': self.get_current_price(symbol),
                'currency': info.get('currency', 'USD'),
                'market_cap': info.get('marketCap'),
                'sector': info.get('sector', ''),
                'industry': info.get('industry', ''),
            }
        except Exception as e:
            logger.warning("Error fetching info for %s: %s", symbol, e)
            return None

    def get_currency(self, symbol: str) -> Optional[str]:
        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info
            return info.get('currency', 'USD')
        except Exception as e:
            logger.warning("Error fetching currency for %s: %s", symbol, e)
            return None

    def get_historical_prices(
        self,
        symbols: List[str],
        start_date: date,
        end_date: date,
    ) -> Dict[str, pd.Series]:
        if not symbols:
            return {}
        try:
            data = yf.download(
                symbols,
                start=start_date.isoformat(),
                end=(end_date + timedelta(days=1)).isoformat(),
                progress=False,
            )
        except Exception:
            logger.exception("yfinance download failed for %s", symbols)
            return {}
        if data is None or data.empty:
            return {}
        try:
            close = data["Close"]
        except KeyError:
            return {}
        if isinstance(close, pd.Series):
            close = close.to_frame(name=symbols[0])
        if isinstance(close.columns, pd.MultiIndex):
            close.columns = close.columns.get_level_values(-1)
        close.index = pd.to_datetime(close.index).date
        close = close.ffill()
        result: Dict[str, pd.Series] = {}
        for sym in symbols:
            if sym in close.columns:
                result[sym] = close[sym].dropna()
        return result

    # ---- Additional methods (integrated from utils/dataFetcher) ----

    def get_stock_price_history(self, ticker: str, start_date: str, end_date: str) -> dict:
        """Get historical closing prices as {date_str: price}."""
        data = yf.download(ticker, start=start_date, end=end_date)
        closing_prices = {}
        for index, row in data.iterrows():
            date_str = index.strftime('%Y-%m-%d')
            closing_price = row['Close']
            closing_prices[date_str] = closing_price
        return closing_prices

    def get_fundamental_analysis(self, ticker: str) -> dict:
        """Get fundamental analysis data for a ticker."""
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
        return {
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
            'Revenue History': revenue_yearly,
        }

    def get_basic_stock_info(self, ticker: str) -> dict:
        """Get basic stock info (company name, price, change)."""
        stock = yf.Ticker(ticker)
        info = stock.info
        hist = stock.history(period='5d')
        current_price = hist['Close'].iloc[-1]
        if len(hist) < 2:
            return {
                'Company Name': info.get('shortName', 'N/A'),
                'Current Price': current_price,
                'Price Change': 'N/A',
                'Percent Change': 'N/A',
            }
        last_close = hist['Close'].iloc[-1]
        previous_close = hist['Close'].iloc[-2]
        price_change = last_close - previous_close
        percent_change = (price_change / previous_close) * 100
        return {
            'Company Name': info.get('shortName', 'N/A'),
            'Current Price': current_price,
            'Price Change': round(price_change, 2),
            'Percent Change': round(percent_change, 2),
        }

    def get_technical_indicators(self, ticker: str) -> dict:
        """Get technical analysis indicators for a ticker."""
        import ta as ta_lib
        stock = yf.Ticker(ticker)
        data = stock.history(period="1y")
        if data.empty:
            return {"error": "No data for the given ticker"}
        data['SMA_50'] = ta_lib.trend.sma_indicator(data['Close'], window=50)
        data['SMA_200'] = ta_lib.trend.sma_indicator(data['Close'], window=200)
        data['RSI'] = ta_lib.momentum.rsi(data['Close'], window=14)
        data['MACD'] = ta_lib.trend.macd(data['Close'])
        data['MACD_Signal'] = ta_lib.trend.macd_signal(data['Close'])
        data['Bollinger_High'] = ta_lib.volatility.bollinger_hband(data['Close'])
        data['Bollinger_Low'] = ta_lib.volatility.bollinger_lband(data['Close'])
        return {
            "Ticker": ticker,
            "Current Price": data['Close'].iloc[-1],
            "SMA_50": data['SMA_50'].iloc[-1],
            "SMA_200": data['SMA_200'].iloc[-1],
            "RSI": data['RSI'].iloc[-1],
            "MACD": data['MACD'].iloc[-1],
            "MACD_Signal": data['MACD_Signal'].iloc[-1],
            "Bollinger_High": data['Bollinger_High'].iloc[-1],
            "Bollinger_Low": data['Bollinger_Low'].iloc[-1],
        }


class YfinanceCryptoDataFetcher(CryptoDataFetcher):
    """Implementation of CryptoDataFetcher using yfinance library."""

    def __init__(self):
        self._cache = {}

    def _yfinance_symbol(self, symbol: str) -> str:
        if '-' in symbol:
            return symbol
        return f"{symbol}-USD"

    def get_current_price(self, symbol: str) -> Optional[Decimal]:
        try:
            yf_symbol = self._yfinance_symbol(symbol)
            ticker = yf.Ticker(yf_symbol)
            info = ticker.info
            price = info.get('regularMarketPrice') or info.get('currentPrice')
            if price is None:
                hist = ticker.history(period='1d')
                if not hist.empty:
                    price = hist['Close'].iloc[-1]
            if price is not None:
                return Decimal(str(price))
            return None
        except Exception as e:
            logger.warning("Error fetching crypto price for %s: %s", symbol, e)
            return None

    def get_currency(self, symbol: str) -> Optional[str]:
        try:
            if '-' in symbol:
                return symbol.split('-')[-1].upper()
            return 'USD'
        except Exception as e:
            logger.warning("Error fetching crypto currency for %s: %s", symbol, e)
            return None

    def get_historical_prices(
        self,
        symbols: List[str],
        start_date: date,
        end_date: date,
    ) -> Dict[str, pd.Series]:
        if not symbols:
            return {}
        yf_to_orig: Dict[str, str] = {}
        for sym in symbols:
            yf_to_orig[self._yfinance_symbol(sym)] = sym
        yf_symbols = list(yf_to_orig.keys())
        try:
            data = yf.download(
                yf_symbols,
                start=start_date.isoformat(),
                end=(end_date + timedelta(days=1)).isoformat(),
                progress=False,
            )
        except Exception:
            logger.exception("yfinance crypto download failed for %s", yf_symbols)
            return {}
        if data is None or data.empty:
            return {}
        try:
            close = data["Close"]
        except KeyError:
            return {}
        if isinstance(close, pd.Series):
            close = close.to_frame(name=yf_symbols[0])
        if isinstance(close.columns, pd.MultiIndex):
            close.columns = close.columns.get_level_values(-1)
        close.index = pd.to_datetime(close.index).date
        close = close.ffill()
        result: Dict[str, pd.Series] = {}
        for yf_sym, orig_sym in yf_to_orig.items():
            if yf_sym in close.columns:
                result[orig_sym] = close[yf_sym].dropna()
        return result


class YfinanceFXDataFetcher(FXDataFetcher):
    """Implementation of FXDataFetcher using yfinance (e.g. USDPLN=X)."""

    def get_historical_fx_series(
        self,
        from_currency: str,
        to_currency: str,
        start_date: date,
        end_date: date,
    ) -> Optional[pd.Series]:
        if from_currency == to_currency:
            idx = pd.date_range(start=start_date, end=end_date, freq='D')
            return pd.Series(1.0, index=pd.DatetimeIndex(idx))
        # Try ticker from_to=X (gives "to per from")
        ticker_symbol = f"{from_currency}{to_currency}=X"
        try:
            ticker = yf.Ticker(ticker_symbol)
            hist = ticker.history(
                start=start_date.isoformat(),
                end=(end_date + timedelta(days=1)).isoformat(),
                auto_adjust=False,
            )
            if hist is not None and not hist.empty and 'Close' in hist.columns:
                close = hist['Close'].dropna()
                if not close.empty:
                    close.index = pd.to_datetime(close.index)
                    if close.index.tz is not None:
                        close.index = close.index.tz_localize(None)
                    close.index = close.index.date
                    close.index = pd.DatetimeIndex(close.index)
                    return close.astype(float)
        except Exception as e:
            logger.debug("FX ticker %s failed: %s", ticker_symbol, e)
        # Try inverse pair (e.g. USDPLN for PLN→USD)
        ticker_symbol = f"{to_currency}{from_currency}=X"
        try:
            ticker = yf.Ticker(ticker_symbol)
            hist = ticker.history(
                start=start_date.isoformat(),
                end=(end_date + timedelta(days=1)).isoformat(),
                auto_adjust=False,
            )
            if hist is not None and not hist.empty and 'Close' in hist.columns:
                close = hist['Close'].dropna()
                if not close.empty:
                    inv = (1.0 / close).astype(float)
                    inv.index = pd.to_datetime(inv.index)
                    if inv.index.tz is not None:
                        inv.index = inv.index.tz_localize(None)
                    inv.index = inv.index.date
                    inv.index = pd.DatetimeIndex(inv.index)
                    return inv
        except Exception as e:
            logger.warning("Failed to fetch historical FX %s→%s: %s", from_currency, to_currency, e)
        return None

    def get_current_rate(self, from_currency: str, to_currency: str) -> Optional[Decimal]:
        if from_currency == to_currency:
            return Decimal('1')
        for ticker_symbol in (f"{from_currency}{to_currency}=X", f"{to_currency}{from_currency}=X"):
            try:
                ticker = yf.Ticker(ticker_symbol)
                hist = ticker.history(period='2d')
                if hist is not None and not hist.empty and 'Close' in hist.columns:
                    rate = float(hist['Close'].iloc[-1])
                    if ticker_symbol.startswith(to_currency):
                        rate = 1.0 / rate
                    return Decimal(str(rate))
            except Exception as e:
                logger.debug("FX rate %s: %s", ticker_symbol, e)
        return None
