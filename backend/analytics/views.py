from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny

from .services.predictions import linear_regression_predict
from .services.sentiment import analyze_sentiment
from base.services import get_default_stock_fetcher, get_default_news_fetchers


@api_view(['GET'])
@permission_classes([AllowAny])
def predictView(request, ticker):
    start_date = request.GET.get('start')
    end_date = request.GET.get('end')
    fetcher = get_default_stock_fetcher()
    data = fetcher.get_stock_price_history(ticker, start_date, end_date)
    prediction = linear_regression_predict(ticker, start_date, end_date)
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
