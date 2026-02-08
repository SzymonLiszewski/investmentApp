from django.contrib import admin
from .models import Asset, EconomicData


@admin.register(Asset)
class AssetAdmin(admin.ModelAdmin):
    list_display = ('symbol', 'name', 'asset_type')
    list_filter = ('asset_type',)
    search_fields = ('symbol', 'name')


@admin.register(EconomicData)
class EconomicDataAdmin(admin.ModelAdmin):
    list_display = ('date', 'wibor_3m', 'wibor_6m', 'inflation_cpi', 'created_at', 'updated_at')
    list_filter = ('date',)
    search_fields = ('date',)
    ordering = ('-date',)
    date_hierarchy = 'date'
    
    fieldsets = (
        ('Economic Data', {
            'fields': ('date', 'wibor_3m', 'wibor_6m', 'inflation_cpi')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ('created_at', 'updated_at')
