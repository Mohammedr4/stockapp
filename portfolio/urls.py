# portfolio/urls.py
from django.urls import path
from . import views

app_name = 'portfolio'

urlpatterns = [
    # The new dashboard page is the root of the portfolio app
    path('', views.portfolio_dashboard_view, name='portfolio_list'),
    
    # The API endpoint that provides all data for the dashboard
    path('api/summary/', views.PortfolioAPIView.as_view(), name='api_summary'),

    # URLs for Creating, Updating, Deleting holdings
    path('api/holdings/', views.StockHoldingAPIView.as_view(), name='api_holdings_create'),
    path('api/holdings/<int:pk>/', views.StockHoldingAPIView.as_view(), name='api_holdings_detail'),
]