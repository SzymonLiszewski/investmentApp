"""
Selectors for portfolio snapshots.
Pure read-only access from the database - no business logic.
"""
from datetime import date
from typing import TYPE_CHECKING

from portfolio.models import PortfolioSnapshot

if TYPE_CHECKING:
    from django.contrib.auth.models import User


def get_portfolio_snapshots(
    user: 'User',
    currency: str,
    start_date: date,
    end_date: date,
):
    """
    Return portfolio snapshots for the given user, currency and date range.
    Ordered by date ascending.
    """
    return PortfolioSnapshot.objects.filter(
        user=user,
        currency=currency,
        date__gte=start_date,
        date__lte=end_date,
    ).order_by('date')
