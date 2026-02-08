"""
Management command to generate daily portfolio-value snapshots.
"""
from datetime import date, timedelta

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand

from portfolio.services.portfolio_snapshots import PortfolioSnapshotService


class Command(BaseCommand):
    help = "Generate daily portfolio value snapshots for all users with transactions."

    def add_arguments(self, parser):
        parser.add_argument(
            "--date", type=str, default=None,
            help="Target date (YYYY-MM-DD). Defaults to yesterday.",
        )
        parser.add_argument(
            "--backfill", action="store_true",
            help="Backfill from each user's first transaction to today.",
        )
        parser.add_argument(
            "--currency", type=str, default="PLN",
            help="Currency for snapshot values (default: PLN).",
        )

    def handle(self, *args, **options):
        target_date_str = options["date"]
        backfill = options["backfill"]
        currency = options["currency"]

        if target_date_str:
            target_date = date.fromisoformat(target_date_str)
        else:
            target_date = date.today() - timedelta(days=1)

        service = PortfolioSnapshotService(currency=currency)
        users = User.objects.filter(transactions__isnull=False).distinct()
        total_snapshots = 0

        for user in users:
            if backfill:
                first_tx = user.transactions.order_by("date").first()
                if not first_tx:
                    continue
                start = first_tx.date
                end = date.today()
            else:
                start = target_date
                end = target_date

            self.stdout.write(
                f"Generating snapshots for {user.username} ({start} -> {end})"
            )
            try:
                snapshots = service.build_snapshots_for_user(
                    user, start, end, currency=currency,
                )
                total_snapshots += len(snapshots)
                self.stdout.write(f"  Done: {len(snapshots)} snapshot(s)")
            except Exception as exc:
                self.stderr.write(self.style.ERROR(f"  Error: {exc}"))

        self.stdout.write(
            self.style.SUCCESS(f"Done - {total_snapshots} snapshot(s) created/updated.")
        )
