"""
Seed demo user with sample transactions and generate portfolio snapshots.
Depends on: seed_demo_user (demo user exists) and asset seeds (stocks, crypto, etc.).
"""
from datetime import date, timedelta

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand

from base.models import Asset
from portfolio.models import Transactions
from portfolio.services.portfolio_snapshots import PortfolioSnapshotService
from portfolio.services.transaction_service import update_user_asset


DEMO_USERNAME = "demo"


class Command(BaseCommand):
    help = (
        "Create sample transactions for the demo user and backfill portfolio snapshots. "
        "Run after seed_demo_user and asset seeds (e.g. seed_polish_stocks, seed_crypto, seed_nasdaq_stocks)."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--skip-snapshots",
            action="store_true",
            help="Do not run snapshot backfill (only create transactions).",
        )

    def handle(self, *args, **options):
        try:
            user = User.objects.get(username=DEMO_USERNAME)
        except User.DoesNotExist:
            self.stdout.write(
                self.style.ERROR(
                    f'User "{DEMO_USERNAME}" not found. Run seed_demo_user first.'
                )
            )
            return

        if user.transactions.exists():
            if options.get("verbosity", 1) >= 2:
                self.stdout.write(
                    self.style.WARNING(
                        f'User "{DEMO_USERNAME}" already has transactions; skipping (idempotent).'
                    )
                )
            return

        stocks = list(
            Asset.objects.filter(asset_type=Asset.AssetType.STOCKS)
            .order_by("id")[:3]
        )
        cryptos = list(
            Asset.objects.filter(asset_type=Asset.AssetType.CRYPTOCURRENCIES)
            .order_by("id")[:1]
        )
        if not stocks and not cryptos:
            self.stdout.write(
                self.style.WARNING(
                    "No stocks or crypto assets found. Run asset seeds first (e.g. seed_polish_stocks, seed_crypto)."
                )
            )
            return

        today = date.today()
        txs = []

        if stocks:
            # BUY stock 1
            tx1 = Transactions.objects.create(
                owner=user,
                product=stocks[0],
                transactionType=Transactions.transaction_type.BUY,
                quantity=10.0,
                price=100.0,
                date=today - timedelta(days=30),
                currency="PLN",
            )
            update_user_asset(tx1)
            txs.append(tx1)

            # BUY more stock 1
            tx2 = Transactions.objects.create(
                owner=user,
                product=stocks[0],
                transactionType=Transactions.transaction_type.BUY,
                quantity=5.0,
                price=105.0,
                date=today - timedelta(days=20),
                currency="PLN",
            )
            update_user_asset(tx2)
            txs.append(tx2)

            # SELL some stock 1
            tx3 = Transactions.objects.create(
                owner=user,
                product=stocks[0],
                transactionType=Transactions.transaction_type.SELL,
                quantity=5.0,
                price=110.0,
                date=today - timedelta(days=10),
                currency="PLN",
            )
            update_user_asset(tx3)
            txs.append(tx3)

            if len(stocks) >= 2:
                tx4 = Transactions.objects.create(
                    owner=user,
                    product=stocks[1],
                    transactionType=Transactions.transaction_type.BUY,
                    quantity=20.0,
                    price=25.0,
                    date=today - timedelta(days=15),
                    currency="PLN",
                )
                update_user_asset(tx4)
                txs.append(tx4)

        if cryptos:
            tx_crypto = Transactions.objects.create(
                owner=user,
                product=cryptos[0],
                transactionType=Transactions.transaction_type.BUY,
                quantity=0.05,
                price=40000.0,
                date=today - timedelta(days=14),
                currency="PLN",
            )
            update_user_asset(tx_crypto)
            txs.append(tx_crypto)

        self.stdout.write(
            self.style.SUCCESS(f"Created {len(txs)} demo transaction(s) for user '{DEMO_USERNAME}'.")
        )

        if options.get("skip_snapshots"):
            return

        service = PortfolioSnapshotService(currency="PLN")
        first_date = min(t.date for t in txs)
        end_date = today
        try:
            snapshots = service.build_snapshots_for_user(
                user, first_date, end_date, currency="PLN"
            )
            self.stdout.write(
                self.style.SUCCESS(
                    f"Generated {len(snapshots)} portfolio snapshot(s) from {first_date} to {end_date}."
                )
            )
        except Exception as e:
            self.stderr.write(
                self.style.ERROR(f"Snapshot generation failed: {e}")
            )
