from django.urls import path, include
from django.conf import settings
from . import views
from django.conf.urls.static import static
# Make sure there are no extra characters or blank lines immediately above or below this line
urlpatterns = [
    # Home page URL
    path('', views.index, name ='index'),
    # Login URL (maps to your custom Login view)
    path('login/', views.Login, name ='login'),
    # Registration URL
    path('register/', views.register, name ='register'),
    # A placeholder for a profile page (requires login)
    # path('profile/', views.profile, name='profile'),
]

# Serve static files during development
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
