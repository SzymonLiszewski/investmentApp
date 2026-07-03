import logging
from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import List, Optional

from django.db import transaction

from analytics.models import SarimaForecast
from analytics.services.predictions import sarima_forecast
from analytics.services.top_stocks import get_top_stock_symbols

logger = logging.getLogger(__name__)


def _to_decimal(value: float) -> Decimal:
    return Decimal(str(round(value, 4)))


def generate_sarima_forecast_for_symbol(
    symbol: str,
    predicted_days: int = 30,
    history_days: int = 365,
) -> int:
    """Fit SARIMA on recent price history and atomically replace the stored
    forecast rows for the symbol. Returns the number of rows written."""
    end = date.today()
    start = end - timedelta(days=history_days)
    forecast = sarima_forecast(symbol, start.isoformat(), end.isoformat(), predicted_days)

    rows = [
        SarimaForecast(
            symbol=symbol,
            forecast_date=datetime.strptime(point["date"], "%Y-%m-%d").date(),
            predicted_price=_to_decimal(point["predicted"]),
            lower_bound=_to_decimal(point["lower"]),
            upper_bound=_to_decimal(point["upper"]),
        )
        for point in forecast
    ]
    with transaction.atomic():
        SarimaForecast.objects.filter(symbol=symbol).delete()
        SarimaForecast.objects.bulk_create(rows)
    return len(rows)


def run_sarima_batch(symbols: Optional[List[str]] = None) -> dict:
    """Generate SARIMA forecasts for each symbol (defaults to the top-stocks list).

    A failure on one symbol never aborts the batch.
    Returns {"succeeded": [symbol, ...], "failed": {symbol: error_message}}.
    """
    if symbols is None:
        symbols = get_top_stock_symbols()

    succeeded = []
    failed = {}
    for symbol in symbols:
        try:
            count = generate_sarima_forecast_for_symbol(symbol)
            succeeded.append(symbol)
            logger.info("SARIMA forecast stored for %s (%d rows)", symbol, count)
        except Exception as exc:
            failed[symbol] = str(exc)
            logger.exception("SARIMA forecast failed for %s", symbol)
    logger.info("SARIMA batch done: %d succeeded, %d failed", len(succeeded), len(failed))
    return {"succeeded": succeeded, "failed": failed}
