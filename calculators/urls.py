# calculators/urls.py
from django.urls import path
from . import views

app_name = 'calculators'

urlpatterns = [
    path('', views.calculators_index, name='calculators_index'),
    
    # Repricing
    path('stock-reprice/', views.reprice_dashboard_view, name='stock_reprice_calculator'),
    # DRIP Predictor
    path('drip-predictor/', views.drip_dashboard_view, name='drip_dashboard'),
    
    # Capital Gains
    path('capital-gains/', views.clarity_dashboard_view, name='clarity_dashboard'),
    path('api/calculate-gains/', views.CapitalGainsAPIView.as_view(), name='api_calculate_gains'),
    path('api/upload-csv/', views.CSVImportAPIView.as_view(), name='api_upload_csv'),

    # Reprice API
    path('api/calculate-reprice/', views.RepriceAPIView.as_view(), name='api_calculate_reprice'),
    
    # DRIP API
    path('api/calculate-drip/', views.DRIPAPIView.as_view(), name='api_calculate_drip'),

    # Saved Strategies (Reprice)
    path('api/reprice-strategies/', views.SavedRepriceStrategyAPIView.as_view(), name='api_reprice_strategies_list_create'),
    path('api/reprice-strategies/<int:pk>/', views.SavedRepriceStrategyAPIView.as_view(), name='api_reprice_strategies_delete'),
    path('api/reprice-export-pdf/', views.ExportRepricePDFView.as_view(), name='api_reprice_export_pdf'),

    # Saved Scenarios (Tax)
    path('api/tax-scenarios/', views.SavedCapitalGainsScenarioAPIView.as_view(), name='api_tax_scenarios_list_create'),
    path('api/tax-scenarios/<int:pk>/', views.SavedCapitalGainsScenarioAPIView.as_view(), name='api_tax_scenarios_delete'),
    path('api/tax-export-pdf/', views.ExportCapitalGainsPDFView.as_view(), name='api_tax_export_pdf'),

    # Saved Projections (DRIP)
    path('api/drip-projections/', views.SavedDRIPProjectionAPIView.as_view(), name='api_drip_projections'),
    path('api/drip-projections/<int:pk>/', views.SavedDRIPProjectionAPIView.as_view(), name='api_drip_projections_delete'),
]