# portfolio/urls.py

from django.urls import path
from . import views # Assuming your views are in portfolio/views.py
from .views import StockHoldingUpdateView, StockHoldingDeleteView # <--- NEW IMPORTS

app_name = 'portfolio'

urlpatterns = [
    path('', views.portfolio_list, name='portfolio_list'),
    # <--- NEW URL PATTERNS ---
    path('edit/<int:pk>/', StockHoldingUpdateView.as_view(), name='holding_update'),
    path('delete/<int:pk>/', StockHoldingDeleteView.as_view(), name='holding_delete'),
    path('chart/<str:symbol>/', views.stock_chart_view, name='stock_chart'),
    # --- END NEW URL PATTERNS ---
]