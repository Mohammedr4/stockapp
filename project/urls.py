"""
URL configuration for project project.
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings 
from django.conf.urls.static import static 

from user import views as user_views
from portfolio.views import dashboard_view # IMPORTANT: Import the new dashboard_view
from user.views import CustomLogoutView 

urlpatterns = [
    path('admin/', admin.site.urls),

    # IMPORTANT CHANGE: Make the root URL ('/') the unified calculator dashboard
    path('', dashboard_view, {'tab': 'reprice'}, name='home'), 
    
    # User authentication paths (signup, login, logout)
    path('login/', user_views.Login, name ='login'),
    path('logout/', CustomLogoutView.as_view(next_page = '/'), name ='logout'), 
    path('register/', user_views.register, name ='register'),

    # Portfolio app URLs:
    # Keep /calculator/ for direct access, also pointing to the dashboard
    path('calculator/', dashboard_view, {'tab': 'reprice'}, name='portfolio_calculator'), 
    
    # NEW: Capital Gains Estimator Page (now part of the dashboard)
    # This URL will open the dashboard with the 'capital_gains' tab active
    path('capital-gains/', dashboard_view, {'tab': 'capital_gains'}, name='capital_gains_estimator'),
]

# IMPORTANT: This block tells Django to serve static files when DEBUG is False.
# This is a simple solution for small deployments. For large scale, use a CDN.
if not settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
