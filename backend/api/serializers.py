from django.contrib.auth.models import User
from rest_framework import serializers
from .models import UserAsset, Transactions, Asset
from utils.dataFetcher import getBasicStockInfo

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "username", "password"]
        extra_kwargs = {"password": {"write_only": True}}
    def create(self, validated_data):
        user = User.objects.create_user(**validated_data)
        return user
    
class UserAssetSerializer(serializers.ModelSerializer):
    name = serializers.CharField(source='ownedAsset.name', read_only=True)
    market_value = serializers.SerializerMethodField(read_only=True)
    
    class Meta:
        model = UserAsset
        fields = ["name", "quantity", "market_value", "ownedAsset"]
        extra_kwargs = {
            "ownedAsset": {"write_only": True},
        }
    
    def get_market_value(self, obj):
        """
        Calculate market value (current price * quantity) for the asset.
        For STOCKS: fetch current price from yfinance using getBasicStockInfo.
        For other types (BONDS, CRYPTOCURRENCIES): use last transaction price.
        TODO: Add dynamic price fetching for bonds and cryptocurrencies in the future.
        """
        try:
            asset = obj.ownedAsset
            quantity = obj.quantity
            
            # For STOCKS, fetch current price from yfinance
            if asset.asset_type == Asset.AssetType.STOCKS:
                #For stocks without symbol, use last transaction price
                if not asset.symbol:
                    return self._get_market_value_from_last_transaction(obj, quantity)
                
                # Main logic: For stocks with symbol, fetch current price from yfinance
                try:
                    basic_info = getBasicStockInfo(asset.symbol)
                    current_price = basic_info.get('Current Price', 0)
                    
                    # Handle 'N/A' or None values
                    if current_price == 'N/A' or current_price is None:
                        return 0.0
                    
                    return float(current_price) * float(quantity)
                except Exception as e:
                    return self._get_market_value_from_last_transaction(obj, quantity)
            else:
                # TODO: Add dynamic price fetching for bonds and cryptocurrencies, when adding that create separate method for different types instead if-else
                return self._get_market_value_from_last_transaction(obj, quantity)
        except Exception as e:
            return 0.0
    
    def _get_market_value_from_last_transaction(self, obj, quantity):
        """
        Get market value using the last transaction price for this asset and user.
        """
        try:
            last_transaction = Transactions.objects.filter(
                owner=obj.owner,
                product=obj.ownedAsset
            ).order_by('-date', '-id').first()
            
            if last_transaction and last_transaction.price > 0:
                return float(last_transaction.price) * float(quantity)
            else:
                return 0.0
        except Exception:
            return 0.0
    
class AssetSerializer(serializers.ModelSerializer):
    class Meta:
        model = Asset
        fields = ["id", "symbol", "name", "asset_type"]
        extra_kwargs = {
            "symbol": {"required": False, "allow_null": True, "allow_blank": True},
            "name": {"required": True},
        }
    
    def validate(self, data):
        asset_type = data.get('asset_type', Asset.AssetType.STOCKS)
        
        if asset_type == Asset.AssetType.STOCKS:
            if not data.get('symbol'):
                raise serializers.ValidationError({'symbol': 'Symbol is required for stocks'})
        
        # Bonds and cryptocurrencies can have optional symbol
        
        return data

class TransactionSerializer(serializers.ModelSerializer):
    # Optional fields for creating asset if it doesn't exist
    symbol = serializers.CharField(required=False, allow_null=True, allow_blank=True, write_only=True)
    name = serializers.CharField(required=False, allow_null=True, allow_blank=True, write_only=True)
    asset_type = serializers.CharField(required=False, write_only=True)
    
    class Meta:
        model = Transactions
        fields = ["owner", "product", "transactionType", "quantity", "price", "date", "external_id", "symbol", "name", "asset_type"]
        extra_kwargs = {"owner": {"read_only": True}, "price": {"required": False}, "external_id": {"required": False}, "product": {"required": False}}
    
    def create(self, validated_data):
        # Remove write_only fields that don't belong to Transactions model
        validated_data.pop('symbol', None)
        validated_data.pop('name', None)
        validated_data.pop('asset_type', None)
        
        # Create and return the transaction
        return Transactions.objects.create(**validated_data)