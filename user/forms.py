from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm

# Custom user registration form extending Django's UserCreationForm
class UserRegisterForm(UserCreationForm):
    # Add custom fields for email, phone_no, first_name, last_name
    email = forms.EmailField(required=True) # Email field, made required
    phone_no = forms.CharField(max_length = 20, required=False) # Phone number field
    first_name = forms.CharField(max_length = 20, required=False) # First name field
    last_name = forms.CharField(max_length = 20, required=False) # Last name field

    class Meta:
        # Link this form to Django's built-in User model
        model = User
        # Define the fields to be included in the form
        # 'password1' and 'password2' are handled by UserCreationForm for password confirmation
        fields = ['username', 'email', 'phone_no', 'first_name', 'last_name']

    # Override the save method to handle saving custom fields
    def save(self, commit=True):
        user = super().save(commit=False) # Call parent save method without committing to DB
        user.email = self.cleaned_data['email']
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        # Note: phone_no is not a default field in Django's User model.
        # If you need to save phone_no, you'd need to extend the User model
        # or create a separate UserProfile model linked to User.
        # For this example, it's included in the form but won't be saved to User model directly.
        # To save phone_no, you would need to:
        # 1. Extend the User model or create a OneToOneField to a Profile model.
        # 2. Modify this save method to save phone_no to the extended model/profile.
        if commit:
            user.save()
        return user
