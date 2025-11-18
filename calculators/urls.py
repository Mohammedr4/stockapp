# calculators/urls.py
from django.urls import path
from . import views

app_name = 'calculators'

urlpatterns = [
    path('', views.calculators_index, name='calculators_index'),
    
    # The new Repricing Strategy Dashboard UI
    path('stock-reprice/', views.reprice_dashboard_view, name='stock_reprice_calculator'),
    
    # The new Clarity Dashboard UI and its API
    path('capital-gains/', views.clarity_dashboard_view, name='clarity_dashboard'),
    path('api/calculate-gains/', views.CapitalGainsAPIView.as_view(), name='api_calculate_gains'),

    # The new Reprice API
    path('api/calculate-reprice/', views.RepriceAPIView.as_view(), name='api_calculate_reprice'),
    
    path('portfolio-rebalance/', views.rebalance_dashboard_view, name='rebalance_dashboard'),
    path('api/calculate-rebalance/', views.RebalanceAPIView.as_view(), name='api_calculate_rebalance'),

    # Saved Strategies API
    path('api/reprice-strategies/', views.SavedRepriceStrategyAPIView.as_view(), name='api_reprice_strategies_list_create'),
    path('api/reprice-strategies/<int:pk>/', views.SavedRepriceStrategyAPIView.as_view(), name='api_reprice_strategies_delete'),
]