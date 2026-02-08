from django.contrib import admin
from .models import UserAsset, Transactions, PortfolioSnapshot


@admin.register(UserAsset)
class UserAssetAdmin(admin.ModelAdmin):
    list_display = ('owner', 'ownedAsset', 'quantity')


@admin.register(Transactions)
class TransactionsAdmin(admin.ModelAdmin):
    list_display = ('owner', 'product', 'transactionType', 'quantity', 'price', 'date')
    list_filter = ('transactionType', 'date')


@admin.register(PortfolioSnapshot)
class PortfolioSnapshotAdmin(admin.ModelAdmin):
    list_display = ('user', 'date', 'currency', 'total_value')
    list_filter = ('currency', 'date')
