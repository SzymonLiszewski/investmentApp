"""
Repository for persisting and querying PriceHistory records.
"""
from datetime import date
from decimal import Decimal
from typing import Dict, List, Optional

from base.infrastructure.interfaces.price_repository import AbstractPriceRepository
from base.models import Asset, PriceHistory


class PriceRepository(AbstractPriceRepository):
    """Handles persistence and retrieval of historical price data."""

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
