# accounts/adapters.py
from django.contrib import messages
from django.urls import reverse_lazy
from allauth.account.adapter import DefaultAccountAdapter

class CustomAccountAdapter(DefaultAccountAdapter):

    def populate_username(self, request, user):
        """
        Ensures a unique username is generated from the email address.
        """
        user.username = user.email

    def get_password_change_redirect_url(self, request, user):
        """
        After a user successfully changes their password,
        this redirects them to their profile page.
        """
        return reverse_lazy('core:profile')

    def get_password_reset_redirect_url(self, request, user):
        """
        After a user successfully resets a forgotten password,
        this redirects them to the login page and adds a success message.
        """
        messages.success(request, 'Your password has been changed successfully. You may now sign in.')
        return reverse_lazy('account_login')