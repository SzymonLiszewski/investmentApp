from datetime import date, datetime, timedelta

from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny

from ..services.stock_data_cache import get_stock_data_cached
from base.infrastructure.db import PriceRepository
from base.services import get_default_stock_fetcher


@api_view(['GET'])
@permission_classes([AllowAny])
def stockDataView(request, ticker):
    end_date_str = request.GET.get('end')
    start_date_str = request.GET.get('start')
    end_date = date.today()
    if end_date_str:
        try:
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
        except ValueError:
            return Response({'error': 'Invalid end date. Use YYYY-MM-DD'}, status=400)
    start_date = end_date - timedelta(days=365)
    if start_date_str:
        try:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
        except ValueError:
            return Response({'error': 'Invalid start date. Use YYYY-MM-DD'}, status=400)
    repo = PriceRepository()
    fetcher = get_default_stock_fetcher()
    prices = repo.get_price_history(ticker, start_date, end_date, fetcher)
    data = {d.isoformat(): float(v) for d, v in prices.items()}
    return Response(data)


@api_view(['GET'])
@permission_classes([AllowAny])
def basicInfoView(request, ticker):
    fetcher = get_default_stock_fetcher()
    data = get_stock_data_cached(ticker, "basic_info", fetcher)
    return Response(data)


@api_view(['GET'])
@permission_classes([AllowAny])
def fundamentalAnalysisView(request, ticker):
    fetcher = get_default_stock_fetcher()
    data = get_stock_data_cached(ticker, "fundamental_analysis", fetcher)
    return Response(data)


@api_view(['GET'])
@permission_classes([AllowAny])
def technicalAnalysisView(request, ticker):
    fetcher = get_default_stock_fetcher()
    data = get_stock_data_cached(ticker, "technical_indicators", fetcher)
    return Response(data)
