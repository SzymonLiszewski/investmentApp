from django.urls import path, include
from . import views
from analytics.views import stockDataView, predictView, fundamentalAnalysisView, basicInfoView, technicalAnalysisView, CalendarEarningsView, CalendarIPOView
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
    path("auth/", include("rest_framework.urls"))
]