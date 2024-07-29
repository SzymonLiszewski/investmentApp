from django.shortcuts import render
from rest_framework.response import Response
from rest_framework.decorators import api_view
from django.contrib.auth.models import User
from rest_framework import generics
from .serializers import UserSerializer
from rest_framework.permissions import IsAuthenticated, AllowAny

# Create your views here.

class CreateUserView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [AllowAny]

@api_view(['GET', 'POST'])
def getRoutes(request):
    routes = [
        {
            'Endpoint': '/overview',
            'method' : 'GET',
            'body': None,
            'description': 'Returns overview of stock'
        },
        {
            'Endpoint': '/overview/ticker',
            'method' : 'GET',
            'body': None,
            'description': 'Returns overview of stock'
        },
        {
            'Endpoint': '/fundamental/ticker',
            'method' : 'GET',
            'body': None,
            'description': 'Returns fundamental analysis of stock'
        },
        {
            'Endpoint': '/technical/ticker',
            'method' : 'GET',
            'body': None,
            'description': 'Returns technical analysis of stock'
        },
    ]
    return Response(routes)
