from django.shortcuts import render
from rest_framework.response import Response
from rest_framework.decorators import api_view
from django.contrib.auth.models import User
from rest_framework import generics, serializers
from .serializers import UserSerializer, UserAssetSerializer, AssetSerializer, TransactionSerializer
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework import generics
from .models import UserAsset, Transactions, Asset
from .services.transaction_service import get_or_create_asset, update_user_asset
# Create your views here.


class CreateUserView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [AllowAny]

class CreateUserAsset(generics.ListCreateAPIView):
    serializer_class = UserAssetSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user.id
        return UserAsset.objects.filter(owner = user)
    
    def perform_create(self, serializer):
        if serializer.is_valid():
            serializer.save(owner=self.request.user)
        else:
            print(serializer.errors)

class CreateTransaction(generics.ListCreateAPIView):
    serializer_class = TransactionSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user.id
        return Transactions.objects.filter(owner = user)
    
    def perform_create(self, serializer):
        # Get asset data from request (not from validated_data, as these are write_only fields)
        request_data = self.request.data
        symbol = request_data.get('symbol', None)
        name = request_data.get('name', None)
        asset_type = request_data.get('asset_type', None)
        product_id = request_data.get('product', None)
        
        asset = get_or_create_asset(
            symbol=symbol,
            name=name,
            asset_type=asset_type,
            product_id=product_id
        )
        
        # Create transaction with the found/created asset
        transaction = serializer.save(owner=self.request.user, product=asset)
        
        update_user_asset(transaction)

class UserAssetDelete(generics.DestroyAPIView):
    serializer_class = UserAssetSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        return UserAsset.objects.filter(owner = user)

class AssetCreate(generics.ListCreateAPIView):
    queryset = Asset.objects.all()
    serializer_class = AssetSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        queryset = Asset.objects.all()
        symbol = self.request.query_params.get('symbol', None)
        name = self.request.query_params.get('name', None)
        asset_type = self.request.query_params.get('asset_type', None)
        
        if symbol:
            queryset = queryset.filter(symbol=symbol)
        if name:
            queryset = queryset.filter(name=name)
        if asset_type:
            queryset = queryset.filter(asset_type=asset_type)
        
        return queryset

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
