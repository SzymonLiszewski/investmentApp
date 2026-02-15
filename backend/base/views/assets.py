from django.db.models import Q
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework import generics

from ..models import Asset
from ..serializers import AssetSerializer


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
    """Search for assets by symbol or name (partial match, case-insensitive)."""
    query = request.query_params.get('q', '').strip()
    asset_type = request.query_params.get('asset_type', None)
    limit = min(int(request.query_params.get('limit', 20)), 50)
    if len(query) < 2:
        return Response({'error': 'Search query must be at least 2 characters long'}, status=400)
    queryset = Asset.objects.filter(
        Q(symbol__icontains=query) | Q(name__icontains=query)
    )
    if asset_type:
        queryset = queryset.filter(asset_type=asset_type)
    queryset = queryset.order_by('symbol', 'name')[:limit]
    serializer = AssetSerializer(queryset, many=True)
    return Response(serializer.data)
