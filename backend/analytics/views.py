from datetime import date, datetime, timedelta

from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny

from .selectors.forecasts import get_stored_sarima_forecast
from .services.predictions import sarima_forecast
from .services.regression_model import predict_with_regression
from .services.sentiment import analyze_sentiment
from base.infrastructure.db import PriceRepository
from base.services import get_default_stock_fetcher, get_default_news_fetchers


@api_view(['GET'])
@permission_classes([AllowAny])
def predictView(request, ticker):
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
    model = request.GET.get('model', 'regression')
    if model not in ('regression', 'sarima'):
        return Response({'error': "Invalid model. Use 'regression' or 'sarima'"}, status=400)

    repo = PriceRepository()
    fetcher = get_default_stock_fetcher()
    prices = repo.get_price_history(ticker, start_date, end_date, fetcher)
    data = {d.isoformat(): float(v) for d, v in prices.items()}

    if model == 'sarima':
        forecast = get_stored_sarima_forecast(ticker)
        source = 'precomputed'
        if forecast is None:
            try:
                forecast = sarima_forecast(ticker, start_date.isoformat(), end_date.isoformat())
            except ValueError as exc:
                return Response({'error': str(exc)}, status=400)
            source = 'on_demand'
        return Response({'history': data, 'forecast': forecast, 'source': source})

    try:
        prediction = predict_with_regression(
            ticker, start_date.isoformat(), end_date.isoformat()
        )
    except ValueError as exc:
        return Response({'error': str(exc)}, status=400)
    return Response(data | prediction)


@api_view(['GET'])
@permission_classes([AllowAny])
def newsWithSentimentView(request):
    """Return news articles with sentiment analysis score."""
    ticker = request.GET.get('ticker')
    fetchers = get_default_news_fetchers()
    news = []
    for fetcher in fetchers:
        news.extend(fetcher.get_news(ticker, count=5))
    sentiment = analyze_sentiment(news)
    return Response({"sentiment": sentiment, "news": news})
