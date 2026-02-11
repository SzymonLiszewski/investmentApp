"""
Shared utilities for the portfolio app.
"""
from datetime import date, datetime
from typing import Optional, Tuple

DATE_FORMAT = '%Y-%m-%d'


def parse_date(
    value: Optional[str],
    default: date,
    param_name: str = 'date',
) -> Tuple[date, Optional[str]]:
    """
    Parse a single date from string (YYYY-MM-DD).
    Returns (date, error_message). If value is missing or empty, returns (default, None).
    If value is invalid, returns (default, error_message). Otherwise (parsed_date, None).
    """
    if not value or not value.strip():
        return default, None
    try:
        return datetime.strptime(value.strip(), DATE_FORMAT).date(), None
    except ValueError:
        return default, f'Invalid {param_name} format. Use YYYY-MM-DD'
