"""
Service for serving stock data (basic info, fundamental, technical) from DB cache
or from the fetcher when cache is missing or stale.
"""
import logging
from datetime import datetime, timezone, timedelta
from typing import Any, Optional

from base.infrastructure.db.stock_data_cache_repository import StockDataCacheRepository

logger = logging.getLogger(__name__)

STOCK_DATA_CACHE_MAX_AGE = timedelta(minutes=15)


def _to_json_serializable(obj: Any) -> Any:
    """Convert dict values to JSON-serializable types (e.g. numpy -> float)."""
    if hasattr(obj, "item") and callable(getattr(obj, "item")):
        return float(obj)
    if isinstance(obj, dict):
        return {k: _to_json_serializable(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_to_json_serializable(v) for v in obj]
    return obj


def get_stock_data(
    symbol: str,
    data_type: str,
    fetcher: Any,
    repository: Optional[StockDataCacheRepository] = None,
    max_age: Optional[timedelta] = None,
) -> dict:
    """
    Return stock data for symbol and data_type. Uses cache if present and not older than max_age;
    otherwise fetches from fetcher, saves via repository and returns.

    data_type: one of 'basic_info', 'fundamental_analysis', 'technical_indicators'.
    fetcher: must have get_basic_stock_info, get_fundamental_analysis, get_technical_indicators.
    """
    repo = repository or StockDataCacheRepository()
    max_age = max_age or STOCK_DATA_CACHE_MAX_AGE
    try:
        cached = repo.get(symbol, data_type)
        if cached is not None:
            now = datetime.now(timezone.utc)
            updated = cached.updated_at
            if updated.tzinfo is None:
                updated = updated.replace(tzinfo=timezone.utc)
            if now - updated <= max_age:
                return cached.data
    except Exception:
        pass

    logger.info("Fetching stock data from external API: symbol=%s, data_type=%s", symbol, data_type)
    fetch_methods = {
        "basic_info": getattr(fetcher, "get_basic_stock_info", None),
        "fundamental_analysis": getattr(fetcher, "get_fundamental_analysis", None),
        "technical_indicators": getattr(fetcher, "get_technical_indicators", None),
    }
    fetch_fn = fetch_methods.get(data_type)
    if not fetch_fn:
        return {}

    try:
        data = fetch_fn(symbol)
    except Exception as e:
        logger.warning("Failed to fetch %s for %s: %s", data_type, symbol, e)
        return {}

    if not isinstance(data, dict):
        return {}

    data_serializable = _to_json_serializable(data)
    try:
        repo.save(symbol, data_type, data_serializable)
    except Exception as e:
        logger.warning("Failed to save cache for %s %s: %s", symbol, data_type, e)

    return data_serializable
