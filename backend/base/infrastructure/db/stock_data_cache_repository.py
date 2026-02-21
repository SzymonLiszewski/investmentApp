"""
Repository for persisting and querying StockDataCache records.
"""
from datetime import datetime
from typing import Any, Dict, Optional

from base.models import StockDataCache


class StockDataCacheRepository:
    """Handles persistence and retrieval of stock data cache (basic_info, fundamental_analysis, technical_indicators)."""

    def get(self, symbol: str, data_type: str) -> Optional[StockDataCache]:
        """Return cached record for symbol and data_type, or None."""
        return StockDataCache.objects.filter(symbol=symbol, data_type=data_type).first()

    def get_updated_at(self, symbol: str, data_type: str) -> Optional[datetime]:
        """Return updated_at for the cache record, or None if missing."""
        row = (
            StockDataCache.objects.filter(symbol=symbol, data_type=data_type)
            .values_list("updated_at", flat=True)
            .first()
        )
        return row

    def save(self, symbol: str, data_type: str, data: Dict[str, Any]) -> None:
        """Create or update cache record for symbol and data_type."""
        StockDataCache.objects.update_or_create(
            symbol=symbol,
            data_type=data_type,
            defaults={"data": data},
        )
