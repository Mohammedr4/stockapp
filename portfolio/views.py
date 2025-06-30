from django.shortcuts import render, redirect
from django.urls import reverse_lazy
from django.contrib import messages # To display messages to the user

def calculator_view(request):
    """
    Renders the stock reprice calculator page.
    Allows one free use for unauthenticated users, then prompts for login/signup.
    Authenticated users have unlimited access.
    """
    can_use_calculator_free = False # Flag for initial JS behavior
    show_login_popup = False # Flag to trigger the modal
    
    # Initialize message for the user
    user_feedback_message = ""

    if request.user.is_authenticated:
        # Logged-in users have full access
        can_use_calculator_free = True # They can use it freely
        user_feedback_message = f"Welcome back, {request.user.username}! Use the calculator as much as you like."
        
        # IMPORTANT: Clear session count for authenticated users, if it exists
        # This ensures a clean state if they were previously anonymous
        if 'calculator_used_count' in request.session:
            del request.session['calculator_used_count']
            request.session.modified = True
    else:
        # Anonymous user logic
        session_key_name = 'calculator_used_count'
        # Get current count, default to 0 if not set
        used_count = request.session.get(session_key_name, 0)

        # IMPORTANT: Logic for one-time use vs. restriction
        if used_count == 0:
            # First time user in this session - allow use and mark it
            request.session[session_key_name] = 1 # Mark as used once
            request.session.modified = True # Ensure session is marked as modified
            can_use_calculator_free = True
            user_feedback_message = "Welcome! Use the calculator once for free."
        else:
            # Second or subsequent time in this session - restrict and show popup
            show_login_popup = True
            user_feedback_message = "Please login or sign up to continue using the calculator."
            # Increment count for tracking, though only 0 vs >0 matters for this logic
            # This line is primarily for debugging/logging, the 'if used_count == 0' handles restriction
            request.session[session_key_name] = used_count + 1 
            request.session.modified = True # Ensure session is marked as modified

    context = {
        'title': 'Stock Reprice Calculator',
        'can_use_calculator_free': can_use_calculator_free, # Passed to JS
        'show_login_popup': show_login_popup, # Passed to JS
        'user_feedback_message': user_feedback_message, # Optional, for initial feedback
        'login_url': reverse_lazy('login'),
        'register_url': reverse_lazy('register'),
    }
    return render(request, 'portfolio/stock_calculator.html', context)