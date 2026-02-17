import re

from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers
from .models import Asset


MIN_PASSWORD_LENGTH = 8


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "username", "password"]
        extra_kwargs = {"password": {"write_only": True}}

    def validate_password(self, value):
        if len(value) < MIN_PASSWORD_LENGTH:
            raise serializers.ValidationError(
                f"Password must be at least {MIN_PASSWORD_LENGTH} characters."
            )
        validate_password(value)
        if not re.search(r"[A-Z]", value):
            raise serializers.ValidationError(
                "Password must contain at least one uppercase letter."
            )
        if not re.search(r"[a-z]", value):
            raise serializers.ValidationError(
                "Password must contain at least one lowercase letter."
            )
        if not re.search(r"\d", value):
            raise serializers.ValidationError(
                "Password must contain at least one digit."
            )
        return value

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
        
        return data
