from rest_framework import serializers
from api.models import Asset, UserAsset
from api.serializers import AssetSerializer


def get_or_create_asset(
    symbol=None, 
    name=None, 
    asset_type=None, 
    product_id=None,
    bond_type=None,
    bond_series=None,
    maturity_date=None,
    interest_rate_type=None,
    interest_rate=None,
    wibor_margin=None,
    inflation_margin=None,
    base_interest_rate=None,
    face_value=None
):
    """
    Get existing asset by ID or find/create asset by symbol/name and asset_type.
    
    Args:
        symbol: Asset symbol (optional)
        name: Asset name (required if creating new asset)
        asset_type: Asset type (stocks, bonds, cryptocurrencies)
        product_id: Existing asset ID (optional)
        bond_type: Bond type (for bonds only)
        bond_series: Bond series (for bonds only)
        maturity_date: Maturity date (for bonds only)
        interest_rate_type: Interest rate type (for bonds only)
        interest_rate: Interest rate (for bonds only)
        wibor_margin: WIBOR margin (for variable bonds only)
        inflation_margin: Inflation margin (for inflation-indexed bonds only)
        base_interest_rate: Base interest rate (for inflation-indexed bonds only)
        face_value: Face value (for bonds only)
    
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
            
            # Add bond-specific fields if asset_type is bonds
            if asset_type == 'bonds':
                if bond_type:
                    asset_data['bond_type'] = bond_type
                if bond_series:
                    asset_data['bond_series'] = bond_series
                if maturity_date:
                    asset_data['maturity_date'] = maturity_date
                if interest_rate_type:
                    asset_data['interest_rate_type'] = interest_rate_type
                if interest_rate is not None:
                    asset_data['interest_rate'] = interest_rate
                if wibor_margin is not None:
                    asset_data['wibor_margin'] = wibor_margin
                if inflation_margin is not None:
                    asset_data['inflation_margin'] = inflation_margin
                if base_interest_rate is not None:
                    asset_data['base_interest_rate'] = base_interest_rate
                if face_value is not None:
                    asset_data['face_value'] = face_value
            
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
