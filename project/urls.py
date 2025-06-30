"""
URL configuration for project project.
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings # Import settings
from django.conf.urls.static import static # Import static file serving helper

from user import views as user_views
from portfolio import views as portfolio_views
from user.views import CustomLogoutView 

urlpatterns = [
    path('admin/', admin.site.urls),

    path('', portfolio_views.calculator_view, name='home'), 
    
    path('login/', user_views.Login, name ='login'),
    path('logout/', CustomLogoutView.as_view(next_page = '/'), name ='logout'), 
    path('register/', user_views.register, name ='register'),

    path('calculator/', portfolio_views.calculator_view, name='portfolio_calculator'), 
]

# IMPORTANT: This block tells Django to serve static files when DEBUG is False.
# This is a simple solution for small deployments. For large scale, use a CDN.
if not settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)