"""
Asset manager for portfolio analysis and composition.
"""
from typing import Dict, List, Optional, Any
from decimal import Decimal
from django.contrib.auth.models import User
from api.models import UserAsset, Asset, Transactions
from .calculators import AssetCalculator, StockCalculator, BondCalculator
from .data_fetchers import YfinanceStockDataFetcher
from .currency_converter import CurrencyConverter


class AssetManager:
    """
    Manager for analyzing and computing portfolio composition.
    """

    def __init__(self, default_currency: str = 'USD'):
        """
        Initialize the asset manager with default calculators.

        Args:
            default_currency: Default currency for portfolio calculations (e.g., 'USD', 'PLN')
        """
        self.default_currency = default_currency
        
        # Initialize data fetchers
        self.stock_data_fetcher = YfinanceStockDataFetcher()
        
        # Initialize currency converter
        self.currency_converter = CurrencyConverter()
        
        # Initialize calculators
        self.calculators: Dict[str, AssetCalculator] = {
            'stocks': StockCalculator(self.stock_data_fetcher, self.currency_converter),
            'bonds': BondCalculator(),
        }

    def get_portfolio_composition(
        self,
        user: User,
        target_currency: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get the composition of a user's portfolio.

        Args:
            user: Django User object
            target_currency: Currency to use for portfolio values (e.g., 'USD', 'PLN').
                           If None, uses the default currency.

        Returns:
            Dictionary containing:
                - 'total_value': Total portfolio value in target currency
                - 'currency': Currency used for values
                - 'assets': List of assets with their current values
                - 'composition_by_type': Breakdown by asset type
                - 'composition_by_asset': Breakdown by individual asset
        """
        # Use target currency or fall back to default
        currency = target_currency or self.default_currency
        # Get all user assets
        user_assets = UserAsset.objects.filter(owner=user).select_related('ownedAsset')

        assets_data = []
        total_value = Decimal('0')
        composition_by_type: Dict[str, Decimal] = {}
        composition_by_asset: List[Dict[str, Any]] = []

        for user_asset in user_assets:
            asset = user_asset.ownedAsset
            asset_type = asset.asset_type

            # Prepare asset data for calculator
            asset_data = {
                'symbol': asset.symbol,
                'quantity': user_asset.quantity,
                'name': asset.name,
                'asset_type': asset_type,
            }
            
            # Add bond-specific fields if asset is a bond
            if asset_type == 'bonds':
                first_transaction = Transactions.objects.filter(
                    owner=user,
                    product=asset
                ).order_by('date', 'id').first()
                
                purchase_date = first_transaction.date if first_transaction else None
                
                asset_data.update({
                    'bond_type': asset.bond_type,
                    'face_value': asset.face_value or Decimal('100'),
                    'maturity_date': asset.maturity_date,
                    'interest_rate_type': asset.interest_rate_type,
                    'interest_rate': asset.interest_rate,
                    'wibor_margin': asset.wibor_margin,
                    'inflation_margin': asset.inflation_margin,
                    'base_interest_rate': asset.base_interest_rate,
                    'wibor_type': '3M',  # Default
                    'purchase_date': purchase_date,
                })

            # Get appropriate calculator
            calculator = self._get_calculator_for_asset_type(asset_type)
            
            if calculator is None:
                # Skip assets without calculator
                continue

            # Calculate current value in target currency
            # Note: BondCalculator ignores target_currency (bonds are always in PLN)
            current_value = calculator.get_current_value(asset_data, currency)

            if current_value is None:
                # Skip assets that couldn't be valued
                continue

            # Update totals
            total_value += current_value

            # Update composition by type
            if asset_type not in composition_by_type:
                composition_by_type[asset_type] = Decimal('0')
            composition_by_type[asset_type] += current_value

            # Add to assets data
            asset_info = {
                'id': asset.id,
                'symbol': asset.symbol,
                'name': asset.name,
                'asset_type': asset_type,
                'quantity': float(user_asset.quantity),
                'current_value': float(current_value),
            }
            assets_data.append(asset_info)
            composition_by_asset.append(asset_info)

        # Calculate percentages
        composition_by_type_percent = {}
        if total_value > 0:
            for asset_type, value in composition_by_type.items():
                percentage = (value / total_value) * 100
                composition_by_type_percent[asset_type] = {
                    'value': float(value),
                    'percentage': float(percentage),
                }

        composition_by_asset_percent = []
        if total_value > 0:
            for asset_info in composition_by_asset:
                asset_value = Decimal(str(asset_info['current_value']))
                percentage = (asset_value / total_value) * 100
                composition_by_asset_percent.append({
                    **asset_info,
                    'percentage': float(percentage),
                })

        return {
            'total_value': float(total_value),
            'currency': currency,
            'assets': assets_data,
            'composition_by_type': composition_by_type_percent,
            'composition_by_asset': composition_by_asset_percent,
        }

    def _get_value_from_last_transaction(self, user_asset: UserAsset) -> float:
        """Fallback: value from last transaction price when calculator is unavailable."""
        try:
            last_tx = (
                Transactions.objects.filter(
                    owner=user_asset.owner,
                    product=user_asset.ownedAsset,
                )
                .order_by('-date', '-id')
                .first()
            )
            if last_tx and last_tx.price and float(last_tx.price) > 0:
                return float(last_tx.price) * float(user_asset.quantity)
        except Exception:
            pass
        return 0.0

    def get_asset_market_value(
        self,
        user_asset: UserAsset,
        target_currency: Optional[str] = None,
    ) -> float:
        """
        Calculate current market value for a single UserAsset.
        Uses the same calculators as get_portfolio_composition.
        """
        currency = target_currency or self.default_currency
        asset = user_asset.ownedAsset
        asset_type = asset.asset_type

        asset_data = {
            'symbol': asset.symbol,
            'quantity': user_asset.quantity,
            'name': asset.name,
            'asset_type': asset_type,
        }

        if asset_type == 'bonds':
            first_transaction = (
                Transactions.objects.filter(
                    owner=user_asset.owner,
                    product=asset,
                )
                .order_by('date', 'id')
                .first()
            )
            purchase_date = first_transaction.date if first_transaction else None
            asset_data.update({
                'bond_type': asset.bond_type,
                'face_value': asset.face_value or Decimal('100'),
                'maturity_date': asset.maturity_date,
                'interest_rate_type': asset.interest_rate_type,
                'interest_rate': asset.interest_rate,
                'wibor_margin': asset.wibor_margin,
                'inflation_margin': asset.inflation_margin,
                'base_interest_rate': asset.base_interest_rate,
                'wibor_type': '3M',
                'purchase_date': purchase_date,
            })

        calculator = self._get_calculator_for_asset_type(asset_type)
        if calculator is None:
            return self._get_value_from_last_transaction(user_asset)

        current_value = calculator.get_current_value(asset_data, currency)
        if current_value is None:
            return self._get_value_from_last_transaction(user_asset)

        return float(current_value)

    def _get_calculator_for_asset_type(self, asset_type: str) -> Optional[AssetCalculator]:
        """
        Get the appropriate calculator for a given asset type.

        Args:
            asset_type: Type of asset (from Asset.AssetType)

        Returns:
            AssetCalculator instance or None if not available
        """
        # Map asset types to calculator keys
        type_mapping = {
            'stocks': 'stocks',
            'bonds': 'bonds',
            # Add more mappings as needed for cryptocurrencies, etc.
        }

        calculator_key = type_mapping.get(asset_type)
        if calculator_key:
            return self.calculators.get(calculator_key)
        
        return None

    def add_calculator(self, asset_type: str, calculator: AssetCalculator) -> None:
        """
        Add or replace a calculator for a specific asset type.

        Args:
            asset_type: Type of asset
            calculator: AssetCalculator instance
        """
        self.calculators[asset_type] = calculator

    def get_calculator(self, asset_type: str) -> Optional[AssetCalculator]:
        """
        Get the calculator for a specific asset type.

        Args:
            asset_type: Type of asset

        Returns:
            AssetCalculator instance or None if not available
        """
        return self.calculators.get(asset_type)
