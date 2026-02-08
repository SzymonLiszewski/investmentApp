"""
URL configuration for analytics app.
Kept only: predictions and news-with-sentiment.
"""
from django.urls import path
from . import views

urlpatterns = [
    path('predict/<str:ticker>/', views.predictView, name='predict'),
    path('news-with-sentiment/', views.newsWithSentimentView, name='news_with_sentiment'),
]
