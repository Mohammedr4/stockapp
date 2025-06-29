from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import authenticate, login as auth_login_func, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm # Correctly importing Django's built-in AuthenticationForm
from .forms import UserRegisterForm # IMPORTANT: Corrected import to match UserRegisterForm in user/forms.py
from django.core.mail import EmailMultiAlternatives
from django.template.loader import get_template
# from django.template import Context # Context is often not needed in modern Django template rendering

#################### index page ####################################### 
# This is the home page of your user app.
def index(request):
    return render(request, 'user/index.html', {'title':'Home'})
 
########### register view ##################################### 
# Handles user registration.
def register(request):
    if request.method == 'POST':
        form = UserRegisterForm(request.POST) # Using UserRegisterForm
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
            subject, from_email, to = 'Welcome to the Stock Reprice Calculator!', os.environ.get('EMAIL_USER', 'your_email@gmail.com'), email # IMPORTANT: Use EMAIL_USER from settings
            
            # Create an EmailMultiAlternatives object for HTML email
            msg = EmailMultiAlternatives(subject, html_content, from_email, [to])
            msg.attach_alternative(html_content, "text/html") # Attach HTML content
            try:
                msg.send() # Send the email
                messages.success(request, f'Account for {username} has been created! Please check your email for a welcome message. You are now able to log in.')
            except Exception as e:
                messages.error(request, f'Account created but failed to send welcome email: {e}')
            # --- End Email Confirmation System ---

            return redirect('login') # Redirect to the login page after successful registration
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{error}") # Display specific error messages

    context = {
        'form': form,
        'title': 'Sign Up'
    }
    return render(request, 'user/register.html', context)


################ login view ################################################### 
# Handles user login.
def Login(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST) # Correctly using Django's built-in AuthenticationForm
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            # Authenticate the user
            user = authenticate(request, username=username, password=password)
            if user is not None:
                auth_login_func(request, user) # Log in the user using Django's built-in login function
                messages.success(request, f'Welcome back {username}!')
                # Redirect to the page defined in LOGIN_REDIRECT_URL in settings.py (e.g., /calculator/)
                return redirect('home') # Redirect to 'home' which is now the calculator
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

# Custom Logout View to clear session variable
from django.contrib.auth.views import LogoutView

class CustomLogoutView(LogoutView):
    def dispatch(self, request, *args, **kwargs):
        # Clear the calculator_used_count from the session upon logout
        if 'calculator_used_count' in request.session:
            del request.session['calculator_used_count']
        
        # Ensure the session is saved after modification
        request.session.modified = True 
        
        # Call the parent LogoutView's dispatch method to handle the actual logout logic
        return super().dispatch(request, *args, **kwargs)

