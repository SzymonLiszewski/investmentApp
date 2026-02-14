"""
Repository for persisting and querying PriceHistory records.
"""
import logging
from datetime import date, timedelta
from decimal import Decimal
from typing import Dict, List, Optional, Tuple, Union

import pandas as pd

from base.infrastructure.interfaces.market_data_fetcher import (
    StockDataFetcher,
    CryptoDataFetcher,
)
from base.infrastructure.interfaces.price_repository import AbstractPriceRepository
from base.models import Asset, PriceHistory

logger = logging.getLogger(__name__)


class PriceRepository(AbstractPriceRepository):
    """Handles persistence and retrieval of historical price data."""

    def get_price_history(
        self,
        symbol: str,
        start_date: date,
        end_date: date,
        fetcher: Union[StockDataFetcher, CryptoDataFetcher],
        asset: Optional[Asset] = None,
    ) -> Dict[date, Decimal]:
        """
        Return historical closing prices for each day in [start_date, end_date].
        If data is missing or incomplete in the DB, fetches it from the fetcher
        internally and then returns the prices. Callers do not need to check
        or fill data themselves.
        """
        self._ensure_prices_for_range(symbol, start_date, end_date, fetcher, asset=asset)
        return self.get_close_prices(symbol, start_date, end_date)

    def _ensure_prices_for_range(
        self,
        symbol: str,
        start_date: date,
        end_date: date,
        fetcher: Union[StockDataFetcher, CryptoDataFetcher],
        asset: Optional[Asset] = None,
    ) -> int:
        """
        Internal: fetch from API when we have no data, or when we're missing
        data at the start (earliest in DB > start_date) or at the end
        (latest in DB < end_date). Gaps in the middle are normal and do not
        trigger a fetch.
        """
        existing_dates = set(
            PriceHistory.objects.filter(
                symbol=symbol,
                date__gte=start_date,
                date__lte=end_date,
            ).values_list("date", flat=True)
        )
        earliest_in_range = min(existing_dates) if existing_dates else None
        latest_in_range = max(existing_dates) if existing_dates else None

        ranges_to_fetch: List[Tuple[date, date]] = []
        if earliest_in_range is None:
            ranges_to_fetch.append((start_date, end_date))
        else:
            if earliest_in_range > start_date:
                ranges_to_fetch.append((start_date, earliest_in_range - timedelta(days=1)))
            if latest_in_range < end_date:
                ranges_to_fetch.append((latest_in_range + timedelta(days=1), end_date))

        if not ranges_to_fetch:
            return 0

        total_created = 0
        for fetch_start, fetch_end in ranges_to_fetch:
            logger.info(
                "Fetching prices from external API: symbol=%s, range=%s to %s",
                symbol,
                fetch_start,
                fetch_end,
            )
            try:
                data = fetcher.get_historical_prices([symbol], fetch_start, fetch_end)
            except Exception as e:
                logger.warning(
                    "Failed to fetch historical prices for %s [%s, %s]: %s",
                    symbol,
                    fetch_start,
                    fetch_end,
                    e,
                )
                continue

            series = data.get(symbol)
            if series is None or series.empty:
                continue

            prices_to_save: List[Dict[str, Optional[Decimal]]] = []
            for ts, close in series.items():
                day = ts.date() if hasattr(ts, "date") else ts
                if day in existing_dates or not (fetch_start <= day <= fetch_end):
                    continue
                if close is None or (isinstance(close, float) and pd.isna(close)):
                    continue
                prices_to_save.append({
                    "date": day,
                    "close": Decimal(str(close)),
                })

            if prices_to_save:
                total_created += self.save_prices(symbol, prices_to_save, asset=asset)
                existing_dates.update(row["date"] for row in prices_to_save)

        return total_created

    def save_prices(
        self,
        symbol: str,
        prices: List[Dict[str, Optional[Decimal]]],
        asset: Optional[Asset] = None,
    ) -> int:
        """
        Save or update price history for a symbol.
        Each dict in prices should have 'date' and 'close'; may include 'open', 'high', 'low', 'volume'.
        Returns the number of records created or updated.
        """
        if not prices:
            return 0
        created = 0
        for row in prices:
            day = row.get("date")
            if not day:
                continue
            if isinstance(day, str):
                from datetime import datetime
                day = datetime.strptime(day, "%Y-%m-%d").date()
            obj, was_created = PriceHistory.objects.update_or_create(
                symbol=symbol,
                date=day,
                defaults={
                    "asset": asset,
                    "open": row.get("open"),
                    "high": row.get("high"),
                    "low": row.get("low"),
                    "close": row["close"],
                    "volume": row.get("volume"),
                },
            )
            if was_created:
                created += 1
        return created

    def get_by_symbol_and_date_range(
        self,
        symbol: str,
        start_date: date,
        end_date: date,
    ):
        """Return PriceHistory queryset for symbol within [start_date, end_date]."""
        return PriceHistory.objects.filter(
            symbol=symbol,
            date__gte=start_date,
            date__lte=end_date,
        ).order_by("date")

    def get_latest_date(self, symbol: str) -> Optional[date]:
        """Return the most recent date we have data for this symbol, or None."""
        latest = (
            PriceHistory.objects.filter(symbol=symbol)
            .order_by("-date")
            .values_list("date", flat=True)
            .first()
        )
        return latest

    def get_close_prices(
        self,
        symbol: str,
        start_date: date,
        end_date: date,
    ) -> Dict[date, Decimal]:
        """Return mapping of date -> close price for the given symbol and range."""
        qs = self.get_by_symbol_and_date_range(symbol, start_date, end_date)
        return {obj.date: obj.close for obj in qs}
