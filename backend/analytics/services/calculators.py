"""
Asset calculators for computing portfolio values and metrics.
"""
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any
from decimal import Decimal
from datetime import date, datetime, timedelta
from .data_fetchers import StockDataFetcher, CryptoDataFetcher
from .currency_converter import CurrencyConverter
from analytics.selectors.economic_data import (
    get_latest_wibor,
    get_latest_inflation,
    get_inflation_for_date,
)


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


class CryptoCalculator(AssetCalculator):
    """
    Calculator for cryptocurrency assets.
    Uses CryptoDataFetcher for prices and CurrencyConverter for target currency.
    """

    def __init__(
        self,
        data_fetcher: CryptoDataFetcher,
        currency_converter: Optional[CurrencyConverter] = None
    ):
        self.data_fetcher = data_fetcher
        self.currency_converter = currency_converter or CurrencyConverter()

    def _convert_to_target_currency(
        self,
        total_value: Decimal,
        symbol: str,
        target_currency: str,
    ) -> Optional[Decimal]:
        """Convert total_value from asset currency to target_currency. Returns None if conversion fails."""
        asset_currency = self.data_fetcher.get_currency(symbol)
        if not asset_currency or asset_currency == target_currency:
            return total_value
        return self.currency_converter.convert(
            total_value,
            asset_currency,
            target_currency,
        )

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

            if not isinstance(quantity, Decimal):
                quantity = Decimal(str(quantity))

            current_price = self.data_fetcher.get_current_price(symbol)

            if current_price is None:
                return None

            total_value = current_price * quantity

            if target_currency:
                total_value = self._convert_to_target_currency(
                    total_value, symbol, target_currency
                )
                if total_value is None:
                    return None

            return total_value

        except Exception as e:
            print(f"Error calculating crypto value: {str(e)}")
            return None

    def get_asset_type(self) -> str:
        return 'cryptocurrencies'


class BondCalculator(AssetCalculator):
    """
    Calculator for bond assets (Polish Treasury Bonds).
    Supports fixed, variable (WIBOR-based), and inflation-indexed bonds.

    projected_inflation: optional forecast (in %) for inflation-indexed bonds.
    If not set latest inflation from the DB is used for simulations.
    """

    # Bond types (polish_gov_bonds_rules):
    # ROR, DOR: variable, no capitalization, simple interest (nominal + accrued from purchase)
    # TOS: fixed, annual capitalization → value = capital after last anniversary + interest YTD
    # COI, EDO, ROS, DOS: annual capitalization → value = capital after last anniversary + interest YTD

    def __init__(self, projected_inflation: Optional[Decimal] = None):
        self.projected_inflation = projected_inflation

    def _get_rate_for_year(
        self,
        year_index: int,
        anniversary_date: date,
        asset_data: Dict[str, Any],
    ) -> Optional[Decimal]:
        """Rate (in %) for a given year. Fixed bonds (e.g. TOS): same rate every year. Others: year 0 = base_interest_rate, year >= 1 = inflation + margin."""
        # Fixed-rate bonds (TOS): annual capitalization, fixed interest rate each year
        fixed_rate = asset_data.get('interest_rate')
        if fixed_rate is not None:
            return Decimal(str(fixed_rate))
        if year_index == 0:
            base = asset_data.get('base_interest_rate')
            if base is not None:
                return Decimal(str(base))
            # No base rate: use inflation + margin
        inflation_margin = asset_data.get('inflation_margin')
        if inflation_margin is None:
            return None
        inflation_margin = Decimal(str(inflation_margin))
        if self.projected_inflation is not None:
            return self.projected_inflation + inflation_margin
        inf = get_inflation_for_date(anniversary_date)
        if inf is None:
            inf = get_latest_inflation()
        if inf is None:
            return None
        return inf + inflation_margin

    def get_current_interest_rate(
        self,
        asset_data: Dict[str, Any],
        purchase_date: Optional[date] = None
    ) -> Optional[Decimal]:
        """
        Calculate the current interest rate based on bond type.

        Args:
            asset_data: Dictionary containing bond information
            purchase_date: Date when the bond was purchased (for inflation-indexed bonds)

        Returns:
            Current interest rate as Decimal or None if calculation fails
        """
        try:
            interest_rate_type = asset_data.get('interest_rate_type')
            
            if not interest_rate_type or interest_rate_type == 'fixed':
                interest_rate = asset_data.get('interest_rate')
                if interest_rate is None:
                    return None
                return Decimal(str(interest_rate))

            elif interest_rate_type == 'variable_wibor':
                # Variable rate bonds (WIBOR + margin)
                wibor_margin = asset_data.get('wibor_margin')
                if wibor_margin is None:
                    return None
                
                wibor_margin = Decimal(str(wibor_margin))
                wibor_type = asset_data.get('wibor_type', '3M')
                
                # Get current WIBOR
                current_wibor = get_latest_wibor(wibor_type)
                if current_wibor is None:
                    return None
                
                return current_wibor + wibor_margin

            elif interest_rate_type == 'indexed_inflation':
                # Inflation-indexed bonds
                inflation_margin = asset_data.get('inflation_margin')
                base_interest_rate = asset_data.get('base_interest_rate')
                
                # Use projected inflation if provided, otherwise get current
                if self.projected_inflation is not None:
                    current_inflation = self.projected_inflation
                else:
                    current_inflation = get_latest_inflation()
                
                if current_inflation is None:
                    # Fallback to base rate if inflation data not available
                    if base_interest_rate is not None:
                        return Decimal(str(base_interest_rate))
                    return None
                
                # For first period, use base rate if available
                # Otherwise use inflation + margin
                if base_interest_rate is not None and purchase_date:
                    # Check if we're still in the first period (first year)
                    today = date.today()
                    days_since_purchase = (today - purchase_date).days
                    if days_since_purchase < 365:
                        return Decimal(str(base_interest_rate))
                
                # For subsequent periods, use inflation + margin
                if inflation_margin is not None:
                    inflation_margin = Decimal(str(inflation_margin))
                    return current_inflation + inflation_margin
                
                return current_inflation

            return None

        except Exception as e:
            print(f"Error calculating interest rate: {str(e)}")
            return None

    def _get_value_annual_capitalization(
        self,
        face_value: Decimal,
        quantity: Decimal,
        purchase_date: date,
        today: date,
        full_years: int,
        total_face_value: Decimal,
        asset_data: Dict[str, Any],
    ) -> Decimal:
        """TOS, COI, EDO, ROS, DOS: capital after last anniversary + interest YTD (Actual/365, capital_annual * rate * days/365)."""
        capital = face_value
        for i in range(full_years):
            anniv = date(
                purchase_date.year + i,
                purchase_date.month,
                purchase_date.day,
            )
            rate_i = self._get_rate_for_year(i, anniv, asset_data)
            if rate_i is None:
                return total_face_value
            interest_i = capital * rate_i / Decimal('100')
            capital = capital + interest_i
        period_start = date(
            purchase_date.year + full_years,
            purchase_date.month,
            purchase_date.day,
        )
        if period_start >= today:
            return capital * quantity
        days_ytd = (today - period_start).days
        rate_current = self._get_rate_for_year(full_years, period_start, asset_data)
        if rate_current is None:
            return capital * quantity
        interest_ytd = (
            capital * rate_current * Decimal(str(days_ytd))
            / Decimal('365') / Decimal('100')
        )
        return (capital + interest_ytd) * quantity

    def _get_value_simple_interest(
        self,
        total_face_value: Decimal,
        purchase_date: date,
        today: date,
        days_since_purchase: int,
        asset_data: Dict[str, Any],
    ) -> Decimal:
        """ROR, DOR, OS, OTS: nominal + simple interest from purchase to today (no capitalization)."""
        rate = self.get_current_interest_rate(asset_data, purchase_date)
        if rate is None:
            return total_face_value
        interest_accrued = (
            total_face_value * rate * Decimal(str(days_since_purchase))
            / Decimal('365') / Decimal('100')
        )
        return total_face_value + interest_accrued

    def get_current_value(
        self,
        asset_data: Dict[str, Any],
        target_currency: Optional[str] = None,
        valuation_date: Optional[date] = None,
    ) -> Optional[Decimal]:
        """
        Calculate the value of a bond according to polish_gov_bonds_rules.

        - ROR, DOR: nominal + simple interest from purchase to valuation date (no capitalization).
        - TOS: fixed, annual capitalization — capital after last anniversary + interest YTD.
        - COI, EDO, ROS, DOS: annual capitalization — capital after last anniversary + interest YTD.

        Args:
            asset_data: Bond information dict.
            target_currency: Ignored (Polish bonds are always in PLN).
            valuation_date: Date at which the bond is valued.
                            Defaults to ``date.today()`` for backward compatibility.
        """
        try:
            face_value = asset_data.get('face_value', 100)
            quantity = asset_data.get('quantity', 0)
            maturity_date = asset_data.get('maturity_date')
            purchase_date = asset_data.get('purchase_date')
            bond_type = (asset_data.get('bond_type') or '').upper()

            if not maturity_date or quantity is None or quantity <= 0:
                return None

            if not isinstance(face_value, Decimal):
                face_value = Decimal(str(face_value))
            if not isinstance(quantity, Decimal):
                quantity = Decimal(str(quantity))

            if isinstance(maturity_date, str):
                maturity_date = datetime.strptime(maturity_date, '%Y-%m-%d').date()
            if purchase_date and isinstance(purchase_date, str):
                purchase_date = datetime.strptime(purchase_date, '%Y-%m-%d').date()

            today = valuation_date or date.today()
            total_face_value = face_value * quantity

            if maturity_date <= today:
                return total_face_value

            if not purchase_date or purchase_date >= today:
                return total_face_value

            days_since_purchase = (today - purchase_date).days
            # full_years = number of anniversaries passed (for correct YTD in capitalization)
            next_anniv = date(
                purchase_date.year + 1,
                purchase_date.month,
                purchase_date.day,
            )
            full_years = 0
            while next_anniv <= today:
                full_years += 1
                next_anniv = date(
                    next_anniv.year + 1,
                    next_anniv.month,
                    next_anniv.day,
                )

            if bond_type in ('TOS', 'COI', 'EDO', 'ROS', 'DOS'):
                return self._get_value_annual_capitalization(
                    face_value, quantity, purchase_date, today, full_years,
                    total_face_value, asset_data,
                )

            # ROR, DOR, OS, OTS, other: simple interest from purchase to today (no capitalization)
            return self._get_value_simple_interest(
                total_face_value, purchase_date, today, days_since_purchase, asset_data
            )

        except Exception as e:
            print(f"Error calculating bond value: {str(e)}")
            return None

    def calculate_yield_to_maturity(
        self,
        asset_data: Dict[str, Any],
        current_price: Decimal,
        purchase_date: Optional[date] = None
    ) -> Optional[Decimal]:
        """
        Calculate Yield to Maturity (YTM) for a bond.

        Args:
            asset_data: Dictionary containing bond information
            current_price: Current market price of the bond
            purchase_date: Date when the bond was purchased

        Returns:
            YTM as Decimal (percentage) or None if calculation fails
        """
        try:
            face_value = asset_data.get('face_value', 100)
            maturity_date = asset_data.get('maturity_date')
            
            if not maturity_date:
                return None

            if isinstance(maturity_date, str):
                maturity_date = datetime.strptime(maturity_date, '%Y-%m-%d').date()

            today = date.today()
            days_to_maturity = (maturity_date - today).days

            if days_to_maturity <= 0:
                return Decimal('0')

            # Get current interest rate
            current_interest_rate = self.get_current_interest_rate(asset_data, purchase_date)
            if current_interest_rate is None:
                return None

            # Convert to Decimal
            if not isinstance(face_value, Decimal):
                face_value = Decimal(str(face_value))
            if not isinstance(current_price, Decimal):
                current_price = Decimal(str(current_price))

            # Calculate annual interest
            annual_interest = face_value * current_interest_rate / Decimal('100')

            # Calculate capital gain/loss
            capital_gain = face_value - current_price

            # YTM = ((Annual Interest + (Capital Gain / Years to Maturity)) / Current Price) × 100
            years_to_maturity = Decimal(str(days_to_maturity)) / Decimal('365')
            if years_to_maturity <= 0:
                return Decimal('0')

            ytm = ((annual_interest + (capital_gain / years_to_maturity)) / current_price) * Decimal('100')

            return ytm

        except Exception as e:
            print(f"Error calculating YTM: {str(e)}")
            return None

    def get_asset_type(self) -> str:
        return 'bonds'
