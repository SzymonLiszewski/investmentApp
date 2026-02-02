from django.db import models
from decimal import Decimal


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
