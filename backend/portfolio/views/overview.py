import logging
from datetime import date, timedelta
from decimal import Decimal

from django.http import JsonResponse
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated

from ..services.asset_manager import AssetManager
from ..services.currency_converter import CurrencyConverter
from ..services.portfolio_snapshots import PortfolioSnapshotService
from ..selectors import get_portfolio_snapshots
from ..services.portfolio_analysis import (
    calculateIndicators,
    get_benchmark_series,
    snapshots_to_value_series,
)
from ..utils import parse_date

logger = logging.getLogger(__name__)


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
            converted = converter.convert(
                Decimal(str(benchmark_profit_usd)), 'USD', currency
            )
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
