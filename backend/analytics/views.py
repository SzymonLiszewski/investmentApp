from django.shortcuts import render, get_object_or_404
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from utils.dataFetcher import getStockPrice, getFundamentalAnalysis, getBasicStockInfo
from analytics.predictions import linear_regression_predict
from analytics.technical_indicators import get_technical_indicators
from analytics.portfolioAnalysis import calculateProfit, calculateIndicators
from utils.economicCalendar import getEarnings, getIPO
from rest_framework.permissions import IsAuthenticated, AllowAny
from api.models import Transactions, UserAsset
from django.http import JsonResponse
from utils.xtb_integration import getTransactions_xtb, login_to_xtb
from api.serializers import TransactionSerializer
from utils.news import getAllNews
from analytics.services.asset_manager import AssetManager
from api.models import Asset
from analytics.models import EconomicData
from analytics.selectors.economic_data import get_latest_economic_data
from analytics.services.calculators import BondCalculator
from rest_framework import serializers
from decimal import Decimal
from datetime import date, datetime
# Create your views here.

#* Analysis views


@api_view(['GET'])
@permission_classes([AllowAny])
def stockDataView(request, ticker):
    start_date = request.GET.get('start')
    end_date = request.GET.get('end')
    data = getStockPrice(ticker, start_date, end_date)
    return Response(data)


@api_view(['GET'])
@permission_classes([AllowAny])
def predictView(request, ticker):
    start_date = request.GET.get('start')
    end_date = request.GET.get('end')
    data = getStockPrice(ticker, start_date, end_date)
    prediction = linear_regression_predict(ticker, start_date, end_date)
    return Response(data | prediction)

@api_view(['GET'])
@permission_classes([AllowAny])
def fundamentalAnalysisView(request, ticker):
    data = getFundamentalAnalysis(ticker)
    return Response(data)

@api_view(['GET'])
@permission_classes([AllowAny])
def basicInfoView(request, ticker):
    data = getBasicStockInfo(ticker)
    return Response(data)

@api_view(['GET'])
@permission_classes([AllowAny])
def technicalAnalysisView(request, ticker):
    data = get_technical_indicators(ticker)
    return Response(data)

#* Calendar views

@api_view(['GET'])
@permission_classes([AllowAny])
def CalendarEarningsView(request):
    data = getEarnings()
    return Response(data)

@api_view(['GET'])
@permission_classes([AllowAny])
def CalendarIPOView(request):
    data = getIPO()
    return Response(data)

#* portfolio analysis views

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def profitView(request):
    userTransactions = Transactions.objects.filter(owner = request.user)
    userId = request.headers.get("userId")
    password = request.headers.get("password")
    profit, benchmark = calculateProfit(userTransactions, userId, password)
    sharpe, sortino, alpha = calculateIndicators(profit, benchmark)
    profit = profit.to_json(orient='index')
    return JsonResponse({'calculated_data': profit, 'sharpe': sharpe, 'sortino': sortino, 'alpha': alpha})

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def updateTransactions(request):
    userId = request.headers.get("userId")
    password = request.headers.get("password")
    xtb_transactions = getTransactions_xtb(userId, password)
    if xtb_transactions!=None:
        for i in xtb_transactions:
            if i != {}:
                #* add transaction if it does not exists in database
                isTransactionCreated = Transactions.objects.filter(external_id=i['order']).first()
                if isTransactionCreated==None:
                    serializer = TransactionSerializer(data={'product': i['symbol'], 'transactionType': "B", 'quantity': i['volume'], 'price': i['open_price'], 'date': i['date'], 'external_id': i['order']})
                    if serializer.is_valid():
                        transaction = serializer.save(owner=request.user)
                        #* if USER_ASSET does not exits in db create new object, otherwise add value of owned shares
                        user_product, created = UserAsset.objects.get_or_create(
                            owner=transaction.owner,
                            ownedAsset=transaction.product
                        )
                        if created:
                            user_product.quantity = transaction.quantity
                        else:
                            user_product.quantity += transaction.quantity
                        user_product.save()
                    else:
                        print(serializer.errors)
    return JsonResponse({'status': 'OK'})

@api_view(['POST'])
@permission_classes([AllowAny])
def xtbLogin(request):
    userId = request.headers.get("userId")
    password = request.headers.get("password")
    response = login_to_xtb(userId, password)
    return JsonResponse({'status': response})

@api_view(['GET'])
@permission_classes([AllowAny])
def getNews(request):
    data = getAllNews(request.GET.get('ticker'),5)
    return Response(data)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def getUserAssetComposition(request):
    """
    Get user's portfolio composition with current values and percentages.
    
    Query parameters:
    - currency: Target currency for values (e.g., 'USD', 'PLN'). Defaults to 'PLN'.
    
    Returns:
    - total_value: Total portfolio value in target currency
    - currency: Currency used for values
    - assets: List of assets with their current values
    - composition_by_type: Breakdown by asset type (stocks, bonds, etc.)
    - composition_by_asset: Breakdown by individual asset with percentages
    """
    # Get currency from query params or use PLN as default
    currency = request.query_params.get('currency', 'PLN')
    
    # Create AssetManager with user's preferred currency
    asset_manager = AssetManager(default_currency=currency)
    
    # Get portfolio composition
    composition = asset_manager.get_portfolio_composition(
        user=request.user,
        target_currency=currency
    )
    
    return Response(composition)

#* Bond endpoints

@api_view(['GET'])
@permission_classes([AllowAny])
def getBondSeries(request):
    """
    Get list of available bond series, optionally filtered by bond type.
    
    Query parameters:
    - bond_type: Optional filter by bond type (OS, OTS, EDO, ROR, DOR, etc.)
    
    Returns:
    - List of bond series with their details
    """
    bond_type = request.query_params.get('bond_type', None)
    
    queryset = Asset.objects.filter(asset_type=Asset.AssetType.BONDS)
    
    if bond_type:
        queryset = queryset.filter(bond_type=bond_type)
    
    bonds = []
    for bond in queryset:
        bond_data = {
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
        }
        bonds.append(bond_data)
    
    return Response(bonds)

@api_view(['GET'])
@permission_classes([AllowAny])
def getBondSeriesByType(request, bond_type):
    """
    Get bond series for a specific bond type.
    
    Returns:
    - List of bond series for the specified type
    """
    queryset = Asset.objects.filter(
        asset_type=Asset.AssetType.BONDS,
        bond_type=bond_type
    )
    
    bonds = []
    for bond in queryset:
        bond_data = {
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
        }
        bonds.append(bond_data)
    
    return Response(bonds)

@api_view(['POST'])
@permission_classes([AllowAny])
def calculateBondValue(request):
    """
    Calculate bond value assuming holding until maturity.
    
    Request body:
    - asset_id: ID of the bond asset (optional if manual data provided)
    - quantity: Number of bonds
    - purchase_date: Date when bonds were purchased (optional, defaults to today)
    - projected_inflation: Projected inflation rate for simulation (optional)
    - Manual bond data (if asset_id not provided):
      - bond_type, bond_series, maturity_date, interest_rate_type, etc.
    
    Returns:
    - current_value: Calculated current value
    - interest_rate: Current interest rate used
    - interest_accrued: Interest accrued until maturity
    - face_value_total: Total face value
    """
    try:
        asset_id = request.data.get('asset_id')
        quantity = request.data.get('quantity')
        purchase_date_str = request.data.get('purchase_date')
        projected_inflation = request.data.get('projected_inflation')
        
        if not quantity:
            return Response({'error': 'Quantity is required'}, status=400)
        
        quantity = Decimal(str(quantity))
        
        # Parse purchase date
        purchase_date = None
        if purchase_date_str:
            try:
                purchase_date = datetime.strptime(purchase_date_str, '%Y-%m-%d').date()
            except ValueError:
                return Response({'error': 'Invalid purchase_date format. Use YYYY-MM-DD'}, status=400)
        else:
            purchase_date = date.today()
        
        # Get bond data
        asset_data = {}
        
        if asset_id:
            # Get from database
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
                    'wibor_type': '3M',  # Default
                }
            except Asset.DoesNotExist:
                return Response({'error': 'Bond not found'}, status=404)
        else:
            # Manual data
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
        
        # Create calculator
        projected_inflation_decimal = None
        if projected_inflation:
            projected_inflation_decimal = Decimal(str(projected_inflation))
        
        calculator = BondCalculator(projected_inflation=projected_inflation_decimal)
        
        # Calculate current interest rate
        current_interest_rate = calculator.get_current_interest_rate(asset_data, purchase_date)
        
        # Calculate value
        current_value = calculator.get_current_value(asset_data)
        
        if current_value is None:
            return Response({'error': 'Failed to calculate bond value'}, status=400)
        
        # Breakdown: interest accrued so far (from purchase to today)
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

@api_view(['GET', 'POST'])
@permission_classes([AllowAny])
def getEconomicData(request):
    """
    Get or create economic data (WIBOR rates and inflation).
    
    GET: Returns current economic data
    POST: Creates new economic data entry (requires authentication for production)
    """
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
        # In production, this should require authentication
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
    """
    Get historical economic data.
    
    Query parameters:
    - limit: Number of records to return (default: 50, max: 200)
    - start_date: Start date filter (YYYY-MM-DD)
    - end_date: End date filter (YYYY-MM-DD)
    """
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