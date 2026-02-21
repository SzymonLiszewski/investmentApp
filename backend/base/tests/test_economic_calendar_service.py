# Tests for economic_calendar_service (get_earnings, get_ipo)
from datetime import datetime, timezone, timedelta
from decimal import Decimal
from unittest.mock import Mock

from django.test import TestCase

from base.models import EconomicCalendarEvent
from base.services.economic_calendar_service import get_earnings, get_ipo


class TestGetEarnings(TestCase):
    """Tests for get_earnings."""

    def test_returns_from_cache_when_fresh(self):
        """When DB has earnings events within max_age, return without calling fetcher."""
        EconomicCalendarEvent.objects.create(
            event_type=EconomicCalendarEvent.EventType.EARNINGS,
            symbol="AAPL",
            name="Apple Inc.",
            report_date=datetime.now(timezone.utc).date(),
            fiscal_date_ending=None,
            estimate=Decimal("1.50"),
            currency="USD",
        )
        fetcher = Mock()
        result = get_earnings(fetcher)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0][0], "AAPL")
        self.assertEqual(result[0][5], "USD")
        fetcher.get_earnings.assert_not_called()

    def test_fetches_and_saves_when_cache_empty(self):
        """When no earnings in DB, call fetcher, save to DB and return."""
        rows = [["SYM", "Company", "2025-03-01", "2024-12-31", "0.25", "USD"]]
        fetcher = Mock()
        fetcher.get_earnings.return_value = rows

        result = get_earnings(fetcher)

        fetcher.get_earnings.assert_called_once()
        self.assertEqual(len(result), 1)
        self.assertEqual(
            EconomicCalendarEvent.objects.filter(event_type=EconomicCalendarEvent.EventType.EARNINGS).count(), 1
        )
        ev = EconomicCalendarEvent.objects.get(event_type=EconomicCalendarEvent.EventType.EARNINGS, symbol="SYM")
        self.assertEqual(ev.name, "Company")
        self.assertEqual(ev.estimate, Decimal("0.25"))


class TestGetIPO(TestCase):
    """Tests for get_ipo."""

    def test_returns_from_cache_when_fresh(self):
        """When DB has IPO events within max_age, return without calling fetcher."""
        EconomicCalendarEvent.objects.create(
            event_type=EconomicCalendarEvent.EventType.IPO,
            symbol="IPO1",
            name="IPO One",
            report_date=datetime.now(timezone.utc).date(),
        )
        fetcher = Mock()
        result = get_ipo(fetcher)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0][0], "IPO1")
        fetcher.get_ipo.assert_not_called()

    def test_fetches_and_saves_when_cache_empty(self):
        """When no IPO in DB, call fetcher, save and return."""
        rows = [["TICK", "Tick Inc", "2025-05-15"]]
        fetcher = Mock()
        fetcher.get_ipo.return_value = rows

        result = get_ipo(fetcher)

        fetcher.get_ipo.assert_called_once()
        self.assertEqual(len(result), 1)
        self.assertEqual(
            EconomicCalendarEvent.objects.filter(event_type=EconomicCalendarEvent.EventType.IPO).count(), 1
        )
        ev = EconomicCalendarEvent.objects.get(event_type=EconomicCalendarEvent.EventType.IPO, symbol="TICK")
        self.assertEqual(ev.name, "Tick Inc")
