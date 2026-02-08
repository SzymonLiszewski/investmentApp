"""
Initial migration for portfolio app.

Uses db_table to take over existing tables from api and analytics apps.
These tables already exist in the database, so we use RunSQL with
state_operations to register the models without actually creating tables.
"""
import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('base', '0001_initial'),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            database_operations=[],
            state_operations=[
                migrations.CreateModel(
                    name='UserAsset',
                    fields=[
                        ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                        ('quantity', models.FloatField(default=0)),
                        ('owner', models.ForeignKey(
                            on_delete=django.db.models.deletion.CASCADE,
                            related_name='ownedAssets',
                            to=settings.AUTH_USER_MODEL,
                        )),
                        ('ownedAsset', models.ForeignKey(
                            on_delete=django.db.models.deletion.CASCADE,
                            to='base.asset',
                        )),
                    ],
                    options={
                        'db_table': 'api_userasset',
                    },
                ),
            ],
        ),
        migrations.SeparateDatabaseAndState(
            database_operations=[],
            state_operations=[
                migrations.CreateModel(
                    name='Transactions',
                    fields=[
                        ('id', models.AutoField(primary_key=True, serialize=False)),
                        ('transactionType', models.CharField(
                            choices=[('B', 'buy'), ('S', 'sell')],
                            default='B', max_length=2,
                        )),
                        ('quantity', models.FloatField(default=0.0)),
                        ('price', models.FloatField(default=0.0)),
                        ('date', models.DateField(default='2024-01-01')),
                        ('external_id', models.CharField(blank=True, max_length=255, null=True, unique=True)),
                        ('owner', models.ForeignKey(
                            on_delete=django.db.models.deletion.CASCADE,
                            related_name='transactions',
                            to=settings.AUTH_USER_MODEL,
                        )),
                        ('product', models.ForeignKey(
                            on_delete=django.db.models.deletion.CASCADE,
                            to='base.asset',
                        )),
                    ],
                    options={
                        'db_table': 'api_transactions',
                    },
                ),
            ],
        ),
        migrations.SeparateDatabaseAndState(
            database_operations=[],
            state_operations=[
                migrations.CreateModel(
                    name='PortfolioSnapshot',
                    fields=[
                        ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                        ('date', models.DateField()),
                        ('currency', models.CharField(default='PLN', max_length=10)),
                        ('total_value', models.DecimalField(decimal_places=2, max_digits=15)),
                        ('created_at', models.DateTimeField(auto_now_add=True)),
                        ('user', models.ForeignKey(
                            on_delete=django.db.models.deletion.CASCADE,
                            related_name='portfolio_snapshots',
                            to=settings.AUTH_USER_MODEL,
                        )),
                    ],
                    options={
                        'db_table': 'analytics_portfoliosnapshot',
                        'ordering': ['date'],
                        'unique_together': {('user', 'date', 'currency')},
                        'indexes': [
                            models.Index(fields=['user', 'date'], name='portfolio_p_user_id_0b22b8_idx'),
                        ],
                    },
                ),
            ],
        ),
    ]
