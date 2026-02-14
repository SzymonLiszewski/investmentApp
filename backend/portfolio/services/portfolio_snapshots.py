"""
Service for building and managing daily portfolio value snapshots.

Snapshots are calculated by reconstructing positions from transactions,
fetching historical prices via ``PriceRepository`` (which uses data fetchers
internally and persists to DB), and valuing the positions via ``AssetManager.value_positions``.
"""
import logging
from datetime import date, timedelta
from decimal import Decimal
from typing import Dict, List, Optional

import pandas as pd
from django.contrib.auth.models import User

from portfolio.models import PortfolioSnapshot
from portfolio.models import Transactions
from .asset_manager import AssetManager
from base.infrastructure.interfaces.market_data_fetcher import CryptoDataFetcher, StockDataFetcher
from base.infrastructure.db import PriceRepository
from base.services import get_default_stock_fetcher, get_default_crypto_fetcher

logger = logging.getLogger(__name__)


def _price_dict_to_series(prices: Dict[date, Decimal]) -> pd.Series:
    """Convert Dict[date, Decimal] from PriceRepository to pd.Series for _get_price_at_date."""
    if not prices:
        return pd.Series(dtype=float)
    s = pd.Series({d: float(v) for d, v in prices.items()})
    s.index = pd.DatetimeIndex(s.index)
    return s.sort_index()


class PortfolioSnapshotService:
    """Build and persist daily portfolio-value snapshots."""

    def __init__(
        self,
        currency: str = "PLN",
        stock_data_fetcher: Optional[StockDataFetcher] = None,
        crypto_data_fetcher: Optional[CryptoDataFetcher] = None,
        asset_manager: Optional[AssetManager] = None,
        price_repository: Optional[PriceRepository] = None,
    ):
        self.currency = currency
        self.stock_data_fetcher = stock_data_fetcher or get_default_stock_fetcher()
        self.crypto_data_fetcher = crypto_data_fetcher or get_default_crypto_fetcher()
        self.asset_manager = asset_manager or AssetManager(default_currency=currency)
        self.price_repository = price_repository if price_repository is not None else PriceRepository()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def build_snapshots_for_user(
        self,
        user: User,
        start_date: date,
        end_date: date,
        currency: Optional[str] = None,
    ) -> List[PortfolioSnapshot]:
        """
        Build daily snapshots for *user* from *start_date* to *end_date*.

        Existing snapshots in the range are overwritten (update_or_create).
        Returns the list of created/updated ``PortfolioSnapshot`` instances.
        """
        currency = currency or self.currency
        end_date = min(end_date, date.today())

        transactions = list(
            Transactions.objects.filter(owner=user, date__lte=end_date)
            .select_related("product")
            .order_by("date", "id")
        )

        if not transactions:
            return []

        # Collect tradable symbols split by asset type
        stock_symbols: List[str] = []
        crypto_symbols: List[str] = []
        for tx in transactions:
            sym = tx.product.symbol
            atype = tx.product.asset_type
            if not sym:
                continue
            if atype == "stocks" and sym not in stock_symbols:
                stock_symbols.append(sym)
            elif atype == "cryptocurrencies" and sym not in crypto_symbols:
                crypto_symbols.append(sym)

        # Fetch historical prices via dedicated fetchers
        historical_prices = self._fetch_historical_prices(
            stock_symbols, crypto_symbols, start_date, end_date,
        )

        # Running total of net cash invested (BUY adds, SELL subtracts)
        total_invested_runner = Decimal("0")
        tx_index = 0

        # Build snapshots day by day
        snapshots: List[PortfolioSnapshot] = []
        current = start_date
        while current <= end_date:
            # Include any transactions on or before this day in total_invested
            while tx_index < len(transactions) and transactions[tx_index].date <= current:
                tx = transactions[tx_index]
                amount = Decimal(str(tx.price * tx.quantity))
                from_currency = tx.currency or self.asset_manager._get_native_currency(tx.product)
                if from_currency != currency:
                    converted = self.asset_manager.currency_converter.convert(
                        amount, from_currency, currency
                    )
                    if converted is not None:
                        amount = converted
                if tx.transactionType == Transactions.transaction_type.BUY:
                    total_invested_runner += amount
                else:
                    total_invested_runner -= amount
                tx_index += 1

            positions = self._reconstruct_positions(transactions, current)

            # Build a price-getter closure for this specific date
            prices_for_date = historical_prices  # captured by ref
            snap_date = current  # captured by value

            def get_price(symbol, _d=snap_date, _p=prices_for_date):
                return self._get_price_at_date(_p.get(symbol), _d)

            total = self.asset_manager.value_positions(
                positions, get_price, valuation_date=current,
                target_currency=currency,
            )

            snap, _ = PortfolioSnapshot.objects.update_or_create(
                user=user,
                date=current,
                currency=currency,
                defaults={
                    "total_value": total,
                    "total_invested": total_invested_runner,
                },
            )
            snapshots.append(snap)
            current += timedelta(days=1)

        return snapshots

    # ------------------------------------------------------------------
    # Historical price fetching (delegates to dedicated fetchers)
    # ------------------------------------------------------------------

    def _fetch_historical_prices(
        self,
        stock_symbols: List[str],
        crypto_symbols: List[str],
        start_date: date,
        end_date: date,
    ) -> Dict[str, pd.Series]:
        """
        Fetch historical prices via PriceRepository (DB + fetcher fallback).
        Returns a dict symbol -> pd.Series (date index, close prices) for use with _get_price_at_date.
        """
        result: Dict[str, pd.Series] = {}
        repo = self.price_repository

        for symbol in stock_symbols:
            prices = repo.get_price_history(
                symbol, start_date, end_date, self.stock_data_fetcher,
            )
            result[symbol] = _price_dict_to_series(prices)

        for symbol in crypto_symbols:
            prices = repo.get_price_history(
                symbol, start_date, end_date, self.crypto_data_fetcher,
            )
            result[symbol] = _price_dict_to_series(prices)

        return result

    # ------------------------------------------------------------------
    # Position reconstruction
    # ------------------------------------------------------------------

    @staticmethod
    def _reconstruct_positions(
        transactions: list,
        target_date: date,
    ) -> List[Dict]:
        """
        Reconstruct portfolio positions at *target_date* from the
        transaction history.

        Returns a list of dicts compatible with
        ``AssetManager.value_positions``::

            {'asset': Asset, 'quantity': float, 'purchase_date': date | None}

        ``purchase_date`` is the date of the first BUY transaction for
        that asset (needed for bond interest-accrual calculations).
        """
        # product_id → [asset, qty, purchase_date]
        positions: Dict[int, list] = {}

        for tx in transactions:
            if tx.date > target_date:
                break
            pid = tx.product_id
            if pid not in positions:
                positions[pid] = [tx.product, 0.0, None]

            if tx.transactionType == "B":
                positions[pid][1] += tx.quantity
                # Record the earliest BUY date
                if positions[pid][2] is None:
                    positions[pid][2] = tx.date
            else:
                positions[pid][1] -= tx.quantity

        return [
            {"asset": asset, "quantity": qty, "purchase_date": pdate}
            for asset, qty, pdate in positions.values()
        ]

    # ------------------------------------------------------------------
    # Price lookup helper
    # ------------------------------------------------------------------

    @staticmethod
    def _get_price_at_date(
        price_series: Optional[pd.Series],
        target_date: date,
    ) -> Optional[float]:
        """Return the Close price on *target_date* or the most recent earlier price."""
        if price_series is None or price_series.empty:
            return None

        # Use date-only comparison to avoid "Invalid comparison between dtype=datetime64 and date"
        def index_as_date(i):
            return i.date() if hasattr(i, "date") else i

        index_dates = [index_as_date(i) for i in price_series.index]
        if target_date in index_dates:
            pos = index_dates.index(target_date)
            val = price_series.iloc[pos]
            if pd.notna(val):
                return float(val)

        earlier_mask = [d <= target_date for d in index_dates]
        if not any(earlier_mask):
            return None
        earlier = price_series.loc[earlier_mask]
        val = earlier.iloc[-1]
        return float(val) if pd.notna(val) else None
