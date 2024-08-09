from django.db import models
from django.contrib.auth.models import User

# Create your models here.

class Stock(models.Model):
    ticker = models.CharField(max_length=10, unique=True, primary_key=True)
    companyName = models.TextField()
    sector = models.TextField()
    industry = models.TextField()

    def __str__(self):
        return self.ticker

class UserStock(models.Model):
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name="ownedStocks")
    ownedStock = models.ForeignKey(Stock, on_delete=models.CASCADE)
    quantity = models.FloatField(default=0)

class Transactions(models.Model):
    class transaction_type(models.TextChoices):
        BUY = 'B', 'buy'
        SELL = 'S', 'sell'
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name="transactions")
    product = models.ForeignKey(Stock, on_delete=models.CASCADE)
    transactionType = models.CharField(
        max_length=2,
        choices=transaction_type.choices,
        default=transaction_type.BUY
    )
    quantity = models.FloatField(default=0.0)
    price = models.FloatField(default=0.0)
    date = models.DateField(default='2024-01-01')
    