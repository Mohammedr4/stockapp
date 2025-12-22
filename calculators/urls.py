# calculators/urls.py
from django.urls import path
from . import views

app_name = 'calculators'

urlpatterns = [
    path('', views.calculators_index, name='calculators_index'),
    
    # Repricing
    path('stock-reprice/', views.reprice_dashboard_view, name='stock_reprice_calculator'),
    
    # Capital Gains
    path('capital-gains/', views.clarity_dashboard_view, name='clarity_dashboard'),
    path('api/calculate-gains/', views.CapitalGainsAPIView.as_view(), name='api_calculate_gains'),

    # Reprice API
    path('api/calculate-reprice/', views.RepriceAPIView.as_view(), name='api_calculate_reprice'),
    
    # Rebalance Page & Calculation API
    path('portfolio-rebalance/', views.rebalance_dashboard_view, name='rebalance_dashboard'),
    path('api/calculate-rebalance/', views.RebalanceAPIView.as_view(), name='api_calculate_rebalance'),

    # Saved Strategies (Reprice)
    path('api/reprice-strategies/', views.SavedRepriceStrategyAPIView.as_view(), name='api_reprice_strategies_list_create'),
    path('api/reprice-strategies/<int:pk>/', views.SavedRepriceStrategyAPIView.as_view(), name='api_reprice_strategies_delete'),
    path('api/reprice-export-pdf/', views.ExportRepricePDFView.as_view(), name='api_reprice_export_pdf'),

    # Saved Scenarios (Tax)
    path('api/tax-scenarios/', views.SavedCapitalGainsScenarioAPIView.as_view(), name='api_tax_scenarios_list_create'),
    path('api/tax-scenarios/<int:pk>/', views.SavedCapitalGainsScenarioAPIView.as_view(), name='api_tax_scenarios_delete'),
    path('api/tax-export-pdf/', views.ExportCapitalGainsPDFView.as_view(), name='api_tax_export_pdf'),

    # --- NEW: Saved Scenarios (Rebalance) ---
    # ADD "views." prefix here!
    path('api/rebalance-scenarios/', views.SavedRebalanceScenarioAPIView.as_view(), name='rebalance_scenarios_list'),
    path('api/rebalance-scenarios/<int:pk>/', views.SavedRebalanceScenarioAPIView.as_view(), name='rebalance_scenarios_detail'),
    path('api/rebalance-export-pdf/', views.ExportRebalancePDFView.as_view(), name='api_rebalance_export_pdf'),
]