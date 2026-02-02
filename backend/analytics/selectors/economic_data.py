"""
Selectors for economic data (WIBOR, inflation).
Pure read-only access from the database - no business logic.
"""
from typing import Optional
from decimal import Decimal
from datetime import date, datetime

from analytics.models import EconomicData


def get_latest_economic_data() -> Optional[EconomicData]:
    return EconomicData.objects.order_by('-date').first()


def get_economic_data_for_date(target_date) -> Optional[EconomicData]:
    """
    Returns economic data for the given date or the nearest earlier record.

    Args:
        target_date: date, datetime or str in YYYY-MM-DD format

    Returns:
        EconomicData or None if no data.
    """
    if isinstance(target_date, str):
        target_date = datetime.strptime(target_date, '%Y-%m-%d').date()
    elif isinstance(target_date, datetime):
        target_date = target_date.date()

    try:
        return EconomicData.objects.get(date=target_date)
    except EconomicData.DoesNotExist:
        return (
            EconomicData.objects.filter(date__lte=target_date)
            .order_by('-date')
            .first()
        )


def get_latest_wibor(wibor_type: str = '3M') -> Optional[Decimal]:
    """
    Returns the latest WIBOR value.

    Args:
        wibor_type: '3M' or '6M'

    Returns:
        WIBOR rate in % (Decimal) or None.
    """
    latest = get_latest_economic_data()
    if not latest:
        return None
    if wibor_type.upper() == '6M':
        return latest.wibor_6m
    return latest.wibor_3m


def get_latest_inflation() -> Optional[Decimal]:
    latest = get_latest_economic_data()
    if not latest:
        return None
    return latest.inflation_cpi


def get_inflation_for_date(target_date) -> Optional[Decimal]:
    data = get_economic_data_for_date(target_date)
    if not data:
        return None
    return data.inflation_cpi


def get_wibor_for_date(target_date, wibor_type: str = '3M') -> Optional[Decimal]:
    data = get_economic_data_for_date(target_date)
    if not data:
        return None
    if wibor_type.upper() == '6M':
        return data.wibor_6m
    return data.wibor_3m
