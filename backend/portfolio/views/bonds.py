from datetime import date, datetime
from decimal import Decimal

from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny

from base.models import Asset
from ..services.calculators import BondCalculator


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
