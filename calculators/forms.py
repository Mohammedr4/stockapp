# calculators/forms.py

from django import forms
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Submit, Field, HTML, Row, Column
from decimal import Decimal # Make sure Decimal is imported for forms
import datetime # For date field default/initial values

class StockRepriceForm(forms.Form):
    # Core Inputs for Current Holdings (from your HTML's "Current Holdings" card)
    stock_symbol = forms.CharField(
        max_length=10,
        label="Stock Symbol (e.g., TSLA)",
        help_text="The ticker symbol of the stock.",
        required=True
    )
    current_shares = forms.DecimalField( # Using DecimalField for precision and consistency
        min_value=Decimal('0'), # Allow 0 shares for new potential positions
        max_digits=15,
        decimal_places=4,
        label="Current Shares Held",
        help_text="The number of shares you currently own.",
        required=True
    )
    average_buy_price = forms.DecimalField(
        min_value=Decimal('0.00'), # Allow 0 for initial buy where avg price is current price
        max_digits=15,
        decimal_places=4,
        label="Average Buy Price ($)",
        help_text="Your current average purchase price per share.",
        required=True
    )
    current_market_price = forms.DecimalField(
        min_value=Decimal('0.01'), # Current price should generally be positive for this calc
        max_digits=15,
        decimal_places=4,
        label="Current Market Price ($)",
        help_text="The current market price per share of the stock.",
        required=True
    )

    # Calculation Mode Selector (from your HTML's "Reprice Calculator" card, <select id="calculationMode">)
    CALCULATION_MODES = [
        ('shares', 'Calculate by Number of Shares'),
        ('price', 'Calculate by Target Average Price'),
    ]
    calculation_mode = forms.ChoiceField(
        choices=CALCULATION_MODES,
        label="Calculation Mode",
        initial='shares', # Matches the default option in your HTML
        required=True
    )

    # Inputs specific to each mode (from your HTML, these are conditionally displayed in JS)
    # We make them not required at the form level, and handle conditional validation in the view
    additional_shares_to_buy = forms.DecimalField( # Matches <input type="number" id="newShares">
        min_value=Decimal('0'),
        max_digits=15,
        decimal_places=4,
        label="Additional Shares to Buy",
        help_text="Number of new shares you plan to buy.",
        required=False # Only required if 'shares' mode is selected
    )
    target_average_price = forms.DecimalField( # Matches <input type="number" id="targetAvgPrice">
        min_value=Decimal('0.01'), # Target price should be positive
        max_digits=15,
        decimal_places=4,
        label="Target Average Price ($)",
        help_text="Your desired new average price per share.",
        required=False # Only required if 'price' mode is selected
    )

    # Hidden field for onboarding logic (as per our "try before you commit" discussion)
    user_authenticated = forms.BooleanField(required=False, widget=forms.HiddenInput())

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
    shares_sold = forms.IntegerField( # <<< ADDED THIS FIELD >>>
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

    # NEW FIELDS FOR TAX ESTIMATION
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
                # This depends on your business logic. If you want to allow partial sales
                # of a larger block bought earlier, this check needs to be more complex
                # and involve a proper "cost basis accounting" method (FIFO, LIFO, etc.).
                # For a simple single transaction, this is a reasonable check.
                self.add_error('shares_sold', "Shares sold cannot exceed shares purchased for this specific transaction. For partial sales, please adjust shares purchased to match shares sold.")
            if shares_sold <= 0:
                self.add_error('shares_sold', "Number of shares sold must be a positive number.")


        # Conditional validation for tax inputs
        # Only require these if the user has explicitly selected a country
        # and there's a gross gain to potentially tax.
        # The view handles the 'info' message if no tax country is selected.
        if tax_rule_country: # If a country is selected, then validate annual_taxable_income
            if annual_taxable_income is None: 
                self.add_error('annual_taxable_income', "Please provide your annual taxable income for tax estimation.")
            
            if tax_rule_country == 'US' and not us_filing_status:
                self.add_error('us_filing_status', "Please select your filing status for US tax estimation.")

        return cleaned_data