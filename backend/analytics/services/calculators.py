"""
Asset calculators for computing portfolio values and metrics.
"""
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any
from decimal import Decimal
from .data_fetchers import StockDataFetcher
from .currency_converter import CurrencyConverter


class AssetCalculator(ABC):
    """
    Abstract base class for calculating asset values.
    """

    @abstractmethod
    def get_current_value(
        self,
        asset_data: Dict[str, Any],
        target_currency: Optional[str] = None
    ) -> Optional[Decimal]:
        """
        Calculate the current value of an asset.

        Args:
            asset_data: Dictionary containing asset information
                       (e.g., symbol, quantity, etc.)
            target_currency: Target currency for the value (e.g., 'USD', 'PLN').
                           If None, returns value in asset's native currency.

        Returns:
            Current value as Decimal or None if calculation fails
        """
        pass

    @abstractmethod
    def get_asset_type(self) -> str:
        """
        Get the type of asset this calculator handles.

        Returns:
            String representing the asset type
        """
        pass


class StockCalculator(AssetCalculator):
    """
    Calculator for stock assets.
    """

    def __init__(
        self,
        data_fetcher: StockDataFetcher,
        currency_converter: Optional[CurrencyConverter] = None
    ):
        self.data_fetcher = data_fetcher
        self.currency_converter = currency_converter or CurrencyConverter()

    def get_current_value(
        self,
        asset_data: Dict[str, Any],
        target_currency: Optional[str] = None
    ) -> Optional[Decimal]:
        try:
            symbol = asset_data.get('symbol')
            quantity = asset_data.get('quantity')

            if not symbol or quantity is None:
                return None

            # Convert quantity to Decimal if it's not already
            if not isinstance(quantity, Decimal):
                quantity = Decimal(str(quantity))

            # Get current price from data fetcher
            current_price = self.data_fetcher.get_current_price(symbol)

            if current_price is None:
                return None

            # Calculate total value in native currency
            total_value = current_price * quantity

            # Convert to target currency if specified
            if target_currency:
                asset_currency = self.data_fetcher.get_currency(symbol)
                
                if asset_currency and asset_currency != target_currency:
                    converted_value = self.currency_converter.convert(
                        total_value,
                        asset_currency,
                        target_currency
                    )
                    
                    if converted_value is None:
                        # If conversion fails, return None
                        return None
                    
                    total_value = converted_value

            return total_value

        except Exception as e:
            # Log error in production
            print(f"Error calculating stock value: {str(e)}")
            return None

    def get_asset_type(self) -> str:
        return 'stock'

    def get_stock_details(self, symbol: str) -> Optional[Dict[str, Any]]:
        """
        Get detailed information about a stock.

        Args:
            symbol: Stock ticker symbol

        Returns:
            Dictionary with stock information or None if not available
        """
        return self.data_fetcher.get_stock_info(symbol)
