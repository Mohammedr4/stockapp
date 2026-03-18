# accounts/adapters.py
from allauth.account.adapter import DefaultAccountAdapter
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from django.conf import settings
from django.urls import reverse_lazy
from django.contrib import messages

class CustomAccountAdapter(DefaultAccountAdapter):
    """
    Handles local account signups and password resets.
    """
    def get_password_reset_redirect_url(self, request, user):
        """
        Redirects to the login page after a successful password reset.
        """
        messages.success(request, 'Your password has been changed successfully. You may now sign in.')
        return reverse_lazy('account_login')

class CustomSocialAccountAdapter(DefaultSocialAccountAdapter):
    """
    Handles social account (Google) signups.
    """
    def populate_user(self, request, sociallogin, data):
        """
        This is called when a user signs up via Google.
        We safely extract the email and assign names.
        """
        user = super().populate_user(request, sociallogin, data)
        
        email = data.get('email')
        if email:
             user.username = email
             
        user.first_name = data.get('given_name', '')
        user.last_name = data.get('family_name', '')
        return user