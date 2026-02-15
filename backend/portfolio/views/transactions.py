import logging
from datetime import date, datetime

from decimal import Decimal
from rest_framework.permissions import IsAuthenticated
from rest_framework import generics

from ..models import Transactions
from ..serializers import TransactionSerializer
from ..services.transaction_service import (
    get_or_create_asset,
    get_target_currency_for_user,
    update_user_asset,
    resolve_price_for_date,
)
from ..services.asset_manager import AssetManager
from ..services.currency_converter import CurrencyConverter
from ..services.portfolio_snapshots import PortfolioSnapshotService

logger = logging.getLogger(__name__)


class CreateTransaction(generics.ListCreateAPIView):
    serializer_class = TransactionSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user.id
        return Transactions.objects.filter(owner=user)

    def perform_create(self, serializer):
        request_data = self.request.data
        symbol = request_data.get('symbol', None)
        name = request_data.get('name', None)
        asset_type = request_data.get('asset_type', None)
        product_id = request_data.get('product', None)

        bond_type = request_data.get('bond_type', None)
        bond_series = request_data.get('bond_series', None)
        maturity_date = request_data.get('maturity_date', None)
        interest_rate_type = request_data.get('interest_rate_type', None)
        interest_rate = request_data.get('interest_rate', None)
        wibor_margin = request_data.get('wibor_margin', None)
        inflation_margin = request_data.get('inflation_margin', None)
        base_interest_rate = request_data.get('base_interest_rate', None)
        face_value = request_data.get('face_value', None)

        if maturity_date and isinstance(maturity_date, str):
            try:
                maturity_date = datetime.strptime(maturity_date, '%Y-%m-%d').date()
            except ValueError:
                pass

        asset = get_or_create_asset(
            symbol=symbol, name=name, asset_type=asset_type, product_id=product_id,
            bond_type=bond_type, bond_series=bond_series, maturity_date=maturity_date,
            interest_rate_type=interest_rate_type, interest_rate=interest_rate,
            wibor_margin=wibor_margin, inflation_margin=inflation_margin,
            base_interest_rate=base_interest_rate, face_value=face_value,
        )

        # Resolve price when user left it empty: use closing price for transaction date
        price = request_data.get('price')
        transaction_date = request_data.get('date')
        if transaction_date and isinstance(transaction_date, str):
            try:
                transaction_date = datetime.strptime(transaction_date, '%Y-%m-%d').date()
            except ValueError:
                transaction_date = None
        if transaction_date is None:
            transaction_date = date.today()

        price_value = None
        if price is not None and price != '':
            try:
                price_value = float(price)
            except (TypeError, ValueError):
                pass
        resolved_from_api = False
        if (price_value is None or price_value <= 0) and symbol and asset_type in ('stocks', 'cryptocurrencies'):
            resolved = resolve_price_for_date(symbol, asset_type, transaction_date)
            if resolved is not None:
                price_value = resolved
                resolved_from_api = True

        # When price was resolved from API, express it in user/snapshot currency
        transaction_currency = None
        if resolved_from_api and price_value is not None and price_value > 0:
            target_currency = get_target_currency_for_user(self.request.user)
            asset_manager = AssetManager(default_currency=target_currency)
            native_currency = asset_manager._get_native_currency(asset)
            if native_currency != target_currency:
                converter = CurrencyConverter()
                converted = converter.convert(Decimal(str(price_value)), native_currency, target_currency)
                if converted is not None:
                    price_value = float(converted)
            transaction_currency = target_currency

        save_kwargs = {
            'owner': self.request.user,
            'product': asset,
            'price': price_value if price_value is not None else 0.0,
        }
        if transaction_currency is not None:
            save_kwargs['currency'] = transaction_currency
        transaction = serializer.save(**save_kwargs)
        update_user_asset(transaction)

        try:
            service = PortfolioSnapshotService()
            service.build_snapshots_for_user(
                user=self.request.user,
                start_date=transaction.date,
                end_date=date.today(),
            )
        except Exception:
            logger.exception("Snapshot rebuild failed after transaction creation")
