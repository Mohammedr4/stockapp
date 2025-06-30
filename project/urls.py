"""
URL configuration for project project.
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings # Import settings
from django.conf.urls.static import static # Import static file serving helper

# Import your views
from user import views as user_views
from portfolio import views as portfolio_views
from user.views import CustomLogoutView # Assuming you have this custom logout view

urlpatterns = [
    path('admin/', admin.site.urls),

    # Make the root URL ('/') the calculator page for both authenticated and unauthenticated users
    # The view itself will handle redirection for unauthenticated users if needed.
    path('', portfolio_views.calculator_view, name='home'), 
    
    # User authentication paths
    path('login/', user_views.Login, name ='login'),
    # Use your CustomLogoutView if you have one, otherwise use Django's built-in LogoutView
    path('logout/', CustomLogoutView.as_view(next_page = '/'), name ='logout'), 
    path('register/', user_views.register, name ='register'),

    # Portfolio app URLs (calculator is already at root, but keeping this for direct path if desired)
    path('calculator/', portfolio_views.calculator_view, name='portfolio_calculator'), 
]

# IMPORTANT: Serve static files in production.
# This is explicitly added because you are not using WhiteNoise.
# This block should ONLY be active when DEBUG is False in production.
if not settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)