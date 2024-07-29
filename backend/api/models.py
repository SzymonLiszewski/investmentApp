from django.db import models
from django.contrib.auth.models import User

# Create your models here.

class Stock(models.Model):
    ticker = models.CharField(max_length=10)
    companyName = models.TextField()
    sector = models.TextField()
    industry = models.TextField()

    def __str__(self):
        return self.ticker

class UserStock(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    ownedStock = models.ForeignKey(Stock, on_delete=models.CASCADE)
    quantity = models.BigIntegerField()

class Transactions(models.Model):
    class transaction_type(models.TextChoices):
        BUY = 'B', 'buy'
        SELL = 'S', 'sell'
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    product = models.ForeignKey(Stock, on_delete=models.CASCADE)
    transactionType = models.CharField(
        max_length=2,
        choices=transaction_type.choices,
        default=transaction_type.BUY
    )