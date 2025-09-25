# accounts/adapters.py
from django.contrib import messages
from allauth.account.adapter import DefaultAccountAdapter

class CustomAccountAdapter(DefaultAccountAdapter):

    def add_message(self, request, level, message_template, message_context=None, **kwargs):
        """
        This is a hook to customize messages. We'll use the standard Django messages.
        """
        if message_template == 'account/messages/password_reset_link_sent.txt':
            messages.success(request, 'Password reset e-mail has been sent.')
        else:
            # Fallback to default behavior for other messages if needed
            super().add_message(request, level, message_template, message_context, **kwargs)
    
    def get_password_reset_redirect_url(self, request, user):
        """
        Redirect to the login page after a successful password reset.
        """
        messages.success(request, 'Your password has been changed. You may sign in now.')
        return super().get_password_reset_redirect_url(request, user)