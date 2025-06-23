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
from django.contrib.auth import views as auth_views # Alias to avoid name collision with custom Login view
from user import views as user_views # Alias for user app views

urlpatterns = [
    path('admin/', admin.site.urls),

    # User authentication paths (signup, login, logout, home)
    path('', include('user.urls')), # Includes 'index', 'register', 'login' from user app
    
    # Custom login/logout views provided by the user
    # Note: user_views.Login is a custom view that handles login.
    # auth_views.LogoutView is Django's built-in logout.
    path('login/', user_views.Login, name ='login'),
    # Use Django's built-in LogoutView, redirecting to the home page after logout
    # Changed next_page='index' to next_page='/' for more robustness in redirect
    path('logout/', auth_views.LogoutView.as_view(next_page = '/'), name ='logout'), 
    path('register/', user_views.register, name ='register'),

    # Portfolio app URLs (for the calculator)
    path('calculator/', include('portfolio.urls')), 
]
