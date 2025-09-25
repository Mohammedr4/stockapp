# stock_savvy_project/urls.py
from django.contrib import admin
from django.urls import path, include
from core import views as core_views

urlpatterns = [
    path('admin/', admin.site.urls),
    # This line replaces your custom accounts app's URLs for login/logout etc.
    path('accounts/', include('allauth.urls')),
    path('calculators/', include('calculators.urls', namespace='calculators')),
    path('', core_views.landing_page, name='home'),
    path('core/', include('core.urls', namespace='core')),
    path('portfolio/', include('portfolio.urls', namespace='portfolio')),
]