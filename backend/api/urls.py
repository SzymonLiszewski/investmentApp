from django.urls import path
from . import views
from analytics.views import stockDataView, predictView, fundamentalAnalysisView, basicInfoView

urlpatterns = [
    path('', views.getRoutes, name="routes"),
    path('stockData/<str:ticker>/', stockDataView, name="stockData"),
    path('predict/<str:ticker>/', predictView, name="predict"),
    path('fundamental/<str:ticker>/', fundamentalAnalysisView, name="fundamental"),
    path('basic/<str:ticker>/', basicInfoView, name="basic")
]