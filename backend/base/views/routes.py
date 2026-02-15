from rest_framework.response import Response
from rest_framework.decorators import api_view


@api_view(['GET', 'POST'])
def getRoutes(request):
    routes = [
        {'Endpoint': '/overview', 'method': 'GET', 'body': None, 'description': 'Returns overview of stock'},
        {'Endpoint': '/overview/ticker', 'method': 'GET', 'body': None, 'description': 'Returns overview of stock'},
        {'Endpoint': '/fundamental/ticker', 'method': 'GET', 'body': None, 'description': 'Returns fundamental analysis of stock'},
        {'Endpoint': '/technical/ticker', 'method': 'GET', 'body': None, 'description': 'Returns technical analysis of stock'},
    ]
    return Response(routes)
