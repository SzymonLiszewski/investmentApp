import logging
from datetime import date, datetime, timedelta
from decimal import Decimal

from django.http import JsonResponse
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework import generics

from base.models import Asset
from base.services import get_default_stock_fetcher, get_default_crypto_fetcher
from .models import Transactions
from .selectors import get_portfolio_snapshots
from .serializers import TransactionSerializer
from .services.transaction_service import (
    get_or_create_asset,
    get_target_currency_for_user,
    update_user_asset,
    resolve_price_for_date,
)
from .services.asset_manager import AssetManager
from .services.currency_converter import CurrencyConverter
from .services.portfolio_snapshots import PortfolioSnapshotService
from .services.calculators import BondCalculator
from .services.portfolio_analysis import (
    calculateIndicators,
    get_benchmark_series,
    snapshots_to_value_series,
)
from base.selectors.economic_data import get_latest_economic_data

from .utils import parse_date

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


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def getUserAssetComposition(request):
    """Get user's portfolio composition with current values and percentages."""
    currency = request.query_params.get('currency', 'PLN')
    asset_manager = AssetManager(default_currency=currency)
    composition = asset_manager.get_portfolio_composition(
        user=request.user, target_currency=currency
    )
    return Response(composition)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def indicatorsView(request):
    """Return portfolio risk indicators (Sharpe, Sortino, Alpha) from snapshots and benchmark."""
    today = date.today()
    currency = request.query_params.get('currency', 'PLN')
    start_date, err_start = parse_date(
        request.query_params.get('start_date'),
        today - timedelta(days=365),
        'start_date',
    )
    end_date, err_end = parse_date(
        request.query_params.get('end_date'),
        today,
        'end_date',
    )
    if err_start or err_end:
        return JsonResponse({'error': err_start or err_end}, status=400)
    end_date = min(end_date, today)

    snapshots = get_portfolio_snapshots(
        request.user, currency, start_date, end_date
    )

    if not snapshots:
        return JsonResponse({
            'sharpe': -100,
            'sortino': -100,
            'alpha': -100,
        })

    portfolio_value_series, total_invested_series = snapshots_to_value_series(
        snapshots
    )

    # Convert to USD for benchmark comparison (benchmark is in USD); use historical FX per day
    if currency != 'USD':
        converter = CurrencyConverter()
        total_invested_series = converter.convert_series(
            total_invested_series, currency, 'USD', start_date, end_date
        )
        portfolio_value_series = converter.convert_series(
            portfolio_value_series, currency, 'USD', start_date, end_date
        )

    benchmark_series = get_benchmark_series(start_date, end_date)
    if benchmark_series is None or benchmark_series.empty:
        return JsonResponse({
            'sharpe': -100,
            'sortino': -100,
            'alpha': -100,
        })

    # Align benchmark to snapshot dates (benchmark has only trading days; snapshots are every calendar day)
    benchmark_series = benchmark_series.reindex(portfolio_value_series.index).ffill().bfill()

    sharpe, sortino, alpha, benchmark_profit_usd = calculateIndicators(
        portfolio_value_series, benchmark_series, total_invested_series=total_invested_series
    )

    # Convert benchmark profit from USD to user currency (today's rate) for display
    benchmark_profit_display = None
    if benchmark_profit_usd is not None:
        if currency == 'USD':
            benchmark_profit_display = float(benchmark_profit_usd)
        else:
            converter = CurrencyConverter()
            converted = converter.convert(Decimal(str(benchmark_profit_usd)), 'USD', currency)
            if converted is not None:
                benchmark_profit_display = float(converted)

    # Use -100 for missing indicators so frontend shows "No data" (IndicatorsGaugeChart convention)
    response_data = {
        'sharpe': sharpe if sharpe is not None else -100,
        'sortino': sortino if sortino is not None else -100,
        'alpha': alpha if alpha is not None else -100,
    }
    if benchmark_profit_display is not None:
        response_data['benchmark_profit'] = benchmark_profit_display
    return JsonResponse(response_data)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def updateTransactions(request):
    return JsonResponse({'status': 'OK'})


@api_view(['POST'])
@permission_classes([AllowAny])
def xtbLogin(request):
    return JsonResponse({'status': False, 'deprecated': True})


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def valueHistoryView(request):
    """Return the daily portfolio-value history based on pre-computed snapshots."""
    currency = request.query_params.get('currency', 'PLN')
    today = date.today()
    start_date, err_start = parse_date(
        request.query_params.get('start_date'),
        today - timedelta(days=365),
        'start_date',
    )
    end_date, err_end = parse_date(
        request.query_params.get('end_date'),
        today,
        'end_date',
    )
    if err_start or err_end:
        return Response({'error': err_start or err_end}, status=400)
    end_date = min(end_date, today)

    refresh_today = request.query_params.get('refresh_today', 'false').lower() == 'true'
    if refresh_today:
        try:
            service = PortfolioSnapshotService(currency=currency)
            service.build_snapshots_for_user(
                request.user, today, today, currency=currency
            )
        except Exception:
            logger.exception("Refresh today snapshot failed in valueHistoryView")

    snapshots = get_portfolio_snapshots(
        request.user, currency, start_date, end_date
    )

    data = [
        {
            'date': snap.date.isoformat(),
            'total_value': float(snap.total_value),
            'total_invested': float(snap.total_invested),
            'currency': snap.currency,
        }
        for snap in snapshots
    ]
    return Response(data)


@api_view(['POST'])
@permission_classes([AllowAny])
def calculateBondValue(request):
    """Calculate bond value assuming holding until maturity."""
    try:
        asset_id = request.data.get('asset_id')
        quantity = request.data.get('quantity')
        purchase_date_str = request.data.get('purchase_date')
        projected_inflation = request.data.get('projected_inflation')

        if not quantity:
            return Response({'error': 'Quantity is required'}, status=400)

        quantity = Decimal(str(quantity))

        purchase_date = None
        if purchase_date_str:
            try:
                purchase_date = datetime.strptime(purchase_date_str, '%Y-%m-%d').date()
            except ValueError:
                return Response({'error': 'Invalid purchase_date format. Use YYYY-MM-DD'}, status=400)
        else:
            purchase_date = date.today()

        asset_data = {}

        if asset_id:
            try:
                bond = Asset.objects.get(id=asset_id, asset_type=Asset.AssetType.BONDS)
                asset_data = {
                    'bond_type': bond.bond_type,
                    'face_value': bond.face_value or Decimal('100'),
                    'maturity_date': bond.maturity_date,
                    'interest_rate_type': bond.interest_rate_type,
                    'interest_rate': bond.interest_rate,
                    'wibor_margin': bond.wibor_margin,
                    'inflation_margin': bond.inflation_margin,
                    'base_interest_rate': bond.base_interest_rate,
                    'wibor_type': '3M',
                }
            except Asset.DoesNotExist:
                return Response({'error': 'Bond not found'}, status=404)
        else:
            maturity_date_str = request.data.get('maturity_date')
            if not maturity_date_str:
                return Response({'error': 'maturity_date is required when asset_id is not provided'}, status=400)
            try:
                maturity_date = datetime.strptime(maturity_date_str, '%Y-%m-%d').date()
            except ValueError:
                return Response({'error': 'Invalid maturity_date format. Use YYYY-MM-DD'}, status=400)
            asset_data = {
                'face_value': Decimal(str(request.data.get('face_value', 100))),
                'maturity_date': maturity_date,
                'interest_rate_type': request.data.get('interest_rate_type', 'fixed'),
                'interest_rate': Decimal(str(request.data.get('interest_rate', 0))) if request.data.get('interest_rate') else None,
                'wibor_margin': Decimal(str(request.data.get('wibor_margin'))) if request.data.get('wibor_margin') else None,
                'inflation_margin': Decimal(str(request.data.get('inflation_margin'))) if request.data.get('inflation_margin') else None,
                'base_interest_rate': Decimal(str(request.data.get('base_interest_rate'))) if request.data.get('base_interest_rate') else None,
                'wibor_type': request.data.get('wibor_type', '3M'),
            }

        asset_data['quantity'] = quantity
        asset_data['purchase_date'] = purchase_date

        projected_inflation_decimal = None
        if projected_inflation:
            projected_inflation_decimal = Decimal(str(projected_inflation))

        calculator = BondCalculator(projected_inflation=projected_inflation_decimal)
        current_interest_rate = calculator.get_current_interest_rate(asset_data, purchase_date)
        current_value = calculator.get_current_value(asset_data)

        if current_value is None:
            return Response({'error': 'Failed to calculate bond value'}, status=400)

        face_value = asset_data.get('face_value', Decimal('100'))
        total_face_value = face_value * quantity
        today = date.today()

        if purchase_date and purchase_date < today and current_interest_rate:
            days_accrued = (today - purchase_date).days
            interest_accrued = (
                total_face_value * current_interest_rate * Decimal(str(days_accrued))
                / Decimal('365') / Decimal('100')
            )
        else:
            interest_accrued = Decimal('0')

        return Response({
            'current_value': float(current_value),
            'interest_rate': float(current_interest_rate) if current_interest_rate else None,
            'interest_accrued': float(interest_accrued),
            'face_value_total': float(total_face_value),
            'quantity': float(quantity),
        })

    except Exception as e:
        return Response({'error': str(e)}, status=400)
