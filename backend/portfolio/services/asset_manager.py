"""
Asset manager for portfolio analysis and composition.
"""
from datetime import date
from typing import Callable, Dict, List, Optional, Any
from decimal import Decimal
from django.contrib.auth.models import User
from base.models import Asset
from portfolio.models import UserAsset, Transactions
from .calculators import AssetCalculator, StockCalculator, BondCalculator, CryptoCalculator
from base.services import get_default_stock_fetcher, get_default_crypto_fetcher
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
        self.stock_data_fetcher = get_default_stock_fetcher()
        self.crypto_data_fetcher = get_default_crypto_fetcher()

        # Initialize currency converter
        self.currency_converter = CurrencyConverter()

        # Initialize calculators
        self.calculators: Dict[str, AssetCalculator] = {
            'stocks': StockCalculator(self.stock_data_fetcher, self.currency_converter),
            'bonds': BondCalculator(),
            'cryptocurrencies': CryptoCalculator(self.crypto_data_fetcher, self.currency_converter),
        }

    def _get_cost_basis(self, user: User, asset: 'Asset', current_quantity: float) -> Optional[Decimal]:
        """
        Compute cost basis (total cost of current position) from transactions.
        Uses average-cost method: on SELL, cost is reduced proportionally to quantity.
        Transaction amounts in non-native currency are converted to asset native currency.

        Returns:
            Total cost in asset's native currency, or None if no transactions.
        """
        native_currency = self._get_native_currency(asset)
        txs = (
            Transactions.objects.filter(owner=user, product=asset)
            .order_by('date', 'id')
        )
        qty = Decimal('0')
        cost = Decimal('0')
        for tx in txs:
            qty_tx = Decimal(str(tx.quantity))
            price_tx = Decimal(str(tx.price)) if tx.price else Decimal('0')
            amount = qty_tx * price_tx
            tx_currency = getattr(tx, 'currency', None) or native_currency
            if tx_currency != native_currency and amount > 0:
                converted = self.currency_converter.convert(amount, tx_currency, native_currency)
                if converted is not None:
                    amount = converted
            if tx.transactionType == 'B':  # BUY
                cost += amount
                qty += qty_tx
            else:  # SELL
                if qty <= 0:
                    continue
                qty_after = qty - qty_tx
                if qty_after < 0:
                    qty_after = Decimal('0')
                if qty > 0:
                    cost = cost * (qty_after / qty)
                qty = qty_after
        if qty <= 0:
            return None
        # Scale cost to match current_quantity (in case of rounding)
        current_q = Decimal(str(current_quantity))
        if current_q <= 0:
            return None
        if qty != current_q:
            cost = cost * (current_q / qty) if qty > 0 else Decimal('0')
        return cost

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
                - 'composition_by_asset': Breakdown by individual asset (incl. cost & profit)
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

            # Cost basis and profit (in target currency)
            quantity_float = float(user_asset.quantity)
            total_cost_dec = None
            average_purchase_price = None
            if quantity_float > 0 and user_asset.average_purchase_price is not None and user_asset.currency:
                # Use stored average and currency when available
                cost_basis_stored = Decimal(str(user_asset.average_purchase_price)) * Decimal(str(quantity_float))
                if user_asset.currency != currency:
                    total_cost_dec = self.currency_converter.convert(
                        cost_basis_stored, user_asset.currency, currency,
                    )
                else:
                    total_cost_dec = cost_basis_stored
                average_purchase_price = float(user_asset.average_purchase_price)
            if total_cost_dec is None:
                # Fallback: compute from transactions
                cost_basis = self._get_cost_basis(user, asset, user_asset.quantity)
                if cost_basis is not None and cost_basis > 0:
                    native_currency = self._get_native_currency(asset)
                    if native_currency != currency:
                        total_cost_dec = self.currency_converter.convert(
                            cost_basis, native_currency, currency,
                        )
                    else:
                        total_cost_dec = cost_basis
                    if quantity_float:
                        average_purchase_price = float(cost_basis / Decimal(str(quantity_float)))
            total_cost_float = float(total_cost_dec) if total_cost_dec is not None else None
            if average_purchase_price is None and total_cost_float and quantity_float:
                average_purchase_price = total_cost_float / quantity_float
            profit = (float(current_value) - total_cost_float) if total_cost_float is not None else None
            profit_percentage = (
                (profit / total_cost_float * 100) if total_cost_float and total_cost_float > 0 and profit is not None else None
            )

            asset_info = {
                'id': asset.id,
                'symbol': asset.symbol,
                'name': asset.name,
                'asset_type': asset_type,
                'quantity': quantity_float,
                'current_value': float(current_value),
                'average_purchase_price': round(average_purchase_price, 4) if average_purchase_price is not None else None,
                'total_cost': round(total_cost_float, 2) if total_cost_float is not None else None,
                'profit': round(profit, 2) if profit is not None else None,
                'profit_percentage': round(profit_percentage, 2) if profit_percentage is not None else None,
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

    # ---- Generic position valuation (used by SnapshotService & others) ----

    def value_positions(
        self,
        positions: List[Dict[str, Any]],
        get_price: Callable[[str], Optional[Decimal]],
        valuation_date: Optional[date] = None,
        target_currency: Optional[str] = None,
    ) -> Decimal:
        """
        Calculate the total value of a list of positions.

        This is the single source of truth for "how to value a portfolio"
        regardless of *where* prices come from (live fetcher, historical
        cache, test stub, etc.).

        Args:
            positions: List of dicts, each containing:
                - 'asset': an Asset model instance
                - 'quantity': number (int / float / Decimal)
                - 'purchase_date' (optional): earliest BUY date,
                  used for bond interest-accrual calculations.
            get_price: Callable that receives a ticker symbol and returns
                       the unit price (Decimal / float) or ``None`` when
                       the price is unavailable.
            valuation_date: Date at which the portfolio is valued.
                            Defaults to date.today().  Passed through
                            to BondCalculator for interest accrual.
            target_currency: Currency to express the total value in
                (e.g. 'PLN', 'USD').  When set, each position is
                converted from its native currency to *target_currency*.
                ``None`` means no conversion (backward-compatible).

        Returns:
            Total portfolio value as Decimal.
        """
        total = Decimal('0')
        val_date = valuation_date or date.today()

        for pos in positions:
            asset = pos['asset']
            quantity = pos['quantity']
            if quantity <= 0:
                continue

            qty_dec = Decimal(str(quantity))
            asset_type = asset.asset_type
            position_value = Decimal('0')

            if asset_type in ('stocks', 'cryptocurrencies') and asset.symbol:
                price = get_price(asset.symbol)
                if price is not None:
                    if not isinstance(price, Decimal):
                        price = Decimal(str(price))
                    position_value = price * qty_dec

            elif asset_type == 'bonds':
                position_value = self._value_bond_position(
                    asset, qty_dec, pos.get('purchase_date'), val_date,
                )

            # Convert to target currency when requested
            if position_value > 0 and target_currency:
                native_currency = self._get_native_currency(asset)
                if native_currency != target_currency:
                    converted = self.currency_converter.convert(
                        position_value, native_currency, target_currency,
                    )
                    if converted is not None:
                        position_value = converted

            total += position_value

        return total

    def _value_bond_position(
        self,
        asset: 'Asset',
        quantity: Decimal,
        purchase_date: Optional[date],
        valuation_date: date,
    ) -> Decimal:
        """
        Value a single bond position using ``BondCalculator``.

        Falls back to face_value x quantity when the calculator
        cannot determine a value (missing economic data, etc.).
        """
        face_value = asset.face_value or Decimal('100')
        if not isinstance(face_value, Decimal):
            face_value = Decimal(str(face_value))
        fallback = face_value * quantity

        calculator = self._get_calculator_for_asset_type('bonds')
        if calculator is None:
            return fallback

        asset_data = {
            'face_value': face_value,
            'quantity': quantity,
            'maturity_date': asset.maturity_date,
            'bond_type': asset.bond_type,
            'interest_rate_type': asset.interest_rate_type,
            'interest_rate': asset.interest_rate,
            'wibor_margin': asset.wibor_margin,
            'inflation_margin': asset.inflation_margin,
            'base_interest_rate': asset.base_interest_rate,
            'wibor_type': '3M',
            'purchase_date': purchase_date,
        }

        value = calculator.get_current_value(
            asset_data, valuation_date=valuation_date,
        )
        return value if value is not None else fallback

    # ---- Native currency inference ----

    def _get_native_currency(self, asset: 'Asset') -> str:
        """
        Determine the native (trading) currency of an asset.

        - Bonds: always PLN (Polish Treasury Bonds).
        - Crypto: always USD (prices fetched as ``<SYM>-USD``).
        - Stocks: inferred from the exchange suffix of the symbol.
        """
        asset_type = asset.asset_type
        if asset_type == 'bonds':
            return 'PLN'
        if asset_type == 'cryptocurrencies':
            return 'USD'
        if asset_type == 'stocks' and asset.symbol:
            return self._infer_stock_currency(asset.symbol)
        return 'USD'

    @staticmethod
    def _infer_stock_currency(symbol: str) -> str:
        """
        Infer the trading currency of a stock from its exchange suffix.

        Common suffixes for Polish retail investors:
        - ``.WA`` — Warsaw Stock Exchange (PLN)
        - ``.DE``, ``.F`` — Frankfurt (EUR)
        - ``.L`` — London (GBP)
        - No suffix — US market (USD, default)
        """
        _SUFFIX_CURRENCY = {
            '.WA': 'PLN',
            '.L': 'GBP',
            '.DE': 'EUR',
            '.F': 'EUR',
            '.PA': 'EUR',
            '.AS': 'EUR',
            '.MI': 'EUR',
            '.MC': 'EUR',
            '.TO': 'CAD',
            '.AX': 'AUD',
            '.HK': 'HKD',
            '.T': 'JPY',
        }
        for suffix, currency in _SUFFIX_CURRENCY.items():
            if symbol.endswith(suffix):
                return currency
        return 'USD'

    # ---- Fallback valuation ----

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
            'cryptocurrencies': 'cryptocurrencies',
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
