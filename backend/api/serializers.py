from django.contrib.auth.models import User
from rest_framework import serializers
from .models import Transactions, Asset
from decimal import Decimal
from datetime import datetime

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "username", "password"]
        extra_kwargs = {"password": {"write_only": True}}
    def create(self, validated_data):
        user = User.objects.create_user(**validated_data)
        return user

class AssetSerializer(serializers.ModelSerializer):
    class Meta:
        model = Asset
        fields = [
            "id", "symbol", "name", "asset_type",
            "bond_type", "bond_series", "maturity_date",
            "interest_rate", "face_value", "interest_rate_type",
            "wibor_margin", "inflation_margin", "base_interest_rate"
        ]
        extra_kwargs = {
            "symbol": {"required": False, "allow_null": True, "allow_blank": True},
            "name": {"required": True},
            "bond_type": {"required": False, "allow_null": True, "allow_blank": True},
            "bond_series": {"required": False, "allow_null": True, "allow_blank": True},
            "maturity_date": {"required": False, "allow_null": True},
            "interest_rate": {"required": False, "allow_null": True},
            "face_value": {"required": False, "allow_null": True},
            "interest_rate_type": {"required": False, "allow_null": True, "allow_blank": True},
            "wibor_margin": {"required": False, "allow_null": True},
            "inflation_margin": {"required": False, "allow_null": True},
            "base_interest_rate": {"required": False, "allow_null": True},
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
    
    # Bond-specific fields (for manual entry)
    bond_type = serializers.CharField(required=False, allow_null=True, allow_blank=True, write_only=True)
    bond_series = serializers.CharField(required=False, allow_null=True, allow_blank=True, write_only=True)
    maturity_date = serializers.DateField(required=False, allow_null=True, write_only=True)
    interest_rate_type = serializers.CharField(required=False, allow_null=True, allow_blank=True, write_only=True)
    interest_rate = serializers.DecimalField(max_digits=5, decimal_places=2, required=False, allow_null=True, write_only=True)
    wibor_margin = serializers.DecimalField(max_digits=5, decimal_places=2, required=False, allow_null=True, write_only=True)
    inflation_margin = serializers.DecimalField(max_digits=5, decimal_places=2, required=False, allow_null=True, write_only=True)
    base_interest_rate = serializers.DecimalField(max_digits=5, decimal_places=2, required=False, allow_null=True, write_only=True)
    face_value = serializers.DecimalField(max_digits=10, decimal_places=2, required=False, allow_null=True, write_only=True)
    
    class Meta:
        model = Transactions
        fields = [
            "owner", "product", "transactionType", "quantity", "price", "date", "external_id",
            "symbol", "name", "asset_type",
            "bond_type", "bond_series", "maturity_date", "interest_rate_type",
            "interest_rate", "wibor_margin", "inflation_margin", "base_interest_rate", "face_value"
        ]
        extra_kwargs = {
            "owner": {"read_only": True},
            "price": {"required": False},
            "external_id": {"required": False},
            "product": {"required": False}
        }
    
    def validate(self, data):
        asset_type = data.get('asset_type')
        
        # Validate bond fields if asset_type is bonds
        if asset_type == 'bonds':
            interest_rate_type = data.get('interest_rate_type')
            
            if interest_rate_type == 'fixed':
                if not data.get('interest_rate'):
                    raise serializers.ValidationError({
                        'interest_rate': 'Interest rate is required for fixed rate bonds'
                    })
            elif interest_rate_type == 'variable_wibor':
                if data.get('wibor_margin') is None:
                    raise serializers.ValidationError({
                        'wibor_margin': 'WIBOR margin is required for variable rate bonds'
                    })
            elif interest_rate_type == 'indexed_inflation':
                if data.get('inflation_margin') is None:
                    raise serializers.ValidationError({
                        'inflation_margin': 'Inflation margin is required for inflation-indexed bonds'
                    })
        
        return data
    
    def create(self, validated_data):
        # Remove write_only fields that don't belong to Transactions model
        validated_data.pop('symbol', None)
        validated_data.pop('name', None)
        validated_data.pop('asset_type', None)
        validated_data.pop('bond_type', None)
        validated_data.pop('bond_series', None)
        validated_data.pop('maturity_date', None)
        validated_data.pop('interest_rate_type', None)
        validated_data.pop('interest_rate', None)
        validated_data.pop('wibor_margin', None)
        validated_data.pop('inflation_margin', None)
        validated_data.pop('base_interest_rate', None)
        validated_data.pop('face_value', None)
        
        # Create and return the transaction
        return Transactions.objects.create(**validated_data)