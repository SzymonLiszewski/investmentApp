from decimal import Decimal

from django.db import models
from django.contrib.auth.models import User
from base.models import Asset


class UserAsset(models.Model):
    """
    Currently open positions of the user: for each asset, the quantity held and
    the average purchase price (and its currency) for that position.
    """
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name="ownedAssets")
    ownedAsset = models.ForeignKey(Asset, on_delete=models.CASCADE)
    quantity = models.FloatField(default=0)
    average_purchase_price = models.DecimalField(
        max_digits=18,
        decimal_places=6,
        null=True,
        blank=True,
        help_text="Average cost per unit of this position, in the given currency.",
    )
    currency = models.CharField(
        max_length=10,
        null=True,
        blank=True,
        help_text="Currency of average_purchase_price (e.g. PLN, USD).",
    )


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
    currency = models.CharField(
        max_length=10,
        blank=True,
        null=True,
        help_text='Currency of price when set (e.g. PLN). When null, price is in asset native currency.',
    )
    external_id = models.CharField(max_length=255, blank=True, null=True, unique=True)


class PortfolioSnapshot(models.Model):
    """Daily snapshot of a user's total portfolio value and cost basis."""
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='portfolio_snapshots',
    )
    date = models.DateField()
    currency = models.CharField(max_length=10, default='PLN')
    total_value = models.DecimalField(max_digits=15, decimal_places=2)
    total_invested = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=Decimal('0'),
        help_text='Cumulative net cash invested (purchases minus sales) up to this date.',
    )
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
