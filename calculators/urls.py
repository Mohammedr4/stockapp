# calculators/urls.py
from django.urls import path
from . import views

app_name = 'calculators'

urlpatterns = [
    path('', views.calculators_index, name='calculators_index'),
    path('stock-reprice/', views.stock_reprice_calculator, name='stock_reprice_calculator'),
    path('capital-gains/', views.capital_gains_estimator, name='capital_gains_estimator')
    # Add other calculator URLs here later (e.g., 'capital-gains/', 'compound-interest/')
]