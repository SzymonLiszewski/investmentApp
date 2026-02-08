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
from .models import Transactions, PortfolioSnapshot
from .serializers import TransactionSerializer
from .services.transaction_service import get_or_create_asset, update_user_asset
from .services.asset_manager import AssetManager
from .services.portfolio_snapshots import PortfolioSnapshotService
from .services.calculators import BondCalculator
from .services.portfolio_analysis import calculateProfit, calculateIndicators
from base.selectors.economic_data import get_latest_economic_data

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

        transaction = serializer.save(owner=self.request.user, product=asset)
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


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def profitView(request):
    """Legacy endpoint - computes short-window profit & indicators."""
    userTransactions = Transactions.objects.filter(owner=request.user)
    profit, benchmark = calculateProfit(userTransactions, None, None)
    sharpe, sortino, alpha = calculateIndicators(profit, benchmark)
    profit = profit.to_json(orient='index')
    return JsonResponse({
        'calculated_data': profit,
        'sharpe': sharpe,
        'sortino': sortino,
        'alpha': alpha,
    })


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
    start_date_str = request.query_params.get('start_date')
    end_date_str = request.query_params.get('end_date')

    if start_date_str:
        try:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
        except ValueError:
            return Response({'error': 'Invalid start_date format. Use YYYY-MM-DD'}, status=400)
    else:
        start_date = today - timedelta(days=365)

    if end_date_str:
        try:
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
        except ValueError:
            return Response({'error': 'Invalid end_date format. Use YYYY-MM-DD'}, status=400)
    else:
        end_date = today

    rebuild = request.query_params.get('rebuild', 'false').lower() == 'true'
    if rebuild:
        try:
            service = PortfolioSnapshotService(currency=currency)
            service.build_snapshots_for_user(request.user, start_date, end_date, currency=currency)
        except Exception:
            pass

    snapshots = PortfolioSnapshot.objects.filter(
        user=request.user, currency=currency,
        date__gte=start_date, date__lte=end_date,
    ).order_by('date')

    data = [
        {'date': snap.date.isoformat(), 'total_value': float(snap.total_value), 'currency': snap.currency}
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
