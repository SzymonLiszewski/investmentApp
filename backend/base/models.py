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


class CurrentPrice(models.Model):
    """
    Stores the latest (current) price for a symbol. One record per symbol;
    update when fetching fresh price from API.
    """
    asset = models.ForeignKey(
        Asset,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="current_prices",
    )
    symbol = models.CharField(max_length=50, unique=True, db_index=True)
    price = models.DecimalField(max_digits=18, decimal_places=4)
    currency = models.CharField(max_length=10, default="USD")
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["symbol"]
        verbose_name = "Current Price"
        verbose_name_plural = "Current Prices"

    def __str__(self):
        return f"{self.symbol}: {self.price} {self.currency}"


class StockDataCache(models.Model):
    """
    Cache for stock data from fetcher (basic info, fundamental analysis, technical indicators).
    One record per (symbol, data_type). Data stored as JSON; refetched when older than max age.
    """
    class DataType(models.TextChoices):
        BASIC_INFO = "basic_info", "Basic Info"
        FUNDAMENTAL_ANALYSIS = "fundamental_analysis", "Fundamental Analysis"
        TECHNICAL_INDICATORS = "technical_indicators", "Technical Indicators"

    symbol = models.CharField(max_length=50, db_index=True)
    data_type = models.CharField(max_length=30, choices=DataType.choices, db_index=True)
    data = models.JSONField(default=dict)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["symbol", "data_type"]
        verbose_name = "Stock Data Cache"
        verbose_name_plural = "Stock Data Cache"
        constraints = [
            models.UniqueConstraint(
                fields=["symbol", "data_type"],
                name="unique_stock_data_cache_symbol_type",
            )
        ]

    def __str__(self):
        return f"{self.symbol} ({self.data_type})"


class EconomicCalendarEvent(models.Model):
    """
    Cached economic calendar events (earnings, IPO) from external API.
    Refreshed periodically; API is called only when cache is stale or empty.
    """
    class EventType(models.TextChoices):
        EARNINGS = "earnings", "Earnings"
        IPO = "ipo", "IPO"

    event_type = models.CharField(max_length=20, choices=EventType.choices, db_index=True)
    symbol = models.CharField(max_length=50, db_index=True)
    name = models.CharField(max_length=255, blank=True)
    report_date = models.DateField(null=True, blank=True)
    fiscal_date_ending = models.DateField(null=True, blank=True)
    estimate = models.DecimalField(max_digits=18, decimal_places=4, null=True, blank=True)
    currency = models.CharField(max_length=10, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["report_date", "symbol"]
        verbose_name = "Economic Calendar Event"
        verbose_name_plural = "Economic Calendar Events"
        constraints = [
            models.UniqueConstraint(
                fields=["event_type", "symbol", "report_date"],
                name="unique_economic_calendar_event",
            )
        ]
        indexes = [
            models.Index(fields=["event_type", "report_date"]),
        ]

    def __str__(self):
        return f"{self.event_type}: {self.symbol} @ {self.report_date}"
