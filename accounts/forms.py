# accounts/forms.py
from django import forms
from django import forms

class CustomSignupForm(forms.Form):
    first_name = forms.CharField(
        max_length=50, 
        label='First Name', 
        required=True,
        widget=forms.TextInput(attrs={'placeholder': 'Jane'})
    )

    def signup(self, request, user):
        # Allauth will pass the newly created user here.
        # We can directly modify and save the extended fields.
        user.first_name = self.cleaned_data['first_name'].strip()
        
        # Fallback to saving email as username if django forces a username column
        if not user.username:
            user.username = user.email
            
        user.save()
        return user