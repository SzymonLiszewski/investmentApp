"""
URL configuration for backend project.
"""
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),

    # base: auth, assets, market data, news raw, calendar, bonds data
    path('api/', include('base.urls')),

    # portfolio: transactions, composition, value-history, profit, bonds/calculate
    path('api/portfolio/', include('portfolio.urls')),

    # analytics: predictions, news-with-sentiment
    path('api/analytics/', include('analytics.urls')),
]
