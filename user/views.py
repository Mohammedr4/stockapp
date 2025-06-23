from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import authenticate, login as auth_login_func, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from .forms import UserRegisterForm
from django.core.mail import EmailMultiAlternatives
from django.template.loader import get_template
from django.template import Context # For older Django/Python versions, might need this, but usually just pass dict directly

#################### index page ####################################### 
# This is the home page of your user app.
def index(request):
    return render(request, 'user/index.html', {'title':'Home'})
 
########### register view ##################################### 
# Handles user registration.
def register(request):
    if request.method == 'POST':
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            user = form.save() # Save the user (including custom fields like email, first/last name)
            username = form.cleaned_data.get('username')
            email = form.cleaned_data.get('email')
            
            # --- Email Confirmation System ---
            # Renders the email template with user-specific data
            htmly = get_template('user/Email.html')
            d = { 'username': username }
            html_content = htmly.render(d) # Render the template to HTML string

            # Email details
            subject, from_email, to = 'Welcome to the Stock Reprice Calculator!', 'your_email@gmail.com', email # IMPORTANT: Update 'your_email@gmail.com' in settings.py too
            
            # Create an EmailMultiAlternatives object for HTML email
            msg = EmailMultiAlternatives(subject, html_content, from_email, [to])
            msg.attach_alternative(html_content, "text/html") # Attach HTML content
            msg.send() # Send the email
            # --- End Email Confirmation System ---

            messages.success(request, f'Account for {username} has been created! Please check your email for a welcome message. You are now able to log in.')
            return redirect('login') # Redirect to the login page after successful registration
    else:
        form = UserRegisterForm() # If GET request, create an empty form
    return render(request, 'user/register.html', {'form': form, 'title':'Register'})
 
################ login view ################################################### 
# Handles user login.
def Login(request): # Renamed from 'Login' to 'user_login' to avoid conflict with built-in login function
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST) # Use Django's built-in AuthenticationForm
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            # Authenticate the user
            user = authenticate(request, username=username, password=password)
            if user is not None:
                auth_login_func(request, user) # Log in the user using Django's built-in login function
                messages.success(request, f'Welcome back {username}!')
                # Redirect to the page defined in LOGIN_REDIRECT_URL in settings.py (e.g., /calculator/)
                return redirect('portfolio_calculator') 
            else:
                messages.error(request, 'Invalid username or password.') # Changed from info to error for clarity
        else:
            messages.error(request, 'Invalid username or password.') # Form is not valid
    else:
        form = AuthenticationForm() # If GET request, create an empty authentication form
    return render(request, 'user/login.html', {'form':form, 'title':'Login'})

# Example of a protected view (only accessible if logged in)
@login_required
def profile(request):
    # This view could be used for user profiles or dashboards
    return render(request, 'user/profile.html', {'title': 'Profile'})
