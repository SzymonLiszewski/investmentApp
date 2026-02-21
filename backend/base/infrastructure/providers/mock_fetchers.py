"""
Mock implementations of data fetchers for local development and tests.
No external API calls; returns deterministic data based on symbol.
Enable via USE_MOCK_DATA_FETCHER=true in environment (see backend.settings).
"""
import random
from datetime import date, timedelta
from decimal import Decimal
from typing import Any, Dict, List, Optional

import pandas as pd

from base.infrastructure.interfaces.market_data_fetcher import (
    StockDataFetcher,
    CryptoDataFetcher,
    FXDataFetcher,
)


def _mock_price_for_symbol(symbol: str) -> Decimal:
    """Deterministic mock price from symbol hash (stable across runs)."""
    n = sum(ord(c) for c in symbol.upper()) % 1000
    return Decimal(str(100 + (n % 200) + (n * 0.01)))


def _mock_historical_series(symbol: str, start_date: date, end_date: date) -> pd.Series:
    """Generate a deterministic random-walk mock price series for the date range."""
    dates = pd.date_range(start=start_date, end=end_date, freq="B")
    if len(dates) == 0:
        return pd.Series(dtype=float)
    seed = (
        sum(ord(c) for c in symbol.upper())
        + start_date.toordinal()
        + end_date.toordinal() * 1000
    ) % (2**32)
    rng = random.Random(seed)
    base = float(_mock_price_for_symbol(symbol))
    values = [base]
    for _ in range(len(dates) - 1):
        # Small random step (e.g. -2% to +2%) so series looks realistic
        change_pct = (rng.random() - 0.5) * 0.04
        next_val = values[-1] * (1 + change_pct)
        values.append(round(next_val, 2))
    return pd.Series(values, index=pd.DatetimeIndex(dates).date).dropna()


def _mock_fx_rate(from_currency: str, to_currency: str) -> Decimal:
    """Deterministic mock FX rate: amount_in_from * rate = amount_in_to."""
    if from_currency.upper() == to_currency.upper():
        return Decimal("1")
    n = sum(ord(c) for c in (from_currency + to_currency).upper()) % 100
    # Stable rate in [0.2, 5.0] so conversions look plausible
    rate = 0.2 + (n % 48) * 0.1
    return Decimal(str(round(rate, 4)))


class MockStockDataFetcher(StockDataFetcher):
    """
    Stock data fetcher that returns mock data. No network calls.
    Use for local development or tests when external API is unavailable.
    """

    def get_current_price(self, symbol: str) -> Optional[Decimal]:
        return _mock_price_for_symbol(symbol)

    def get_stock_info(self, symbol: str) -> Optional[Dict[str, Any]]:
        price = self.get_current_price(symbol)
        return {
            "symbol": symbol,
            "name": f"{symbol} Inc.",
            "current_price": price,
            "currency": "USD",
            "market_cap": 1_000_000_000,
            "sector": "Technology",
            "industry": "Software",
        }

    def get_currency(self, symbol: str) -> Optional[str]:
        return "USD"

    def get_historical_prices(
        self,
        symbols: List[str],
        start_date: date,
        end_date: date,
    ) -> Dict[str, pd.Series]:
        result: Dict[str, pd.Series] = {}
        for sym in symbols:
            result[sym] = _mock_historical_series(sym, start_date, end_date)
        return result

    # ---- Used by get_stock_data / stock_data_service (basic_info, fundamental_analysis, technical_indicators) ----

    def get_basic_stock_info(self, ticker: str) -> dict:
        price = float(_mock_price_for_symbol(ticker))
        return {
            "Company Name": f"{ticker} Inc.",
            "Current Price": price,
            "Price Change": round(random.uniform(-10.0, 10.0), 2),
            "Percent Change": round(random.uniform(-5.0, 5.0), 2),
        }

    def get_fundamental_analysis(self, ticker: str) -> dict:
        price = float(_mock_price_for_symbol(ticker))
        return {
            "Ticker": ticker,
            "Current Price": price,
            "Market Cap": 500_000_000,
            "P/S Ratio": 5.2,
            "P/E Ratio": 22.0,
            "EPS": 4.5,
            "Dividend Yield": 0.5,
            "52 Week High": price * 1.2,
            "52 Week Low": price * 0.85,
            "Dividend History": {"2024": 2.0, "2023": 1.8},
            "Revenue History": {"2024": 100.0, "2023": 90.0},
        }

    def get_technical_indicators(self, ticker: str) -> dict:
        price = float(_mock_price_for_symbol(ticker))
        return {
            "Ticker": ticker,
            "Current Price": price,
            "SMA_50": price * 0.98,
            "SMA_200": price * 0.95,
            "RSI": 55.0,
            "MACD": 0.5,
            "MACD_Signal": 0.4,
            "Bollinger_High": price * 1.02,
            "Bollinger_Low": price * 0.98,
        }


class MockCryptoDataFetcher(CryptoDataFetcher):
    """
    Crypto data fetcher that returns mock data. No network calls.
    Use for local development or tests when external API is unavailable.
    """

    def get_current_price(self, symbol: str) -> Optional[Decimal]:
        # Normalize BTC, ETH etc. to consistent mock price
        base = symbol.split("-")[0] if "-" in symbol else symbol
        return _mock_price_for_symbol(base)

    def get_currency(self, symbol: str) -> Optional[str]:
        if "-" in symbol:
            return symbol.split("-")[-1].upper()
        return "USD"

    def get_historical_prices(
        self,
        symbols: List[str],
        start_date: date,
        end_date: date,
    ) -> Dict[str, pd.Series]:
        result: Dict[str, pd.Series] = {}
        for sym in symbols:
            base = sym.split("-")[0] if "-" in sym else sym
            # Return keyed by original symbol so callers (e.g. PriceRepository) get expected key
            result[sym] = _mock_historical_series(base, start_date, end_date)
        return result


class MockFXDataFetcher(FXDataFetcher):
    """
    FX data fetcher that returns mock exchange rates. No network calls.
    Use for local development or tests when external API is unavailable.
    """

    def get_historical_fx_series(
        self,
        from_currency: str,
        to_currency: str,
        start_date: date,
        end_date: date,
    ) -> Optional[pd.Series]:
        rate = float(_mock_fx_rate(from_currency, to_currency))
        dates = pd.date_range(start=start_date, end=end_date, freq="B")
        values = [rate] * len(dates)
        return pd.Series(values, index=pd.DatetimeIndex(dates))

    def get_current_rate(self, from_currency: str, to_currency: str) -> Optional[Decimal]:
        return _mock_fx_rate(from_currency, to_currency)
