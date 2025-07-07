from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt # Only for API endpoints if needed, but not for this view

# Assuming you have a User model or similar to check for guest usage
# from user.models import UserProfile # Example if you track guest usage

# Placeholder for a simple guest usage tracking (in-memory, not persistent)
# In a real app, this would be database-backed or session-based.
guest_calculator_usage = {} 

def calculator_view(request):
    """
    Renders the stock calculator page.
    Handles guest access logic.
    """
    can_use_calculator_free = True
    show_login_popup = False
    user_feedback_message = ""

    if not request.user.is_authenticated:
        # Check if the user has already used the calculator as a guest in this session
        # For a simple in-memory check, we'll use a session variable
        if request.session.get('calculator_used_as_guest', False):
            can_use_calculator_free = False
            show_login_popup = True
            user_feedback_message = "You have used the calculator once as a guest. Please log in or sign up to continue."
        else:
            # Mark that this session has used the calculator once
            request.session['calculator_used_as_guest'] = True
            user_feedback_message = "You can use the calculator once as a guest. Log in or sign up for unlimited access!"

    context = {
        'can_use_calculator_free': can_use_calculator_free,
        'show_login_popup': show_login_popup,
        'user_feedback_message': user_feedback_message,
    }
    return render(request, 'portfolio/stock_calculator.html', context)


# NEW VIEW: Capital Gains Estimator
def capital_gains_estimator_view(request):
    """
    Renders the Capital Gains Estimator page.
    This page will be accessible to all users for now.
    """
    context = {} # No specific context needed initially, can add later
    return render(request, 'portfolio/capital_gains_estimator.html', context)