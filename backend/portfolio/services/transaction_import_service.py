"""
Import transactions from normalized rows produced by infrastructure parsers.

Parsers (per broker / file format) map source data into ``NormalizedTransactionImportRow``;
this module validates, resolves assets and prices, persists ``Transactions``, and updates positions.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal
from typing import List, Optional, Sequence, Tuple

from django.contrib.auth.models import User
from django.db import IntegrityError
from rest_framework import serializers

from portfolio.models import Transactions
from portfolio.services.asset_manager import AssetManager
from portfolio.services.currency_converter import CurrencyConverter
from portfolio.services.portfolio_snapshots import PortfolioSnapshotService
from portfolio.services.transaction_service import (
    get_or_create_asset,
    get_target_currency_for_user,
    resolve_price_for_date,
    update_user_asset,
)

logger = logging.getLogger(__name__)


@dataclass
class NormalizedTransactionImportRow:
    """
    Broker-agnostic row after parsing. Infrastructure adapters fill this structure.
    """

    transaction_type: str
    quantity: float
    price: Optional[float]
    trade_date: date
    source_row_index: Optional[int] = None
    currency: Optional[str] = None
    external_id: Optional[str] = None
    product_id: Optional[int] = None
    symbol: Optional[str] = None
    name: Optional[str] = None
    asset_type: Optional[str] = None
    bond_type: Optional[str] = None
    bond_series: Optional[str] = None
    maturity_date: Optional[date] = None
    interest_rate_type: Optional[str] = None
    interest_rate: Optional[Decimal] = None
    wibor_margin: Optional[Decimal] = None
    inflation_margin: Optional[Decimal] = None
    base_interest_rate: Optional[Decimal] = None
    face_value: Optional[Decimal] = None


@dataclass
class TransactionImportRowOutcome:
    source_row_index: Optional[int]
    status: str  # "created" | "skipped_duplicate" | "error"
    transaction_id: Optional[int] = None
    message: Optional[str] = None


@dataclass
class TransactionImportResult:
    outcomes: List[TransactionImportRowOutcome] = field(default_factory=list)

    @property
    def created_count(self) -> int:
        return sum(1 for o in self.outcomes if o.status == "created")


def _normalize_external_id(raw: Optional[str]) -> Optional[str]:
    if raw is None:
        return None
    s = str(raw).strip()
    return s or None


def _coerce_transaction_type(value: str) -> str:
    if value is None or (isinstance(value, str) and not value.strip()):
        raise ValueError("transaction_type is required")
    v = str(value).strip().upper()
    if v in ("B", "BUY"):
        return Transactions.transaction_type.BUY
    if v in ("S", "SELL"):
        return Transactions.transaction_type.SELL
    raise ValueError(f"Unknown transaction_type: {value!r}")


def _finalize_price_and_currency(
    user: User,
    asset,
    *,
    symbol: Optional[str],
    asset_type: Optional[str],
    trade_date: date,
    price_value: Optional[float],
    stock_fetcher=None,
    crypto_fetcher=None,
) -> Tuple[Optional[float], Optional[str]]:
    """
    Match CreateTransaction: resolve missing price for stocks/crypto, optionally convert
    to the user's snapshot currency when the price came from market data.
    """
    resolved: Optional[float] = None
    if price_value is not None:
        try:
            resolved = float(price_value)
        except (TypeError, ValueError):
            resolved = None

    resolved_from_api = False
    if (resolved is None or resolved <= 0) and symbol and asset_type in (
        "stocks",
        "cryptocurrencies",
    ):
        api_price = resolve_price_for_date(
            symbol,
            asset_type,
            trade_date,
            stock_fetcher=stock_fetcher,
            crypto_fetcher=crypto_fetcher,
        )
        if api_price is not None:
            resolved = api_price
            resolved_from_api = True

    tx_currency: Optional[str] = None
    if resolved_from_api and resolved is not None and resolved > 0:
        target_currency = get_target_currency_for_user(user)
        asset_manager = AssetManager(default_currency=target_currency)
        native_currency = asset_manager._get_native_currency(asset)
        if native_currency != target_currency:
            converter = CurrencyConverter()
            converted = converter.convert(
                Decimal(str(resolved)), native_currency, target_currency
            )
            if converted is not None:
                resolved = float(converted)
        tx_currency = target_currency

    return resolved, tx_currency


def _process_single_import_row(
    user: User,
    row: NormalizedTransactionImportRow,
    *,
    stock_fetcher=None,
    crypto_fetcher=None,
) -> TransactionImportRowOutcome:
    idx = row.source_row_index
    external_id = _normalize_external_id(row.external_id)

    try:
        tx_type = _coerce_transaction_type(row.transaction_type)
    except ValueError as e:
        return TransactionImportRowOutcome(
            source_row_index=idx, status="error", message=str(e)
        )

    if row.quantity is None or row.quantity <= 0:
        return TransactionImportRowOutcome(
            source_row_index=idx,
            status="error",
            message="quantity must be positive",
        )

    if external_id and Transactions.objects.filter(
        owner=user, external_id=external_id
    ).exists():
        return TransactionImportRowOutcome(
            source_row_index=idx,
            status="skipped_duplicate",
            message="external_id already imported",
        )

    if not (row.product_id or row.symbol or row.name):
        return TransactionImportRowOutcome(
            source_row_index=idx,
            status="error",
            message="product_id, symbol, or name is required",
        )

    try:
        asset = get_or_create_asset(
            symbol=row.symbol,
            name=row.name,
            asset_type=row.asset_type,
            product_id=row.product_id,
            bond_type=row.bond_type,
            bond_series=row.bond_series,
            maturity_date=row.maturity_date,
            interest_rate_type=row.interest_rate_type,
            interest_rate=row.interest_rate,
            wibor_margin=row.wibor_margin,
            inflation_margin=row.inflation_margin,
            base_interest_rate=row.base_interest_rate,
            face_value=row.face_value,
        )
    except serializers.ValidationError as e:
        msg = str(e.detail) if hasattr(e, "detail") else str(e)
        return TransactionImportRowOutcome(
            source_row_index=idx, status="error", message=msg
        )

    effective_asset_type = row.asset_type or asset.asset_type
    symbol_for_price = row.symbol or asset.symbol
    price_final, currency_from_resolution = _finalize_price_and_currency(
        user,
        asset,
        symbol=symbol_for_price,
        asset_type=effective_asset_type,
        trade_date=row.trade_date,
        price_value=row.price,
        stock_fetcher=stock_fetcher,
        crypto_fetcher=crypto_fetcher,
    )
    save_currency = row.currency or currency_from_resolution

    try:
        tx = Transactions.objects.create(
            owner=user,
            product=asset,
            transactionType=tx_type,
            quantity=float(row.quantity),
            price=price_final if price_final is not None else 0.0,
            date=row.trade_date,
            currency=save_currency,
            external_id=external_id,
        )
    except IntegrityError:
        return TransactionImportRowOutcome(
            source_row_index=idx,
            status="skipped_duplicate",
            message="external_id conflict",
        )

    update_user_asset(tx)
    return TransactionImportRowOutcome(
        source_row_index=idx,
        status="created",
        transaction_id=tx.id,
    )


def _rebuild_snapshots_after_import(
    user: User,
    result: TransactionImportResult,
    rows: Sequence[NormalizedTransactionImportRow],
    *,
    rebuild_snapshots: bool,
) -> None:
    if not rebuild_snapshots or result.created_count == 0:
        return
    min_trade_date: Optional[date] = None
    for row, outcome in zip(rows, result.outcomes):
        if outcome.status != "created":
            continue
        if min_trade_date is None or row.trade_date < min_trade_date:
            min_trade_date = row.trade_date
    if min_trade_date is None:
        return
    try:
        service = PortfolioSnapshotService()
        service.build_snapshots_for_user(
            user=user,
            start_date=min_trade_date,
            end_date=date.today(),
        )
    except Exception:
        logger.exception("Snapshot rebuild failed after transaction import")


def import_normalized_transactions(
    user: User,
    rows: Sequence[NormalizedTransactionImportRow],
    *,
    rebuild_snapshots: bool = True,
    stock_fetcher=None,
    crypto_fetcher=None,
) -> TransactionImportResult:
    """
    Persist normalized import rows for ``user`` in order.

    Rows with ``external_id`` already present for this user are skipped (idempotent re-import).
    """
    result = TransactionImportResult()
    for row in rows:
        result.outcomes.append(
            _process_single_import_row(
                user,
                row,
                stock_fetcher=stock_fetcher,
                crypto_fetcher=crypto_fetcher,
            )
        )
    _rebuild_snapshots_after_import(
        user, result, rows, rebuild_snapshots=rebuild_snapshots
    )
    return result
