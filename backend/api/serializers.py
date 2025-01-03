from django.contrib.auth.models import User
from rest_framework import serializers
from .models import UserStock, Transactions, Stock

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "username", "password"]
        extra_kwargs = {"password": {"write_only": True}}
    def create(self, validated_data):
        user = User.objects.create_user(**validated_data)
        return user
    
class UserStockSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserStock
        fields = ["id", "owner", "ownedStock", "quantity"]
        extra_kwargs = {"owner": {"read_only": True}}
    
class StockSerializer(serializers.ModelSerializer):
    class Meta:
        model = Stock
        fields = ["ticker", "companyName", "sector", "industry"]

class TransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Transactions
        fields = ["owner", "product", "transactionType", "quantity", "price", "date", "external_id"]
        extra_kwargs = {"owner": {"read_only": True}, "price": {"required": False}, "external_id": {"required": False}}