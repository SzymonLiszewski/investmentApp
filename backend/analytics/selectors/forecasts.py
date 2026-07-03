from datetime import timedelta
from typing import List, Optional

from django.utils import timezone

from analytics.models import SarimaForecast


def get_stored_sarima_forecast(symbol: str, max_age_days: int = 7) -> Optional[List[dict]]:
    """Return stored SARIMA forecast rows for the symbol, or None when absent
    or older than max_age_days (stale forecasts should be recomputed on demand)."""
    rows = list(
        SarimaForecast.objects.filter(symbol=symbol).order_by("forecast_date")
    )
    if not rows:
        return None
    cutoff = timezone.now() - timedelta(days=max_age_days)
    if rows[0].created_at < cutoff:
        return None
    return [
        {
            "date": row.forecast_date.isoformat(),
            "predicted": float(row.predicted_price),
            "lower": float(row.lower_bound) if row.lower_bound is not None else None,
            "upper": float(row.upper_bound) if row.upper_bound is not None else None,
        }
        for row in rows
    ]
