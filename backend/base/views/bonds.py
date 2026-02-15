from datetime import datetime
from decimal import Decimal

from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny

from ..models import Asset, EconomicData
from ..selectors.economic_data import get_latest_economic_data


@api_view(['GET'])
@permission_classes([AllowAny])
def getBondSeries(request):
    bond_type = request.query_params.get('bond_type', None)
    queryset = Asset.objects.filter(asset_type=Asset.AssetType.BONDS)
    if bond_type:
        queryset = queryset.filter(bond_type=bond_type)
    bonds = []
    for bond in queryset:
        bonds.append({
            'id': bond.id,
            'symbol': bond.symbol,
            'name': bond.name,
            'bond_type': bond.bond_type,
            'bond_series': bond.bond_series,
            'maturity_date': bond.maturity_date.isoformat() if bond.maturity_date else None,
            'interest_rate_type': bond.interest_rate_type,
            'interest_rate': float(bond.interest_rate) if bond.interest_rate else None,
            'wibor_margin': float(bond.wibor_margin) if bond.wibor_margin else None,
            'inflation_margin': float(bond.inflation_margin) if bond.inflation_margin else None,
            'base_interest_rate': float(bond.base_interest_rate) if bond.base_interest_rate else None,
            'face_value': float(bond.face_value) if bond.face_value else 100.0,
        })
    return Response(bonds)


@api_view(['GET'])
@permission_classes([AllowAny])
def getBondSeriesByType(request, bond_type):
    queryset = Asset.objects.filter(
        asset_type=Asset.AssetType.BONDS,
        bond_type=bond_type
    )
    bonds = []
    for bond in queryset:
        bonds.append({
            'id': bond.id,
            'symbol': bond.symbol,
            'name': bond.name,
            'bond_type': bond.bond_type,
            'bond_series': bond.bond_series,
            'maturity_date': bond.maturity_date.isoformat() if bond.maturity_date else None,
            'interest_rate_type': bond.interest_rate_type,
            'interest_rate': float(bond.interest_rate) if bond.interest_rate else None,
            'wibor_margin': float(bond.wibor_margin) if bond.wibor_margin else None,
            'inflation_margin': float(bond.inflation_margin) if bond.inflation_margin else None,
            'base_interest_rate': float(bond.base_interest_rate) if bond.base_interest_rate else None,
            'face_value': float(bond.face_value) if bond.face_value else 100.0,
        })
    return Response(bonds)


@api_view(['GET', 'POST'])
@permission_classes([AllowAny])
def getEconomicData(request):
    if request.method == 'GET':
        latest = get_latest_economic_data()
        if not latest:
            return Response({'error': 'No economic data available'}, status=404)
        return Response({
            'date': latest.date.isoformat(),
            'wibor_3m': float(latest.wibor_3m),
            'wibor_6m': float(latest.wibor_6m),
            'inflation_cpi': float(latest.inflation_cpi),
        })
    elif request.method == 'POST':
        try:
            date_str = request.data.get('date')
            wibor_3m = request.data.get('wibor_3m')
            wibor_6m = request.data.get('wibor_6m')
            inflation_cpi = request.data.get('inflation_cpi')
            if not all([date_str, wibor_3m is not None, wibor_6m is not None, inflation_cpi is not None]):
                return Response({'error': 'All fields are required: date, wibor_3m, wibor_6m, inflation_cpi'}, status=400)
            try:
                date_obj = datetime.strptime(date_str, '%Y-%m-%d').date()
            except ValueError:
                return Response({'error': 'Invalid date format. Use YYYY-MM-DD'}, status=400)
            economic_data, created = EconomicData.objects.update_or_create(
                date=date_obj,
                defaults={
                    'wibor_3m': Decimal(str(wibor_3m)),
                    'wibor_6m': Decimal(str(wibor_6m)),
                    'inflation_cpi': Decimal(str(inflation_cpi)),
                }
            )
            return Response({
                'date': economic_data.date.isoformat(),
                'wibor_3m': float(economic_data.wibor_3m),
                'wibor_6m': float(economic_data.wibor_6m),
                'inflation_cpi': float(economic_data.inflation_cpi),
                'created': created,
            }, status=201 if created else 200)
        except Exception as e:
            return Response({'error': str(e)}, status=400)


@api_view(['GET'])
@permission_classes([AllowAny])
def getEconomicDataHistory(request):
    limit = min(int(request.query_params.get('limit', 50)), 200)
    start_date_str = request.query_params.get('start_date')
    end_date_str = request.query_params.get('end_date')
    queryset = EconomicData.objects.all()
    if start_date_str:
        try:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
            queryset = queryset.filter(date__gte=start_date)
        except ValueError:
            return Response({'error': 'Invalid start_date format. Use YYYY-MM-DD'}, status=400)
    if end_date_str:
        try:
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
            queryset = queryset.filter(date__lte=end_date)
        except ValueError:
            return Response({'error': 'Invalid end_date format. Use YYYY-MM-DD'}, status=400)
    data = queryset.order_by('-date')[:limit]
    history = []
    for entry in data:
        history.append({
            'date': entry.date.isoformat(),
            'wibor_3m': float(entry.wibor_3m),
            'wibor_6m': float(entry.wibor_6m),
            'inflation_cpi': float(entry.inflation_cpi),
        })
    return Response(history)
