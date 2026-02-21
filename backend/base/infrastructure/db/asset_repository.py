"""
Repository for asset lookup and basic info (company name from DB, market data from cache/fetcher).
"""
from typing import Any, Dict, Optional

from base.infrastructure.interfaces.asset_repository import AbstractAssetRepository
from base.models import Asset
from base.services.stock_data_service import get_stock_data


class AssetRepository(AbstractAssetRepository):
    """Resolves Asset by symbol and provides basic info with company name from DB."""

    def get_asset_by_symbol(self, symbol: str) -> Optional[Asset]:
        """Return Asset for symbol or None if not found."""
        return Asset.objects.filter(symbol=symbol).first()

    def get_basic_info(self, symbol: str, fetcher: Any) -> Dict[str, Any]:
        """
        Return basic info dict. Company Name comes from Asset if present in DB;
        Current Price, Price Change, Percent Change come from cache/fetcher.
        """
        data = get_stock_data(symbol, "basic_info", fetcher)
        if not data:
            return {}

        asset = self.get_asset_by_symbol(symbol)
        if asset is not None and asset.name:
            data = {**data, "Company Name": asset.name}

        return data
