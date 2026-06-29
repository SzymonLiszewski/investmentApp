# Tests for MockNewsFetcher / MockEconomicCalendarFetcher and their factory wiring.
import re
from datetime import datetime

from django.test import TestCase, override_settings

from base.infrastructure.db.economic_calendar_event_repository import EconomicCalendarEventRepository
from base.infrastructure.providers.mock_fetchers import (
    MockNewsFetcher,
    MockEconomicCalendarFetcher,
)
from base.models import EconomicCalendarEvent
from base.services import (
    get_default_news_fetchers,
    get_default_economic_calendar_fetcher,
)

_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


class TestMockNewsFetcher(TestCase):
    def test_returns_count_articles_with_required_keys(self):
        news = MockNewsFetcher().get_news("AAPL", count=5)
        self.assertEqual(len(news), 5)
        for article in news:
            self.assertIn("title", article)
            self.assertIn("link", article)
            self.assertIn("summary", article)
            self.assertIn("AAPL", article["title"])

    def test_deterministic_for_same_query(self):
        fetcher = MockNewsFetcher()
        self.assertEqual(fetcher.get_news("AAPL"), fetcher.get_news("AAPL"))

    def test_different_queries_differ(self):
        fetcher = MockNewsFetcher()
        self.assertNotEqual(fetcher.get_news("AAPL"), fetcher.get_news("MSFT"))


class TestMockEconomicCalendarFetcher(TestCase):
    def test_earnings_rows_have_six_columns_and_valid_dates(self):
        rows = MockEconomicCalendarFetcher().get_earnings()
        self.assertTrue(rows)
        for row in rows:
            self.assertEqual(len(row), 6)
            self.assertTrue(_DATE_RE.match(row[2]))
            # estimate parses as a number
            float(row[4])

    def test_earnings_rows_survive_replace_earnings(self):
        rows = MockEconomicCalendarFetcher().get_earnings()
        EconomicCalendarEventRepository().replace_earnings(rows)
        saved = EconomicCalendarEvent.objects.filter(
            event_type=EconomicCalendarEvent.EventType.EARNINGS
        ).count()
        self.assertEqual(saved, len(rows))

    def test_ipo_rows_have_seven_columns_and_valid_dates(self):
        rows = MockEconomicCalendarFetcher().get_ipo()
        self.assertTrue(rows)
        for row in rows:
            self.assertEqual(len(row), 7)
            # parseable ipo date
            datetime.strptime(row[2], "%Y-%m-%d")


class TestFactoryWiring(TestCase):
    @override_settings(USE_MOCK_DATA_FETCHER=True)
    def test_news_factory_returns_mock(self):
        fetchers = get_default_news_fetchers()
        self.assertEqual(len(fetchers), 1)
        self.assertIsInstance(fetchers[0], MockNewsFetcher)

    @override_settings(USE_MOCK_DATA_FETCHER=True)
    def test_calendar_factory_returns_mock(self):
        self.assertIsInstance(
            get_default_economic_calendar_fetcher(), MockEconomicCalendarFetcher
        )
