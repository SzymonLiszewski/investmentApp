from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny

from base.services import get_default_economic_calendar_fetcher


@api_view(['GET'])
@permission_classes([AllowAny])
def CalendarEarningsView(request):
    fetcher = get_default_economic_calendar_fetcher()
    data = fetcher.get_earnings()
    return Response(data)


@api_view(['GET'])
@permission_classes([AllowAny])
def CalendarIPOView(request):
    fetcher = get_default_economic_calendar_fetcher()
    data = fetcher.get_ipo()
    return Response(data)
