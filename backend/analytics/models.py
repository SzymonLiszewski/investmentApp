from django.db import models


class SarimaForecast(models.Model):
    """One forecasted price point for a symbol, produced by the nightly SARIMA batch.

    Rows for a symbol are replaced wholesale on each training run, so the table
    stays bounded at (number of top stocks) x (forecast horizon).
    """

    symbol = models.CharField(max_length=50, db_index=True)
    forecast_date = models.DateField()
    predicted_price = models.DecimalField(max_digits=18, decimal_places=4)
    lower_bound = models.DecimalField(max_digits=18, decimal_places=4, null=True, blank=True)
    upper_bound = models.DecimalField(max_digits=18, decimal_places=4, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["symbol", "forecast_date"]
        constraints = [
            models.UniqueConstraint(
                fields=["symbol", "forecast_date"],
                name="unique_sarima_forecast_symbol_date",
            )
        ]

    def __str__(self):
        return f"{self.symbol} {self.forecast_date}: {self.predicted_price}"
