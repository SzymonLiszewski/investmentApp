from rest_framework import serializers
from .models import Transactions
from base.models import Asset
from decimal import Decimal


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
            "owner", "product", "transactionType", "quantity", "price", "date", "currency", "external_id",
            "symbol", "name", "asset_type",
            "bond_type", "bond_series", "maturity_date", "interest_rate_type",
            "interest_rate", "wibor_margin", "inflation_margin", "base_interest_rate", "face_value"
        ]
        extra_kwargs = {
            "owner": {"read_only": True},
            "price": {"required": False, "allow_null": True},
            "currency": {"required": False, "allow_null": True},
            "external_id": {"required": False},
            "product": {"required": False}
        }

    def validate(self, data):
        asset_type = data.get('asset_type')
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
        for field in ['symbol', 'name', 'asset_type', 'bond_type', 'bond_series',
                      'maturity_date', 'interest_rate_type', 'interest_rate',
                      'wibor_margin', 'inflation_margin', 'base_interest_rate', 'face_value']:
            validated_data.pop(field, None)
        return Transactions.objects.create(**validated_data)
