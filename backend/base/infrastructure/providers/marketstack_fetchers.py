"""
MarketStack API implementations of data fetcher abstractions.

See https://marketstack.com/ for API documentation.

Requires MARKETSTACK_API_KEY in environment (or .env).
"""
import json
import logging
from datetime import date
from typing import Dict, List, Optional, Any
from urllib.parse import urlencode
from urllib.request import urlopen, Request

import pandas as pd
from decouple import config

from base.infrastructure.interfaces.market_data_fetcher import (
    StockDataFetcher,
    CurrentPriceResult,
)

logger = logging.getLogger(__name__)

MARKETSTACK_EOD_URL = "https://api.marketstack.com/v2/eod"


def _get_marketstack_access_key(override: Optional[str] = None) -> str:
    """Load MarketStack API key from override or MARKETSTACK_API_KEY env."""
    if override:
        return override.strip()
    return config("MARKETSTACK_API_KEY", default="").strip()


class MarketStackStockDataFetcher(StockDataFetcher):
    """
    Implementation of StockDataFetcher using the MarketStack API.

    API key is read from MARKETSTACK_API_KEY env var (or .env).
    Optional exchange filter for EOD endpoint.
    """

    def __init__(self, access_key: Optional[str] = None, exchange: Optional[str] = None):
        self.access_key = _get_marketstack_access_key(access_key)
        self.exchange = exchange

    def get_current_price(self, symbol: str) -> Optional[CurrentPriceResult]:
        """Get the current price and currency of a stock."""
        raise NotImplementedError("MarketStackStockDataFetcher.get_current_price")

    def get_stock_info(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Get detailed information about a stock."""
        raise NotImplementedError("MarketStackStockDataFetcher.get_stock_info")

    def get_historical_prices(
        self,
        symbols: List[str],
        start_date: date,
        end_date: date,
    ) -> Dict[str, pd.Series]:
        """Batch-download historical Close prices for multiple stock symbols."""
        if not symbols:
            return {}

        params: Dict[str, str] = {
            "access_key": self.access_key,
            "symbols": ",".join(symbols),
            "date_from": start_date.isoformat(),
            "date_to": end_date.isoformat(),
        }
        if self.exchange:
            params["exchange"] = self.exchange

        url = f"{MARKETSTACK_EOD_URL}?{urlencode(params)}"
        try:
            req = Request(url, method="GET")
            with urlopen(req, timeout=30) as resp:
                body = resp.read().decode()
        except Exception as e:
            logger.warning("MarketStack EOD request failed for %s: %s", symbols, e)
            return {}

        try:
            data = json.loads(body)
        except json.JSONDecodeError as e:
            logger.warning("MarketStack EOD invalid JSON: %s", e)
            return {}

        raw_list = data.get("data")
        if not raw_list or not isinstance(raw_list, list):
            return {}

        # Group by symbol: list of (date, close)
        by_symbol: Dict[str, List[tuple]] = {sym: [] for sym in symbols}
        for row in raw_list:
            if not isinstance(row, dict):
                continue
            sym = row.get("symbol")
            if sym not in by_symbol:
                continue
            date_str = row.get("date")
            close = row.get("close")
            if date_str is None or close is None:
                continue
            try:
                d = pd.Timestamp(date_str).date()
                c = float(close)
            except (TypeError, ValueError):
                continue
            by_symbol[sym].append((d, c))

        result: Dict[str, pd.Series] = {}
        for sym in symbols:
            points = by_symbol.get(sym, [])
            if not points:
                continue
            points.sort(key=lambda x: x[0])
            dates = [p[0] for p in points]
            values = [p[1] for p in points]
            series = pd.Series(values, index=pd.DatetimeIndex(dates))
            series.index = series.index.date
            result[sym] = series.dropna()
        return result
