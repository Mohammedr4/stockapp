# stockapp/urls.py

from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('user.urls')),               # User app URLs at root
    path('portfolio/', include('portfolio.urls')), # Portfolio app URLs under /portfolio/
]
