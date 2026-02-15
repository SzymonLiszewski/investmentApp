from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny

from base.services import get_default_news_fetchers


@api_view(['GET'])
@permission_classes([AllowAny])
def getNews(request):
    ticker = request.GET.get('ticker')
    fetchers = get_default_news_fetchers()
    news = []
    for fetcher in fetchers:
        news.extend(fetcher.get_news(ticker, count=5))
    return Response({"news": news})
