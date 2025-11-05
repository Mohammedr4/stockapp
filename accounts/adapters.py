# accounts/adapters.py
from allauth.account.adapter import DefaultAccountAdapter
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from django.conf import settings

class CustomAccountAdapter(DefaultAccountAdapter):
    
    def get_password_reset_redirect_url(self, request, user):
        """
        Redirects to the login page after a successful password reset.
        """
        from django.urls import reverse_lazy
        from django.contrib import messages
        messages.success(request, 'Your password has been changed successfully. You may now sign in.')
        return reverse_lazy('account_login')

class CustomSocialAccountAdapter(DefaultSocialAccountAdapter):
    
    def populate_user(self, request, sociallogin, data):
        """
        This is the critical fix. It takes the user data from Google
        and correctly populates the new User object.
        """
        user = super().populate_user(request, sociallogin, data)
        
        # Set username to be the email
        user.username = user.email
        
        # Set first and last name from Google data
        user.first_name = data.get('given_name', '')
        user.last_name = data.get('family_name', '')
        
        return user