from django.db import models
from django.contrib.auth.models import User
from base.models import Asset


class UserAsset(models.Model):
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name="ownedAssets")
    ownedAsset = models.ForeignKey(Asset, on_delete=models.CASCADE)
    quantity = models.FloatField(default=0)

    class Meta:
        db_table = 'api_userasset'


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

    class Meta:
        db_table = 'api_transactions'


class PortfolioSnapshot(models.Model):
    """Daily snapshot of a user's total portfolio value."""
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='portfolio_snapshots',
    )
    date = models.DateField()
    currency = models.CharField(max_length=10, default='PLN')
    total_value = models.DecimalField(max_digits=15, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'analytics_portfoliosnapshot'
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
