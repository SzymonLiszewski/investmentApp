from rest_framework import serializers
from api.models import Asset, UserAsset
from api.serializers import AssetSerializer


def get_or_create_asset(symbol=None, name=None, asset_type=None, product_id=None):
    """
    Get existing asset by ID or find/create asset by symbol/name and asset_type.
    
    Args:
        symbol: Asset symbol (optional)
        name: Asset name (required if creating new asset)
        asset_type: Asset type (stocks, bonds, cryptocurrencies)
        product_id: Existing asset ID (optional)
    
    Returns:
        Asset instance
    
    Raises:
        serializers.ValidationError: If asset cannot be found or created
    """
    asset = None
    
    # If product ID is provided, use it
    if product_id:
        try:
            asset = Asset.objects.get(id=product_id)
            return asset
        except Asset.DoesNotExist:
            pass
    
    # If asset not found by ID and asset data is provided, find or create asset
    if not asset and (symbol or name):
        # Try to find existing asset
        if symbol:
            asset = Asset.objects.filter(
                symbol=symbol, 
                asset_type=asset_type or Asset.AssetType.STOCKS
            ).first()
        elif name:
            asset = Asset.objects.filter(
                name=name, 
                asset_type=asset_type or Asset.AssetType.STOCKS
            ).first()
        
        # If asset doesn't exist, create it
        if not asset:
            asset_data = {
                'name': name,
                'asset_type': asset_type or Asset.AssetType.STOCKS
            }
            if symbol:
                asset_data['symbol'] = symbol
            
            asset_serializer = AssetSerializer(data=asset_data)
            if asset_serializer.is_valid():
                asset = asset_serializer.save()
            else:
                raise serializers.ValidationError({'asset': asset_serializer.errors})
    
    if not asset:
        raise serializers.ValidationError({
            'product': 'Asset must be provided either as product ID or asset data (symbol/name, asset_type)'
        })
    
    return asset


def update_user_asset(transaction):
    """
    Update or create UserAsset based on transaction.
    
    Args:
        transaction: Transaction instance
    
    Returns:
        UserAsset instance
    """
    user_product, created = UserAsset.objects.get_or_create(
        owner=transaction.owner,
        ownedAsset=transaction.product
    )
    
    if created:
        user_product.quantity = transaction.quantity
    else:
        user_product.quantity += transaction.quantity
    
    user_product.save()
    return user_product
