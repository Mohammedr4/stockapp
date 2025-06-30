"""
URL configuration for project project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
"""
URL configuration for project project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
    Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.contrib.auth import views as auth_views
from user import views as user_views
from user.views import CustomLogoutView
from portfolio import views as portfolio_views

# Import settings and static for serving static files in production (not recommended for scale)
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),

    # Make the root URL ('/') the calculator page
    path('', portfolio_views.calculator_view, name='home'), 
    
    # User authentication paths (signup, login, logout)
    path('login/', user_views.Login, name ='login'),
    path('logout/', CustomLogoutView.as_view(next_page = '/'), name ='logout'), 
    path('register/', user_views.register, name ='register'),

    # Portfolio app URLs (keeping the /calculator/ path for direct access, though / is preferred now)
    path('calculator/', portfolio_views.calculator_view, name='portfolio_calculator'), 
]

# IMPORTANT: Serve static files in development and production (NOT recommended for production scale)
# This block is added to make static files visible when DEBUG is False,
# as you've chosen not to use WhiteNoise or a dedicated static file server.
if not settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

