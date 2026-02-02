from django.db import models
from django.contrib.auth.models import User
from decimal import Decimal

# Create your models here.

class Asset(models.Model):
    class AssetType(models.TextChoices):
        STOCKS = 'stocks', 'Stocks'
        BONDS = 'bonds', 'Bonds'
        CRYPTOCURRENCIES = 'cryptocurrencies', 'Cryptocurrencies'
    
    class InterestRateType(models.TextChoices):
        FIXED = 'fixed', 'Fixed'
        VARIABLE_WIBOR = 'variable_wibor', 'Variable WIBOR'
        INDEXED_INFLATION = 'indexed_inflation', 'Indexed Inflation'
    
    id = models.AutoField(primary_key=True)
    symbol = models.CharField(max_length=50, unique=True, null=True, blank=True)  # Required for stocks, optional for others
    name = models.CharField(max_length=255)  # Required for all
    asset_type = models.CharField(
        max_length=20,
        choices=AssetType.choices,
        default=AssetType.STOCKS
    )
    
    # Bond-specific fields
    bond_type = models.CharField(max_length=10, null=True, blank=True)  # OS, OTS, EDO, ROR, DOR, etc.
    bond_series = models.CharField(max_length=20, null=True, blank=True)  # e.g., OS0424
    maturity_date = models.DateField(null=True, blank=True)
    interest_rate = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)  # For fixed or base rate
    face_value = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('100.00'))
    interest_rate_type = models.CharField(
        max_length=20,
        choices=InterestRateType.choices,
        null=True,
        blank=True
    )
    wibor_margin = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)  # Margin for WIBOR-based bonds
    inflation_margin = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)  # Margin for inflation-indexed bonds
    base_interest_rate = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)  # Base rate for first period of indexed bonds

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
    