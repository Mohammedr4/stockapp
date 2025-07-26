# portfolio/forms.py
from django import forms
from .models import StockHolding

class StockHoldingForm(forms.ModelForm):
    class Meta:
        model = StockHolding
        # You MUST include 'purchase_date' in the fields tuple
        fields = ['stock_symbol', 'quantity', 'purchase_price', 'purchase_date']
        # The widgets are correctly defined below this
        widgets = {
            'purchase_price': forms.NumberInput(attrs={'step': '0.01'}),
            'quantity': forms.NumberInput(attrs={'step': '0.0001'}), # Allows for fractional shares
            'purchase_date': forms.DateInput(attrs={'type': 'date'}),
        }