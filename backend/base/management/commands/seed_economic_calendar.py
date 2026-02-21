"""
Seed database with sample economic calendar events (earnings and IPO) for development/testing.
"""
from datetime import date, timedelta
from decimal import Decimal

from django.core.management.base import BaseCommand

from base.models import EconomicCalendarEvent


# Sample earnings: (symbol, name, estimate, currency, days_from_today for report_date)
SAMPLE_EARNINGS = [
    ("AAPL", "Apple Inc.", 1.45, "USD", 7),
    ("MSFT", "Microsoft Corporation", 2.89, "USD", 15),
    ("GOOGL", "Alphabet Inc.", 1.65, "USD", 23),
    ("AMZN", "Amazon.com Inc.", 0.82, "USD", 31),
    ("META", "Meta Platforms Inc.", 4.25, "USD", 39),
    ("NVDA", "NVIDIA Corporation", 0.95, "USD", 47),
    ("TSLA", "Tesla Inc.", 0.72, "USD", 55),
    ("JPM", "JPMorgan Chase & Co.", 4.10, "USD", 63),
]

# Sample IPO: (symbol, name, days_from_today for report_date) – frontend calendar uses item[2] as event date
SAMPLE_IPOS = [
    ("NEWCO", "NewCo Technologies Inc.", 3),
    ("STARTUP", "Startup Ventures Ltd.", 14),
    ("TECHIPO", "Tech IPO Corp.", 24),
]


class Command(BaseCommand):
    help = "Seed database with sample economic calendar events (earnings, IPO) for dev/test."

    def add_arguments(self, parser):
        parser.add_argument(
            "--clear",
            action="store_true",
            help="Remove existing economic calendar events before seeding",
        )

    def handle(self, *args, **options):
        if options["clear"]:
            deleted, _ = EconomicCalendarEvent.objects.all().delete()
            self.stdout.write(self.style.WARNING(f"Cleared {deleted} existing events."))

        today = date.today()
        created = 0

        # Earnings: report_date = today + days_from_today
        for symbol, name, estimate, currency, days_offset in SAMPLE_EARNINGS:
            report_date = today + timedelta(days=days_offset)
            fiscal_end = report_date - timedelta(days=90)
            _, was_created = EconomicCalendarEvent.objects.update_or_create(
                event_type=EconomicCalendarEvent.EventType.EARNINGS,
                symbol=symbol,
                report_date=report_date,
                defaults={
                    "name": name,
                    "fiscal_date_ending": fiscal_end,
                    "estimate": Decimal(str(estimate)),
                    "currency": currency,
                },
            )
            if was_created:
                created += 1

        # IPO: report_date = today + days_from_today (frontend uses this as item[2])
        for symbol, name, days_offset in SAMPLE_IPOS:
            report_date = today + timedelta(days=days_offset)
            _, was_created = EconomicCalendarEvent.objects.update_or_create(
                event_type=EconomicCalendarEvent.EventType.IPO,
                symbol=symbol,
                report_date=report_date,
                defaults={"name": name},
            )
            if was_created:
                created += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Economic calendar seeded: {created} new event(s). "
                f"Total earnings: {EconomicCalendarEvent.objects.filter(event_type=EconomicCalendarEvent.EventType.EARNINGS).count()}, "
                f"IPO: {EconomicCalendarEvent.objects.filter(event_type=EconomicCalendarEvent.EventType.IPO).count()}."
            )
        )
