from django.shortcuts import render
from rest_framework.response import Response
from rest_framework.decorators import api_view
from django.contrib.auth.models import User
from rest_framework import generics
from .serializers import UserSerializer, UserStockSerializer, StockSerializer, TransactionSerializer
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework import generics
from .models import UserStock, Transactions, Stock
# Create your views here.


class CreateUserView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [AllowAny]

class CreateUserStock(generics.ListCreateAPIView):
    serializer_class = UserStockSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user.id
        return UserStock.objects.filter(owner = user)
    
    def perform_create(self, serializer):
        if serializer.is_valid():
            serializer.save(owner=self.request.user)
        else:
            print(serializer.errors)

class UserStockDelete(generics.DestroyAPIView):
    serializer_class = UserStockSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        return UserStock.objects.filter(owner = user)

class StockCreate(generics.ListCreateAPIView):
    queryset = Stock.objects.all()
    serializer_class = StockSerializer
    permission_classes = [AllowAny]

    def perform_create(self, serializer):
        return super().perform_create(serializer)


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
