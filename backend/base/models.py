from django.db import models
from decimal import Decimal


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
    symbol = models.CharField(max_length=50, unique=True, null=True, blank=True)
    name = models.CharField(max_length=255)
    asset_type = models.CharField(
        max_length=20,
        choices=AssetType.choices,
        default=AssetType.STOCKS
    )
    
    # Bond-specific fields
    bond_type = models.CharField(max_length=10, null=True, blank=True)
    bond_series = models.CharField(max_length=20, null=True, blank=True)
    maturity_date = models.DateField(null=True, blank=True)
    interest_rate = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    face_value = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('100.00'))
    interest_rate_type = models.CharField(
        max_length=20,
        choices=InterestRateType.choices,
        null=True,
        blank=True
    )
    wibor_margin = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    inflation_margin = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    base_interest_rate = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)

    def __str__(self):
        if self.symbol:
            return self.symbol
        return self.name or str(self.id)
    
    def clean(self):
        from django.core.exceptions import ValidationError
        if self.asset_type == self.AssetType.STOCKS:
            if not self.symbol:
                raise ValidationError({'symbol': 'Symbol is required for stocks'})


class EconomicData(models.Model):
    """
    Model to store economic data (WIBOR rates and inflation) for bond calculations.
    """
    date = models.DateField(unique=True, help_text="Date of the economic data measurement")
    wibor_3m = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        help_text="WIBOR 3M rate in percentage"
    )
    wibor_6m = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        help_text="WIBOR 6M rate in percentage"
    )
    inflation_cpi = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        help_text="CPI inflation rate in percentage"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-date']
        verbose_name = "Economic Data"
        verbose_name_plural = "Economic Data"
    
    def __str__(self):
        return f"Economic Data for {self.date}: WIBOR 3M={self.wibor_3m}%, WIBOR 6M={self.wibor_6m}%, Inflation={self.inflation_cpi}%"


class PriceHistory(models.Model):
    """
    Stores historical OHLCV price data for an asset (stock, crypto, etc.).
    """
    asset = models.ForeignKey(
        Asset,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="price_history",
    )
    symbol = models.CharField(max_length=50, db_index=True)
    date = models.DateField(db_index=True)
    open = models.DecimalField(max_digits=18, decimal_places=4, null=True, blank=True)
    high = models.DecimalField(max_digits=18, decimal_places=4, null=True, blank=True)
    low = models.DecimalField(max_digits=18, decimal_places=4, null=True, blank=True)
    close = models.DecimalField(max_digits=18, decimal_places=4)
    volume = models.BigIntegerField(null=True, blank=True)

    class Meta:
        ordering = ["-date"]
        verbose_name = "Price History"
        verbose_name_plural = "Price History"
        constraints = [
            models.UniqueConstraint(
                fields=["symbol", "date"],
                name="unique_symbol_date",
            )
        ]

    def __str__(self):
        return f"{self.symbol} @ {self.date}: {self.close}"
