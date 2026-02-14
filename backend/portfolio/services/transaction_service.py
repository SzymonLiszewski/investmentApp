from datetime import date, timedelta
from typing import Optional

import pandas as pd
from rest_framework import serializers

from base.infrastructure.db import PriceRepository
from base.models import Asset
from base.serializers import AssetSerializer
from base.services import get_default_stock_fetcher, get_default_crypto_fetcher
from portfolio.models import UserAsset, PortfolioSnapshot


def get_or_create_asset(
    symbol=None,
    name=None,
    asset_type=None,
    product_id=None,
    bond_type=None,
    bond_series=None,
    maturity_date=None,
    interest_rate_type=None,
    interest_rate=None,
    wibor_margin=None,
    inflation_margin=None,
    base_interest_rate=None,
    face_value=None
):
    """Get existing asset by ID or find/create asset by symbol/name and asset_type."""
    asset = None

    if product_id:
        try:
            asset = Asset.objects.get(id=product_id)
            return asset
        except Asset.DoesNotExist:
            pass

    if not asset and (symbol or name):
        if symbol:
            asset = Asset.objects.filter(
                symbol=symbol,
                asset_type=asset_type or Asset.AssetType.STOCKS
            ).first()
        elif name:
            asset = Asset.objects.filter(
                name=name,
                asset_type=asset_type or Asset.AssetType.STOCKS
            ).first()

        if not asset:
            asset_data = {
                'name': name,
                'asset_type': asset_type or Asset.AssetType.STOCKS
            }
            if symbol:
                asset_data['symbol'] = symbol
            if asset_type == 'bonds':
                if bond_type:
                    asset_data['bond_type'] = bond_type
                if bond_series:
                    asset_data['bond_series'] = bond_series
                if maturity_date:
                    asset_data['maturity_date'] = maturity_date
                if interest_rate_type:
                    asset_data['interest_rate_type'] = interest_rate_type
                if interest_rate is not None:
                    asset_data['interest_rate'] = interest_rate
                if wibor_margin is not None:
                    asset_data['wibor_margin'] = wibor_margin
                if inflation_margin is not None:
                    asset_data['inflation_margin'] = inflation_margin
                if base_interest_rate is not None:
                    asset_data['base_interest_rate'] = base_interest_rate
                if face_value is not None:
                    asset_data['face_value'] = face_value

            asset_serializer = AssetSerializer(data=asset_data)
            if asset_serializer.is_valid():
                asset = asset_serializer.save()
            else:
                raise serializers.ValidationError({'asset': asset_serializer.errors})

    if not asset:
        raise serializers.ValidationError({
            'product': 'Asset must be provided either as product ID or asset data (symbol/name, asset_type)'
        })

    return asset


def get_target_currency_for_user(user) -> str:
    """
    Return the currency to use for this user: from the most recent snapshot,
    or default 'PLN' if they have no snapshots.
    """
    latest = (
        PortfolioSnapshot.objects.filter(user=user)
        .order_by('-date')
        .values_list('currency', flat=True)
        .first()
    )
    return latest or 'PLN'


def _get_price_at_date(
    price_series: Optional[pd.Series],
    target_date: date,
) -> Optional[float]:
    """
    Return the Close price on target_date, or the most recent earlier trading day,
    or the nearest next trading day if no earlier data exists.
    """
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
    # Prefer most recent earlier date
    earlier_mask = [d <= target_date for d in index_dates]
    if any(earlier_mask):
        earlier = price_series.loc[earlier_mask]
        val = earlier.iloc[-1]
        if pd.notna(val):
            return float(val)
    # Fallback: nearest next trading day
    later_mask = [d > target_date for d in index_dates]
    if any(later_mask):
        later = price_series.loc[later_mask]
        val = later.iloc[0]
        if pd.notna(val):
            return float(val)
    return None


# Window (calendar days) for historical fetch: before and after target_date
_PRICE_RESOLVE_DAYS_BACK = 7
_PRICE_RESOLVE_DAYS_FORWARD = 2


def resolve_price_for_date(
    symbol: str,
    asset_type: str,
    target_date: date,
    stock_fetcher=None,
    crypto_fetcher=None,
) -> Optional[float]:
    """
    Resolve missing transaction price using PriceRepository (DB + fetcher):
    closing price for the given symbol on the given date. Fetches several days
    around the date; if there is no quote on the exact day (e.g. weekend/holiday),
    uses the previous or next available trading day.
    """
    if not symbol or asset_type not in ("stocks", "cryptocurrencies"):
        return None
    stock_fetcher = stock_fetcher or get_default_stock_fetcher()
    crypto_fetcher = crypto_fetcher or get_default_crypto_fetcher()
    start_date = target_date - timedelta(days=_PRICE_RESOLVE_DAYS_BACK)
    end_date = target_date + timedelta(days=_PRICE_RESOLVE_DAYS_FORWARD)
    repo = PriceRepository()
    if asset_type == "stocks":
        prices = repo.get_price_history(symbol, start_date, end_date, stock_fetcher)
    else:
        prices = repo.get_price_history(symbol, start_date, end_date, crypto_fetcher)
    if not prices:
        return None
    series = pd.Series({d: float(v) for d, v in prices.items()})
    series.index = pd.DatetimeIndex(series.index)
    return _get_price_at_date(series, target_date)


def update_user_asset(transaction):
    """Update or create UserAsset based on transaction."""
    user_product, created = UserAsset.objects.get_or_create(
        owner=transaction.owner,
        ownedAsset=transaction.product
    )
    if created:
        user_product.quantity = transaction.quantity
    else:
        user_product.quantity += transaction.quantity
    user_product.save()
    return user_product
