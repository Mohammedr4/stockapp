from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.urls import reverse_lazy # Import reverse_lazy for URL lookups

# In a real application, guest usage would be handled more robustly (e.g., database, more complex session management).
# For this demo, your session-based tracking is sufficient.

# IMPORTANT FIX: Added 'tab' as a parameter with a default value
def dashboard_view(request, tab='reprice'):
    """
    Renders the unified stock calculator dashboard.
    Handles guest access logic and determines the active tab.
    """
    can_use_calculator_free = False
    show_login_popup = False
    user_feedback_message = ""
    # The 'tab' parameter is now directly from the URL kwargs or defaults to 'reprice'
    # No need to get it from request.GET.get('tab', 'reprice') if it's passed directly.
    # However, if you want to allow /?tab=capital_gains, you'd combine this:
    # active_tab = request.GET.get('tab', tab) # This would prioritize GET param if present
    active_tab = tab # Use the 'tab' value passed from urls.py

    if request.user.is_authenticated:
        # Logged-in users have full access
        can_use_calculator_free = True
        user_feedback_message = f"Welcome back, {request.user.username}! Use the calculators as much as you like."
        
        # Clear session count for authenticated users, if it exists, to reset guest state
        if 'calculator_used_count' in request.session:
            del request.session['calculator_used_count']
            request.session.modified = True # Ensure session is marked as modified
    else:
        # Anonymous user logic
        session_key_name = 'calculator_used_count'
        used_count = request.session.get(session_key_name, 0)

        if used_count == 0:
            # First time user in this session - allow use and mark it
            request.session[session_key_name] = 1
            request.session.modified = True # Ensure session is marked as modified
            can_use_calculator_free = True
            user_feedback_message = "Welcome! You can use the calculator once for free."
        else:
            # Second or subsequent time in this session - restrict and show popup
            show_login_popup = True
            user_feedback_message = "Please login or sign up to continue using the calculator."
            # Increment count for tracking, though only 0 vs >0 matters for this logic
            request.session[session_key_name] = used_count + 1 
            request.session.modified = True # Ensure session is marked as modified

    context = {
        'title': 'Stock Calculators', # Unified title for the dashboard
        'can_use_calculator_free': can_use_calculator_free,
        'show_login_popup': show_login_popup,
        'user_feedback_message': user_feedback_message,
        'login_url': reverse_lazy('login'),
        'register_url': reverse_lazy('register'),
        'active_tab': active_tab, # Pass the active tab to the template
    }
    return render(request, 'portfolio/calculator_dashboard.html', context)

# IMPORTANT: The old capital_gains_estimator_view is no longer needed as dashboard_view handles it.
# You can remove or comment out the old capital_gains_estimator_view if you wish.
# def capital_gains_estimator_view(request):
#     context = {}
#     return render(request, 'portfolio/capital_gains_estimator.html', context)
