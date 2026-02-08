from django.urls import path, include
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from . import views

urlpatterns = [
    path('', views.getRoutes, name="routes"),

    # Auth
    path('user/register/', views.CreateUserView.as_view(), name="register"),
    path('token/', TokenObtainPairView.as_view(), name="get_token"),
    path('token/refresh/', TokenRefreshView.as_view(), name="refresh"),
    path("auth/", include("rest_framework.urls")),

    # Assets
    path('assets/', views.AssetCreate.as_view(), name="assets"),
    path('assets/search/', views.searchAssets, name="search_assets"),

    # Market data
    path('stock/<str:ticker>/', views.stockDataView, name='stock_data'),
    path('basic/<str:ticker>/', views.basicInfoView, name='basic'),
    path('fundamental/<str:ticker>/', views.fundamentalAnalysisView, name='fundamental'),
    path('technical/<str:ticker>/', views.technicalAnalysisView, name='technical'),

    # News (raw)
    path('news/', views.getNews, name='news'),

    # Calendar
    path('calendar/earnings/', views.CalendarEarningsView, name='calendar_earnings'),
    path('calendar/ipo/', views.CalendarIPOView, name='calendar_ipo'),

    # Bond data
    path('bonds/series/', views.getBondSeries, name='bonds_series'),
    path('bonds/series/<str:bond_type>/', views.getBondSeriesByType, name='bonds_series_by_type'),
    path('bonds/economic-data/', views.getEconomicData, name='economic_data'),
    path('bonds/economic-data/history/', views.getEconomicDataHistory, name='economic_data_history'),
]
