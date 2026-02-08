from django.urls import path
from . import views

urlpatterns = [
    path('transactions/', views.CreateTransaction.as_view(), name="transactions"),
    path('composition/', views.getUserAssetComposition, name='portfolio_composition'),
    path('profit/', views.profitView, name='portfolio_profit'),
    path('value-history/', views.valueHistoryView, name='portfolio_value_history'),
    path('update/', views.updateTransactions, name='portfolio_update'),
    path('integration/xtb/login/', views.xtbLogin, name='xtb_login'),
    path('bonds/calculate/', views.calculateBondValue, name='bonds_calculate'),
]
