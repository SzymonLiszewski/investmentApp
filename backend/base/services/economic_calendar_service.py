"""
Service for serving economic calendar (earnings, IPO) from DB or from the fetcher when cache is stale/empty.
"""
import logging
from datetime import datetime, timezone, timedelta
from typing import Any, List, Optional

from base.infrastructure.db.economic_calendar_event_repository import EconomicCalendarEventRepository
from base.models import EconomicCalendarEvent

logger = logging.getLogger(__name__)

ECONOMIC_CALENDAR_CACHE_MAX_AGE = timedelta(hours=24)


def _events_to_rows(events) -> List[list]:
    """Convert EconomicCalendarEvent iterable to list of lists (same format as Alpha Vantage CSV)."""
    rows = []
    for e in events:
        report_str = e.report_date.strftime("%Y-%m-%d") if e.report_date else ""
        fiscal_str = e.fiscal_date_ending.strftime("%Y-%m-%d") if e.fiscal_date_ending else ""
        estimate_str = str(e.estimate) if e.estimate is not None else ""
        rows.append([
            e.symbol or "",
            e.name or "",
            report_str,
            fiscal_str,
            estimate_str,
            e.currency or "",
        ])
    return rows


def get_earnings(
    fetcher: Any,
    repository: Optional[EconomicCalendarEventRepository] = None,
    max_age: Optional[timedelta] = None,
) -> List[list]:
    """
    Return earnings calendar. Use DB if cache is younger than max_age; otherwise fetch from fetcher, save via repo, return.
    """
    repo = repository or EconomicCalendarEventRepository()
    max_age = max_age or ECONOMIC_CALENDAR_CACHE_MAX_AGE
    event_type = EconomicCalendarEvent.EventType.EARNINGS
    now = datetime.now(timezone.utc)
    try:
        latest = repo.get_latest_updated_at(event_type)
        if latest is not None:
            if latest.tzinfo is None:
                latest = latest.replace(tzinfo=timezone.utc)
            if now - latest <= max_age:
                events = repo.get_events(event_type)
                return _events_to_rows(events)
    except Exception:
        pass

    logger.info("Fetching earnings calendar from external API")
    try:
        rows = fetcher.get_earnings()
    except Exception as e:
        logger.warning("Failed to fetch earnings: %s", e)
        rows = []
    if isinstance(rows, list) and rows:
        repo.replace_earnings(rows)
        return rows
    if isinstance(rows, list):
        try:
            events = repo.get_events(event_type)
            if events.exists():
                return _events_to_rows(events)
        except Exception:
            pass
        return []
    return rows if isinstance(rows, list) else []


def get_ipo(
    fetcher: Any,
    repository: Optional[EconomicCalendarEventRepository] = None,
    max_age: Optional[timedelta] = None,
) -> List[list]:
    """
    Return IPO calendar. Use DB if cache is younger than max_age; otherwise fetch from fetcher, save via repo, return.
    """
    repo = repository or EconomicCalendarEventRepository()
    max_age = max_age or ECONOMIC_CALENDAR_CACHE_MAX_AGE
    event_type = EconomicCalendarEvent.EventType.IPO
    now = datetime.now(timezone.utc)
    try:
        latest = repo.get_latest_updated_at(event_type)
        if latest is not None:
            if latest.tzinfo is None:
                latest = latest.replace(tzinfo=timezone.utc)
            if now - latest <= max_age:
                events = repo.get_events(event_type)
                return _events_to_rows(events)
    except Exception:
        pass

    logger.info("Fetching IPO calendar from external API")
    try:
        rows = fetcher.get_ipo()
    except Exception as e:
        logger.warning("Failed to fetch IPO: %s", e)
        rows = []
    if isinstance(rows, list) and rows:
        repo.replace_ipo(rows)
        return rows
    if isinstance(rows, list):
        try:
            events = repo.get_events(event_type)
            if events.exists():
                return _events_to_rows(events)
        except Exception:
            pass
        return []
    return rows if isinstance(rows, list) else []
