from django.urls import path, include
from . import views
from analytics.views import stockDataView, predictView, fundamentalAnalysisView, basicInfoView, technicalAnalysisView, CalendarEarningsView, CalendarIPOView, profitView, updateTransactions, xtbLogin, getNews
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

urlpatterns = [
    path('', views.getRoutes, name="routes"),
    path('stockData/<str:ticker>/', stockDataView, name="stockData"),
    path('predict/<str:ticker>/', predictView, name="predict"),
    path('fundamental/<str:ticker>/', fundamentalAnalysisView, name="fundamental"),
    path('basic/<str:ticker>/', basicInfoView, name="basic"),
    path('technical/<str:ticker>/', technicalAnalysisView, name="technical"),
    path('calendar/earnings/', CalendarEarningsView, name="calendarEarnings"),
    path('calendar/IPO/', CalendarIPOView, name="calendarIPO"),
    path('user/register/', views.CreateUserView.as_view(), name="register"),
    path('token/', TokenObtainPairView.as_view(), name="get_token"),
    path('token/refresh/', TokenRefreshView.as_view(), name="refresh"),
    path("auth/", include("rest_framework.urls")),
    path('userAsset/', views.CreateUserAsset.as_view(), name="asset_list"),
    path('transactions/', views.CreateTransaction.as_view(), name="transactions"),
    path('userAsset/delete/<int:pk>/', views.UserAssetDelete.as_view(), name="delete_asset"),
    path('assets/', views.AssetCreate.as_view(), name="assets"),
    path('assets/search/', views.searchAssets, name="search_assets"),
    path('portfolio/profit', profitView, name="profit"),
    path('portfolio/update', updateTransactions, name="updateTransactions"),
    path('integration/xtb/login/', xtbLogin, name="xtblogin"),
    path('news/', getNews, name="news")
]