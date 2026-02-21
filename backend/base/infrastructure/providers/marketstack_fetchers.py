"""
MarketStack API implementations of data fetcher abstractions.

See https://marketstack.com/ for API documentation.
"""
from datetime import date
from typing import Dict, List, Optional, Any

import pandas as pd

from base.infrastructure.interfaces.market_data_fetcher import (
    StockDataFetcher,
    CurrentPriceResult,
)


class MarketStackStockDataFetcher(StockDataFetcher):
    """
    Implementation of StockDataFetcher using the MarketStack API.

    Not yet fully implemented; add API key and request logic as needed.
    """

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
        raise NotImplementedError("MarketStackStockDataFetcher.get_historical_prices")
