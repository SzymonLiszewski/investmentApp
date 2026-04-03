"""Tests for transaction_import_service (normalized row import)."""
from datetime import date
from unittest.mock import MagicMock, patch

from django.contrib.auth.models import User
from django.test import TestCase

from base.models import Asset
from portfolio.models import Transactions, UserAsset
from portfolio.services.transaction_import_service import (
    NormalizedTransactionImportRow,
    import_normalized_transactions,
)


class ImportNormalizedTransactionsTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="importer", password="x")
        self.asset = Asset.objects.create(
            symbol="TEST.WA",
            name="Test SA",
            asset_type=Asset.AssetType.STOCKS,
        )

    def test_creates_transaction_and_updates_user_asset(self):
        rows = [
            NormalizedTransactionImportRow(
                transaction_type="BUY",
                quantity=10.0,
                price=100.0,
                trade_date=date(2026, 1, 10),
                source_row_index=1,
                product_id=self.asset.id,
                currency="PLN",
            )
        ]
        with patch(
            "portfolio.services.transaction_import_service.PortfolioSnapshotService"
        ) as m_svc:
            m_svc.return_value.build_snapshots_for_user = MagicMock()
            result = import_normalized_transactions(
                self.user, rows, rebuild_snapshots=True
            )

        self.assertEqual(result.created_count, 1)
        self.assertEqual(result.outcomes[0].status, "created")
        self.assertIsNotNone(result.outcomes[0].transaction_id)

        tx = Transactions.objects.get(id=result.outcomes[0].transaction_id)
        self.assertEqual(tx.owner, self.user)
        self.assertEqual(tx.product, self.asset)
        self.assertEqual(tx.transactionType, Transactions.transaction_type.BUY)
        self.assertEqual(tx.quantity, 10.0)
        self.assertEqual(tx.price, 100.0)
        self.assertEqual(tx.currency, "PLN")

        ua = UserAsset.objects.get(owner=self.user, ownedAsset=self.asset)
        self.assertEqual(ua.quantity, 10.0)
        m_svc.return_value.build_snapshots_for_user.assert_called_once()

    def test_skips_duplicate_external_id(self):
        Transactions.objects.create(
            owner=self.user,
            product=self.asset,
            transactionType=Transactions.transaction_type.BUY,
            quantity=1,
            price=10.0,
            date=date(2026, 1, 1),
            external_id="broker-1",
        )
        rows = [
            NormalizedTransactionImportRow(
                transaction_type="B",
                quantity=5.0,
                price=20.0,
                trade_date=date(2026, 1, 2),
                external_id="broker-1",
                product_id=self.asset.id,
            )
        ]
        with patch(
            "portfolio.services.transaction_import_service.PortfolioSnapshotService"
        ) as m_svc:
            result = import_normalized_transactions(self.user, rows)

        self.assertEqual(result.created_count, 0)
        self.assertEqual(result.outcomes[0].status, "skipped_duplicate")
        self.assertEqual(Transactions.objects.filter(owner=self.user).count(), 1)
        m_svc.assert_not_called()

    def test_error_when_no_asset_reference(self):
        rows = [
            NormalizedTransactionImportRow(
                transaction_type="BUY",
                quantity=1.0,
                price=1.0,
                trade_date=date(2026, 1, 1),
            )
        ]
        result = import_normalized_transactions(
            self.user, rows, rebuild_snapshots=False
        )
        self.assertEqual(result.outcomes[0].status, "error")
        self.assertIn("product_id", result.outcomes[0].message)

    def test_error_invalid_transaction_type(self):
        rows = [
            NormalizedTransactionImportRow(
                transaction_type="HOLD",
                quantity=1.0,
                price=1.0,
                trade_date=date(2026, 1, 1),
                product_id=self.asset.id,
            )
        ]
        result = import_normalized_transactions(
            self.user, rows, rebuild_snapshots=False
        )
        self.assertEqual(result.outcomes[0].status, "error")

    def test_error_non_positive_quantity(self):
        rows = [
            NormalizedTransactionImportRow(
                transaction_type="BUY",
                quantity=0.0,
                price=1.0,
                trade_date=date(2026, 1, 1),
                product_id=self.asset.id,
            )
        ]
        result = import_normalized_transactions(
            self.user, rows, rebuild_snapshots=False
        )
        self.assertEqual(result.outcomes[0].status, "error")

    def test_resolves_price_when_missing_for_stock(self):
        rows = [
            NormalizedTransactionImportRow(
                transaction_type="B",
                quantity=2.0,
                price=None,
                trade_date=date(2026, 1, 15),
                symbol="TEST.WA",
                asset_type="stocks",
            )
        ]
        mock_fetcher = MagicMock()
        with patch(
            "portfolio.services.transaction_import_service.resolve_price_for_date",
            return_value=50.0,
        ) as m_resolve:
            with patch(
                "portfolio.services.transaction_import_service.PortfolioSnapshotService"
            ):
                with patch(
                    "portfolio.services.transaction_import_service.AssetManager"
                ) as m_am:
                    inst = m_am.return_value
                    inst._get_native_currency.return_value = "PLN"
                    result = import_normalized_transactions(
                        self.user,
                        rows,
                        stock_fetcher=mock_fetcher,
                    )

        self.assertEqual(result.created_count, 1)
        m_resolve.assert_called()
        tx = Transactions.objects.get(id=result.outcomes[0].transaction_id)
        self.assertEqual(tx.price, 50.0)

    def test_no_snapshot_rebuild_when_disabled(self):
        rows = [
            NormalizedTransactionImportRow(
                transaction_type="SELL",
                quantity=1.0,
                price=10.0,
                trade_date=date(2026, 1, 20),
                product_id=self.asset.id,
            )
        ]
        Transactions.objects.create(
            owner=self.user,
            product=self.asset,
            transactionType=Transactions.transaction_type.BUY,
            quantity=5,
            price=10.0,
            date=date(2026, 1, 1),
        )
        with patch(
            "portfolio.services.transaction_import_service.PortfolioSnapshotService"
        ) as m_svc:
            import_normalized_transactions(
                self.user, rows, rebuild_snapshots=False
            )
        m_svc.assert_not_called()
