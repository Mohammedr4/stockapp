# core/urls.py
from django.urls import path
from . import views

app_name = 'core'

urlpatterns = [
    path('signup-prompt/', views.signup_prompt, name='signup_prompt'),
]