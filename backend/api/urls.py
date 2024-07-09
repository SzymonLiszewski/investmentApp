from django.urls import path
from . import views
from analytics.views import stockDataView, predictView

urlpatterns = [
    path('', views.getRoutes, name="routes"),
    path('stockData/', stockDataView, name="stockData"),
    path('predict', predictView, name="predict")
]