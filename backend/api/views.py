from django.shortcuts import render
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from django.contrib.auth.models import User
from rest_framework import generics, serializers
from .serializers import UserSerializer, UserAssetSerializer, AssetSerializer, TransactionSerializer
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework import generics
from .models import UserAsset, Transactions, Asset
from .services.transaction_service import get_or_create_asset, update_user_asset
from django.db.models import Q
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


@api_view(['GET'])
@permission_classes([AllowAny])
def searchAssets(request):
    """
    Search for assets by symbol or name (partial match, case-insensitive).
    Query parameters:
    - q: search query (required, minimum 2 characters)
    - asset_type: optional filter by asset type (stocks, bonds, cryptocurrencies)
    - limit: optional limit for results (default: 20, max: 50)
    """
    query = request.query_params.get('q', '').strip()
    asset_type = request.query_params.get('asset_type', None)
    limit = min(int(request.query_params.get('limit', 20)), 50)
    
    if len(query) < 2:
        return Response({'error': 'Search query must be at least 2 characters long'}, status=400)
    
    # Build queryset with case-insensitive partial match on symbol or name
    queryset = Asset.objects.filter(
        Q(symbol__icontains=query) | Q(name__icontains=query)
    )
    
    # Filter by asset_type if provided
    if asset_type:
        queryset = queryset.filter(asset_type=asset_type)
    
    # Limit results and order by symbol for consistency
    queryset = queryset.order_by('symbol', 'name')[:limit]
    
    serializer = AssetSerializer(queryset, many=True)
    return Response(serializer.data)


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
