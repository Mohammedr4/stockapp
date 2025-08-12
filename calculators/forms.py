# calculators/forms.py

from django import forms
from decimal import Decimal

class StockRepriceForm(forms.Form):
    stock_symbol = forms.CharField(label="Stock Symbol (e.g., AAPL)", required=True)
    current_shares = forms.DecimalField(label="Current Shares Held", required=True)
    average_buy_price = forms.DecimalField(label="Average Buy Price ($)", required=True)
    current_market_price = forms.DecimalField(label="Current Market Price ($)", required=True)
    calculation_mode = forms.ChoiceField(
        label="Calculation Mode",
        choices=[('shares', 'Calculate by Number of Shares'), ('price', 'Calculate by Target Price')]
    )
    additional_shares_to_buy = forms.DecimalField(label="Additional Shares to Buy", required=False)
    target_average_price = forms.DecimalField(label="Target Average Price ($)", required=False)

    def clean(self):
        cleaned_data = super().clean()
        mode = cleaned_data.get("calculation_mode")
        
        if mode == 'shares' and cleaned_data.get('additional_shares_to_buy') is None:
            self.add_error('additional_shares_to_buy', 'This field is required.')
        
        if mode == 'price' and cleaned_data.get('target_average_price') is None:
            self.add_error('target_average_price', 'This field is required.')
            
        return cleaned_data

# ==============================================================================
# CAPITAL GAINS FORM (STYLED VERSION)
# ==============================================================================

class CapitalGainsForm(forms.Form):
    asset_name = forms.CharField(
        label="Stock Symbol / Asset Name",
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., XYZ Corp'})
    )
    tax_rule_country = forms.ChoiceField(
        label="Calculate for:",
        choices=[('UK', 'United Kingdom (UK)'), ('US', 'United States (US)')],
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    purchase_date = forms.DateField(
        label="Buy Date",
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
    )
    sale_date = forms.DateField(
        label="Sell Date",
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
    )
    shares_purchased = forms.IntegerField(
        label="Number of Shares Purchased",
        widget=forms.NumberInput(attrs={'class': 'form-control'})
    )
    shares_sold = forms.IntegerField(
        label="Number of Shares Sold",
        widget=forms.NumberInput(attrs={'class': 'form-control'})
    )
    purchase_price_per_share = forms.DecimalField(
        label="Buy Price per Share (£ or $)",
        widget=forms.NumberInput(attrs={'class': 'form-control'})
    )
    sale_price_per_share = forms.DecimalField(
        label="Sell Price per Share (£ or $)",
        widget=forms.NumberInput(attrs={'class': 'form-control'})
    )
    commission_purchase = forms.DecimalField(
        label="Buy Commission/Fees (£ or $)",
        required=False,
        widget=forms.NumberInput(attrs={'class': 'form-control'})
    )
    commission_sale = forms.DecimalField(
        label="Sell Commission/Fees (£ or $)",
        required=False,
        widget=forms.NumberInput(attrs={'class': 'form-control'})
    )
    annual_taxable_income = forms.DecimalField(
        label="Your Annual Taxable Income (£ or $)",
        required=False,
        widget=forms.NumberInput(attrs={'class': 'form-control'})
    )
    us_filing_status = forms.ChoiceField(
        label="Filing Status (US Only)",
        choices=[
            ('', 'Select Status'),
            ('single', 'Single'),
            ('married_jointly', 'Married Filing Jointly'),
            ('married_separately', 'Married Filing Separately'),
            ('head_of_household', 'Head of Household'),
        ],
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )

    def clean(self):
        cleaned_data = super().clean()
        # (Your existing clean method for this form goes here)
        return cleaned_data