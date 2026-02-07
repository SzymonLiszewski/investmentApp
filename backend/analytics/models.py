from django.db import models
from django.contrib.auth.models import User
from decimal import Decimal


class PortfolioSnapshot(models.Model):
    """
    Daily snapshot of a user's total portfolio value.

    Snapshots are created by a batch job (management command / cron) and
    re-calculated from the transaction date whenever a new transaction is
    recorded.
    """
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='portfolio_snapshots',
    )
    date = models.DateField()
    currency = models.CharField(max_length=10, default='PLN')
    total_value = models.DecimalField(max_digits=15, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'date', 'currency')
        ordering = ['date']
        indexes = [
            models.Index(fields=['user', 'date']),
        ]

    def __str__(self):
        return (
            f"Snapshot {self.user.username} {self.date} "
            f"{self.total_value} {self.currency}"
        )


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
