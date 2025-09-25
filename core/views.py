from django.shortcuts import render
from django.contrib.auth.decorators import login_required

def landing_page(request):
    """
    Renders the landing page of the application.
    """
    return render(request, 'core/landing_page.html', {})

@login_required
def profile_view(request):
    """ Renders the user's profile page. """
    return render(request, 'core/profile.html')