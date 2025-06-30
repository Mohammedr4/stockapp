from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import authenticate, login as auth_login_func, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from .forms import UserRegisterForm
from django.core.mail import EmailMultiAlternatives
from django.template.loader import get_template
import os # Make sure os is imported for EMAIL_USER in welcome email

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
            htmly = get_template('user/Email.html')
            d = { 'username': username }
            html_content = htmly.render(d)

            subject = 'Welcome to the Stock Reprice Calculator!'
            from_email = os.environ.get('EMAIL_USER', 'your_email@gmail.com') # Use EMAIL_USER from settings or a default
            to = email
            
            msg = EmailMultiAlternatives(subject, html_content, from_email, [to])
            msg.attach_alternative(html_content, "text/html")
            try:
                msg.send()
                messages.success(request, f'Account for {username} has been created! Please check your email for a welcome message. You are now able to log in.')
            except Exception as e:
                messages.error(request, f'Account created but failed to send welcome email: {e}')
            # --- End Email Confirmation System ---

            return redirect('login')
        else:
            # If form is not valid on POST, messages are added in the loop
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{error}")
    else: # This 'else' block runs for GET requests
        form = UserRegisterForm() # IMPORTANT: Initialize form for GET requests here

    context = {
        'form': form, # 'form' is now guaranteed to be defined
        'title': 'Sign Up'
    }
    return render(request, 'user/register.html', context)
 
################ login view ################################################### 
# Handles user login.
def Login(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(request, username=username, password=password)
            if user is not None:
                auth_login_func(request, user)
                messages.success(request, f'Welcome back {username}!')
                return redirect('home') # Redirect to 'home' which is now the calculator
            else:
                messages.error(request, 'Invalid username or password.')
        else:
            messages.error(request, 'Invalid username or password.')
    else:
        form = AuthenticationForm()
    return render(request, 'user/login.html', {'form':form, 'title':'Login'})

# Example of a protected view (only accessible if logged in)
@login_required
def profile(request):
    return render(request, 'user/profile.html', {'title': 'Profile'})

# Custom Logout View to clear session variable
from django.contrib.auth.views import LogoutView

class CustomLogoutView(LogoutView):
    def dispatch(self, request, *args, **kwargs):
        if 'calculator_used_count' in request.session:
            del request.session['calculator_used_count']
        request.session.modified = True
        return super().dispatch(request, *args, **kwargs)
