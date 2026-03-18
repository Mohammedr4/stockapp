from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages

def landing_page(request):
    """
    Renders the landing page of the application.
    """
    return render(request, 'core/landing_page.html', {})

@login_required
def profile_view(request):
    """ Renders the user's profile page and handles form updates. """
    if request.method == 'POST':
        user = request.user
        first_name = request.POST.get('first_name')
        
        if first_name is not None:
            user.first_name = first_name.strip()
            user.save()
            messages.success(request, 'Profile updated successfully.')
        return redirect('core:profile')

    return render(request, 'core/profile.html')

