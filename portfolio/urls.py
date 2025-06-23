from django.urls import path
from . import views

urlpatterns = [
    # Defines the URL for the calculator page.
    # When you navigate to /calculator/, the calculator_view function in views.py will be called.
    path('', views.calculator_view, name='portfolio_calculator'),
]
