"""
Repository for persisting and querying EconomicCalendarEvent records.
"""
from datetime import date, datetime
from decimal import Decimal
from typing import List, Optional

from base.models import EconomicCalendarEvent


def _parse_date(s: str) -> Optional[date]:
    """Parse YYYY-MM-DD or return None."""
    if not s or not (isinstance(s, str) and s.strip()):
        return None
    try:
        return datetime.strptime(str(s).strip()[:10], "%Y-%m-%d").date()
    except (ValueError, TypeError):
        return None


def _parse_decimal(s: str) -> Optional[Decimal]:
    """Parse decimal or return None."""
    if s is None or (isinstance(s, str) and not s.strip()):
        return None
    try:
        return Decimal(str(s).strip())
    except (ValueError, TypeError):
        return None


class EconomicCalendarEventRepository:
    """Handles persistence and retrieval of economic calendar events (earnings, IPO)."""

    def get_events(self, event_type: str):
        """Return queryset of events for event_type, ordered by report_date, symbol."""
        return EconomicCalendarEvent.objects.filter(event_type=event_type).order_by("report_date", "symbol")

    def get_latest_updated_at(self, event_type: str) -> Optional[datetime]:
        """Return the most recent updated_at for event_type, or None."""
        return (
            EconomicCalendarEvent.objects.filter(event_type=event_type)
            .order_by("-updated_at")
            .values_list("updated_at", flat=True)
            .first()
        )

    def replace_earnings(self, rows: List[list]) -> None:
        """Replace all earnings events with rows from API (list of lists: symbol, name, reportDate, fiscalDateEnding, estimate, currency)."""
        EconomicCalendarEvent.objects.filter(event_type=EconomicCalendarEvent.EventType.EARNINGS).delete()
        to_create: List[EconomicCalendarEvent] = []
        for row in rows:
            if len(row) < 6:
                continue
            symbol = (row[0] or "")[:50] if len(row) > 0 else ""
            name = (row[1] or "")[:255] if len(row) > 1 else ""
            report_str = row[2] if len(row) > 2 else ""
            fiscal_str = row[3] if len(row) > 3 else ""
            estimate_str = row[4] if len(row) > 4 else ""
            currency = (row[5] or "")[:10] if len(row) > 5 else ""
            report_date = _parse_date(report_str)
            if report_date is None and report_str:
                continue
            fiscal_date = _parse_date(fiscal_str)
            estimate = _parse_decimal(estimate_str)
            to_create.append(
                EconomicCalendarEvent(
                    event_type=EconomicCalendarEvent.EventType.EARNINGS,
                    symbol=symbol,
                    name=name,
                    report_date=report_date,
                    fiscal_date_ending=fiscal_date,
                    estimate=estimate,
                    currency=currency,
                )
            )
        if to_create:
            EconomicCalendarEvent.objects.bulk_create(to_create)

    def replace_ipo(self, rows: List[list]) -> None:
        """Replace all IPO events with rows from API (list of lists; we use index 0=symbol, 1=name, 2=report_date)."""
        EconomicCalendarEvent.objects.filter(event_type=EconomicCalendarEvent.EventType.IPO).delete()
        to_create: List[EconomicCalendarEvent] = []
        for row in rows:
            if len(row) < 1:
                continue
            symbol = (row[0] or "")[:50] if len(row) > 0 else ""
            name = (row[1] or "")[:255] if len(row) > 1 else ""
            report_date = _parse_date(row[2]) if len(row) > 2 else None
            to_create.append(
                EconomicCalendarEvent(
                    event_type=EconomicCalendarEvent.EventType.IPO,
                    symbol=symbol,
                    name=name,
                    report_date=report_date,
                    fiscal_date_ending=None,
                    estimate=None,
                    currency="",
                )
            )
        if to_create:
            EconomicCalendarEvent.objects.bulk_create(to_create)
