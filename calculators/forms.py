# calculators/forms.py

from django import forms
from crispy_forms.helper import FormHelper # Keep if you use crispy forms for other forms or layouts
from crispy_forms.layout import Layout, Submit, Field, HTML, Row, Column # Keep if you use crispy forms for other forms or layouts
from decimal import Decimal # Essential for precise financial calculations
import datetime # For date field default/initial values (if used elsewhere)

class StockRepriceForm(forms.Form):
    # Field for existing holdings
    stock_symbol = forms.CharField(
        max_length=10, 
        required=True, 
        label="Stock Symbol (e.g., AAPL)",
        widget=forms.TextInput(attrs={'placeholder': 'e.g., AAPL'})
    )
    current_shares = forms.DecimalField(
        max_digits=15, 
        decimal_places=4, 
        min_value=Decimal('0'), 
        required=True, 
        label="Current Shares Held",
        widget=forms.NumberInput(attrs={'step': '0.0001', 'placeholder': 'e.g., 100.00'})
    )
    average_buy_price = forms.DecimalField(
        max_digits=15, 
        decimal_places=4, 
        min_value=Decimal('0'), 
        required=True, 
        label="Average Buy Price ($)",
        widget=forms.NumberInput(attrs={'step': '0.0001', 'placeholder': 'e.g., 150.75'})
    )
    current_market_price = forms.DecimalField(
        max_digits=15, 
        decimal_places=4, 
        min_value=Decimal('0.01'), # Market price should be positive
        required=True, 
        label="Current Market Price ($)",
        widget=forms.NumberInput(attrs={'step': '0.0001', 'placeholder': 'e.g., 140.20'})
    )

    # Calculation mode (radio buttons)
    CALCULATION_MODE_CHOICES = [
        ('shares', 'By Additional Shares'),
        ('price', 'By Target Average Price'),
    ]
    calculation_mode = forms.ChoiceField(
        choices=CALCULATION_MODE_CHOICES, 
        widget=forms.RadioSelect, 
        initial='shares', # Default to 'By Additional Shares'
        label="Choose Calculation Mode"
    )

    # Fields specific to 'shares' mode (not required initially)
    additional_shares_to_buy = forms.DecimalField(
        max_digits=15, 
        decimal_places=4, 
        min_value=Decimal('0'), 
        required=False, # Set required via JavaScript based on mode
        label="Additional Shares to Buy",
        widget=forms.NumberInput(attrs={'step': '0.0001', 'placeholder': 'e.g., 50.00'})
    )

    # Fields specific to 'price' mode (not required initially)
    target_average_price = forms.DecimalField(
        max_digits=15, 
        decimal_places=4, 
        min_value=Decimal('0.01'), 
        required=False, # Set required via JavaScript based on mode
        label="Target Average Price ($)",
        widget=forms.NumberInput(attrs={'step': '0.0001', 'placeholder': 'e.g., 145.00'})
    )

    def clean(self):
        cleaned_data = super().clean()
        calculation_mode = cleaned_data.get('calculation_mode')
        current_shares = cleaned_data.get('current_shares')
        average_buy_price = cleaned_data.get('average_buy_price')
        current_market_price = cleaned_data.get('current_market_price')
        additional_shares_to_buy = cleaned_data.get('additional_shares_to_buy')
        target_average_price = cleaned_data.get('target_average_price')

        # Custom validation for 'shares' mode
        if calculation_mode == 'shares':
            if additional_shares_to_buy is None or additional_shares_to_buy < 0:
                self.add_error('additional_shares_to_buy', "This field is required and must be zero or a positive number for 'By Additional Shares' mode.")
        elif calculation_mode == 'price':
            if target_average_price is None or target_average_price <= 0:
                self.add_error('target_average_price', "This field is required and must be a positive number for 'By Target Average Price' mode.")
            
            # Specific validation for target average price
            if current_shares is not None and average_buy_price is not None and current_market_price is not None and target_average_price is not None:
                if target_average_price >= average_buy_price:
                    self.add_error('target_average_price', "Target average price must be lower than your current average buy price to reprice down.")
                if target_average_price <= current_market_price:
                    self.add_error('target_average_price', "Target average price must be higher than the current market price to be achievable by buying more.")
        
        return cleaned_data
    
# --- CapitalGainsForm (Existing form, ensure it's correctly indented and placed) ---
class CapitalGainsForm(forms.Form):
    asset_name = forms.CharField(
        label="Stock Symbol / Asset Name",
        max_length=100,
        help_text="e.g., TSLA, Apple Stock",
        widget=forms.TextInput(attrs={'placeholder': 'e.g., XYZ Corp'})
    )
    tax_rule_country = forms.ChoiceField(
        label="Calculate for:",
        choices=[('UK', 'United Kingdom (UK)'), ('US', 'United States (US)')],
        initial='UK',
        help_text="Select the country's tax rules for estimation."
    )
    purchase_date = forms.DateField(
        label="Buy Date",
        widget=forms.DateInput(attrs={'type': 'date'}),
        help_text="Date the asset was purchased (MM/DD/YYYY)."
    )
    sale_date = forms.DateField(
        label="Sell Date",
        widget=forms.DateInput(attrs={'type': 'date'}),
        help_text="Date the asset was sold (MM/DD/YYYY)."
    )
    shares_purchased = forms.IntegerField(
        label="Number of Shares Purchased",
        min_value=1,
        help_text="Total number of shares/units bought."
    )
    shares_sold = forms.IntegerField( 
        label="Number of Shares Sold",
        min_value=1,
        help_text="The number of shares/units being sold in this transaction."
    )
    purchase_price_per_share = forms.DecimalField(
        label="Buy Price per Share (£ or $)",
        max_digits=10,
        decimal_places=4,
        min_value=Decimal('0.01'),
        help_text="Price you paid per share/unit."
    )
    sale_price_per_share = forms.DecimalField(
        label="Sell Price per Share (£ or $)",
        max_digits=10,
        decimal_places=4,
        min_value=Decimal('0.01'),
        help_text="Price you received per share/unit."
    )
    commission_purchase = forms.DecimalField(
        label="Buy Commission/Fees (£ or $)",
        max_digits=10,
        decimal_places=2,
        required=False,
        initial=Decimal('0.00'),
        help_text="Any fees paid when purchasing (optional)."
    )
    commission_sale = forms.DecimalField(
        label="Sell Commission/Fees (£ or $)",
        max_digits=10,
        decimal_places=2,
        required=False,
        initial=Decimal('0.00'),
        help_text="Any fees paid when selling (optional)."
    )
    annual_taxable_income = forms.DecimalField(
        label="Your Annual Taxable Income (£ or $)",
        max_digits=12,
        decimal_places=2,
        min_value=Decimal('0.00'),
        required=False,
        help_text="Estimated taxable income for the current tax year."
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
        help_text="Your IRS tax filing status."
    )

    def clean(self):
        cleaned_data = super().clean()
        purchase_date = cleaned_data.get('purchase_date')
        sale_date = cleaned_data.get('sale_date')
        shares_purchased = cleaned_data.get('shares_purchased')
        shares_sold = cleaned_data.get('shares_sold') 

        tax_rule_country = cleaned_data.get('tax_rule_country')
        annual_taxable_income = cleaned_data.get('annual_taxable_income')
        us_filing_status = cleaned_data.get('us_filing_status')

        if purchase_date and sale_date and sale_date < purchase_date:
            self.add_error('sale_date', "Sale date cannot be before purchase date.")

        if shares_purchased is not None and shares_sold is not None:
            if shares_sold > shares_purchased:
                self.add_error('shares_sold', "Shares sold cannot exceed shares purchased for this specific transaction. For partial sales, please adjust shares purchased to match shares sold.")
            if shares_sold <= 0:
                self.add_error('shares_sold', "Number of shares sold must be a positive number.")

        # Conditional validation for tax inputs
        if tax_rule_country: # If a country is selected, then validate annual_taxable_income
            if annual_taxable_income is None: 
                self.add_error('annual_taxable_income', "Please provide your annual taxable income for tax estimation.")
            
            if tax_rule_country == 'US' and not us_filing_status:
                self.add_error('us_filing_status', "Please select your filing status for US tax estimation.")

        return cleaned_data