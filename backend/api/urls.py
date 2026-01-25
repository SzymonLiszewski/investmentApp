from django.urls import path, include
from . import views
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

urlpatterns = [
    path('', views.getRoutes, name="routes"),
    
    # Analytics app endpoints
    path('analytics/', include('analytics.urls')),
    
    # User and authentication endpoints
    path('user/register/', views.CreateUserView.as_view(), name="register"),
    path('token/', TokenObtainPairView.as_view(), name="get_token"),
    path('token/refresh/', TokenRefreshView.as_view(), name="refresh"),
    path("auth/", include("rest_framework.urls")),
    
    # Asset management endpoints
    path('transactions/', views.CreateTransaction.as_view(), name="transactions"),
    path('userAsset/delete/<int:pk>/', views.UserAssetDelete.as_view(), name="delete_asset"),
    path('assets/', views.AssetCreate.as_view(), name="assets"),
    path('assets/search/', views.searchAssets, name="search_assets"),
]