"""
URL configuration for project project.
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings 
from django.conf.urls.static import static 

from user import views as user_views
from portfolio import views as portfolio_views # Ensure portfolio views are imported
from user.views import CustomLogoutView 

urlpatterns = [
    path('admin/', admin.site.urls),

    path('', portfolio_views.calculator_view, name='home'), 
    
    path('login/', user_views.Login, name ='login'),
    path('logout/', CustomLogoutView.as_view(next_page = '/'), name ='logout'), 
    path('register/', user_views.register, name ='register'),

    path('calculator/', portfolio_views.calculator_view, name='portfolio_calculator'), 
    
    # NEW: Capital Gains Estimator Page
    path('capital-gains/', portfolio_views.capital_gains_estimator_view, name='capital_gains_estimator'),
]

# IMPORTANT: Serve static files in production.
if not settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)