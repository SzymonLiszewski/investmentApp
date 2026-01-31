"""
URL configuration for analytics app.
"""
from django.urls import path
from . import views

urlpatterns = [
    # Stock analysis endpoints
    path('stock/<str:ticker>/', views.stockDataView, name='stock_data'),
    path('predict/<str:ticker>/', views.predictView, name='predict'),
    path('fundamental/<str:ticker>/', views.fundamentalAnalysisView, name='fundamental'),
    path('basic/<str:ticker>/', views.basicInfoView, name='basic'),
    path('technical/<str:ticker>/', views.technicalAnalysisView, name='technical'),
    
    # Calendar endpoints
    path('calendar/earnings/', views.CalendarEarningsView, name='calendar_earnings'),
    path('calendar/ipo/', views.CalendarIPOView, name='calendar_ipo'),
    
    # Portfolio endpoints
    path('portfolio/composition/', views.getUserAssetComposition, name='portfolio_composition'),
    path('portfolio/profit/', views.profitView, name='portfolio_profit'),
    path('portfolio/update/', views.updateTransactions, name='portfolio_update'),
    
    # Integration endpoints
    path('integration/xtb/login/', views.xtbLogin, name='xtb_login'),
    
    # News endpoint
    path('news/', views.getNews, name='news'),
    
    # Bond endpoints
    path('bonds/series/', views.getBondSeries, name='bonds_series'),
    path('bonds/series/<str:bond_type>/', views.getBondSeriesByType, name='bonds_series_by_type'),
    path('bonds/calculate/', views.calculateBondValue, name='bonds_calculate'),
    path('bonds/economic-data/', views.getEconomicData, name='economic_data'),
    path('bonds/economic-data/history/', views.getEconomicDataHistory, name='economic_data_history'),
]
