# Generated by Django 5.0.6 on 2024-07-31 13:26

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0002_transactions_price_transactions_quantity_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='transactions',
            name='date',
            field=models.DateField(default='2024-01-01'),
        ),
    ]