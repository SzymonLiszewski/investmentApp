from django.db import models
from django.contrib.auth.models import User

# Create your models here.

class Asset(models.Model):
    class AssetType(models.TextChoices):
        STOCKS = 'stocks', 'Stocks'
        BONDS = 'bonds', 'Bonds'
        CRYPTOCURRENCIES = 'cryptocurrencies', 'Cryptocurrencies'
    
    id = models.AutoField(primary_key=True)
    symbol = models.CharField(max_length=50, unique=True, null=True, blank=True)  # Required for stocks, optional for others
    name = models.CharField(max_length=255)  # Required for all
    asset_type = models.CharField(
        max_length=20,
        choices=AssetType.choices,
        default=AssetType.STOCKS
    )

    def __str__(self):
        if self.symbol:
            return self.symbol
        return self.name or str(self.id)
    
    def clean(self):
        from django.core.exceptions import ValidationError
        # Validation based on asset_type
        if self.asset_type == self.AssetType.STOCKS:
            if not self.symbol:
                raise ValidationError({'symbol': 'Symbol is required for stocks'})
        # Bonds and cryptocurrencies can have optional symbol

class UserAsset(models.Model):
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name="ownedAssets")
    ownedAsset = models.ForeignKey(Asset, on_delete=models.CASCADE)
    quantity = models.FloatField(default=0)

class Transactions(models.Model):
    id = models.AutoField(primary_key=True)
    class transaction_type(models.TextChoices):
        BUY = 'B', 'buy'
        SELL = 'S', 'sell'
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name="transactions")
    product = models.ForeignKey(Asset, on_delete=models.CASCADE)
    transactionType = models.CharField(
        max_length=2,
        choices=transaction_type.choices,
        default=transaction_type.BUY
    )
    quantity = models.FloatField(default=0.0)
    price = models.FloatField(default=0.0)
    date = models.DateField(default='2024-01-01')
    external_id = models.CharField(max_length=255, blank=True, null=True, unique=True)
    