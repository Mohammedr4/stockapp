# accounts/forms.py
from django import forms
# We remove "from allauth.account.forms import SignupForm" to prevent the circular import

class CustomSignupForm(forms.Form):
    # This form no longer needs to inherit from SignupForm
    display_name = forms.CharField(
        max_length=100, 
        label='Display Name', 
        required=True,
        widget=forms.TextInput(attrs={'placeholder': 'e.g., John Doe'})
    )

    def signup(self, request, user):
        user.first_name = self.cleaned_data['display_name'].split(' ')[0]
        if len(self.cleaned_data['display_name'].split(' ')) > 1:
            user.last_name = ' '.join(self.cleaned_data['display_name'].split(' ')[-1:])
        user.save()
        return user