# core/views.py
from django.shortcuts import render

def landing_page(request):
    """
    Renders the landing page of the application.
    This view is typically mapped to the site's root URL ('/').
    """
    return render(request, 'core/landing_page.html', {})

def signup_prompt(request):
    """
    Renders a page prompting the user to sign up or log in,
    often used as an intermediate step or informational page.
    """
    return render(request, 'core/signup_prompt.html', {})