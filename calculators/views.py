# calculators/views.py
import json
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.contrib import messages
from decimal import Decimal, InvalidOperation
from datetime import date
from dateutil.relativedelta import relativedelta # Make sure you have 'pip install python-dateutil'

from .forms import StockRepriceForm
from .forms import CapitalGainsForm

FREE_USE_LIMIT = 1
FREE_CGT_USE_LIMIT = 1 # Your defined limit for Capital Gains Estimator

# --- Helper Functions for Capital Gains Calculations ---
def calculate_holding_period(purchase_date, sale_date):
    """Calculates the holding period between two dates."""
    if not purchase_date or not sale_date:
        return "N/A"
    delta = relativedelta(sale_date, purchase_date)
    years = delta.years
    months = delta.months
    days = delta.days

    if years >= 1:
        return f"{years} year(s), {months} month(s), {days} day(s)"
    elif months > 0:
        return f"{months} month(s), {days} day(s)"
    else:
        return f"{days} day(s)"

def get_gain_loss_type(purchase_date, sale_date):
    """Determines if the gain/loss is short-term or long-term (US-centric)."""
    if not purchase_date or not sale_date:
        return "N/A"
    
    # Holding period of 1 year or more is long-term
    # Check if sale_date is exactly 1 year or more after purchase_date
    if sale_date >= purchase_date + relativedelta(years=1):
        return "Long-Term"
    else:
        return "Short-Term"

def calculate_uk_cgt(gross_gain, annual_income):
    """
    Estimates UK Capital Gains Tax.
    THIS IS A HIGHLY SIMPLIFIED ESTIMATION FOR DEMONSTRATION.
    DO NOT USE FOR ACTUAL TAX ADVICE.
    """
    ANNUAL_EXEMPT_AMOUNT_UK = Decimal('3000.00') # For 2024/2025, check current year
    BASIC_RATE_THRESHOLD_UK = Decimal('50270.00') # This is for income tax, CGT uses different bands generally
    
    # Simplified UK CGT rates for property/other assets (not shares)
    # Shares have a different rate: 10% (basic) / 20% (higher)
    BASIC_RATE_CGT = Decimal('0.10') # 10%
    HIGHER_RATE_CGT = Decimal('0.20') # 20%

    cgt_payable = Decimal('0.00')

    taxable_gain = max(Decimal('0.00'), gross_gain - ANNUAL_EXEMPT_AMOUNT_UK)

    if taxable_gain <= 0:
        return Decimal('0.00')

    # The threshold for higher rate CGT depends on your total taxable income (including income)
    # This is a simplification. A full calculation would add gross_gain to income
    # and then apply the relevant rate to the gain based on which band it falls into.
    # For demonstration, we assume income uses up the basic rate band first.
    remaining_basic_rate_band = max(Decimal('0.00'), BASIC_RATE_THRESHOLD_UK - annual_income)

    if taxable_gain <= remaining_basic_rate_band:
        cgt_payable = taxable_gain * BASIC_RATE_CGT
    else:
        cgt_payable += remaining_basic_rate_band * BASIC_RATE_CGT
        cgt_payable += (taxable_gain - remaining_basic_rate_band) * HIGHER_RATE_CGT

    return cgt_payable.quantize(Decimal('0.01'))

def calculate_us_cgt(gross_gain, annual_income, filing_status, holding_period_type):
    """
    Estimates US Capital Gains Tax.
    THIS IS A HIGHLY SIMPLIFIED ESTIMATION FOR DEMONSTRATION.
    DO NOT USE FOR ACTUAL TAX ADVICE. Tax brackets change annually.
    """
    cgt_payable = Decimal('0.00')

    # Simplified Long-Term Capital Gains Brackets for 2024 (approximate)
    LT_BRACKETS = {
        'single': [
            (Decimal('0'), Decimal('47025'), Decimal('0.00')),
            (Decimal('47026'), Decimal('518900'), Decimal('0.15')),
            (Decimal('518901'), Decimal('inf'), Decimal('0.20'))
        ],
        'married_jointly': [
            (Decimal('0'), Decimal('94050'), Decimal('0.00')),
            (Decimal('94051'), Decimal('583750'), Decimal('0.15')),
            (Decimal('583751'), Decimal('inf'), Decimal('0.20'))
        ],
        'married_separately': [ # Added for more complete demo
            (Decimal('0'), Decimal('47025'), Decimal('0.00')),
            (Decimal('47026'), Decimal('291875'), Decimal('0.15')),
            (Decimal('291876'), Decimal('inf'), Decimal('0.20'))
        ],
        'head_of_household': [ # Added for more complete demo
            (Decimal('0'), Decimal('63000'), Decimal('0.00')),
            (Decimal('63001'), Decimal('329300'), Decimal('0.15')),
            (Decimal('329301'), Decimal('inf'), Decimal('0.20'))
        ],
    }

    if gross_gain <= 0:
        return Decimal('0.00')

    if holding_period_type == "Short-Term":
        # Short-term gains are taxed at ordinary income tax rates.
        # This is a simplification; actual tax is complex and marginal.
        # These are 2024 ordinary income tax brackets (approximate)
        ORDINARY_RATES_SIMPLIFIED = [
            (Decimal('0'), Decimal('0.10')),
            (Decimal('11600'), Decimal('0.12')),
            (Decimal('47150'), Decimal('0.22')),
            (Decimal('100525'), Decimal('0.24')),
            (Decimal('191950'), Decimal('0.32')),
            (Decimal('243725'), Decimal('0.35')),
            (Decimal('609350'), Decimal('0.37'))
        ]
        
        # This is a very rough estimate. A proper calculation would determine
        # which tax bracket the *gain itself* falls into, given total taxable income.
        total_taxable_income = annual_income + gross_gain
        applicable_rate = Decimal('0.00')
        for threshold, rate in ORDINARY_RATES_SIMPLIFIED:
            if total_taxable_income > threshold:
                applicable_rate = rate
        cgt_payable = gross_gain * applicable_rate

    else: # Long-Term
        brackets = LT_BRACKETS.get(filing_status, LT_BRACKETS['single'])
        
        # Calculate the portion of gain falling into each bracket
        # This is a more accurate way to calculate marginal tax
        income_after_other_gains = annual_income # Assuming `annual_income` is pre-CGT
        remaining_gain = gross_gain
        
        for lower, upper, rate in brackets:
            if remaining_gain <= 0:
                break

            # Calculate the portion of the current bracket that this gain could use
            bracket_top_for_gain = upper - income_after_other_gains
            
            if bracket_top_for_gain <= 0 and upper != Decimal('inf'): # If income fills this bracket, move to next
                continue

            # Amount of gain that falls into this bracket
            gain_in_this_bracket = min(remaining_gain, bracket_top_for_gain)
            
            if lower <= income_after_other_gains: # If income already covers or starts in this bracket
                taxable_at_this_rate = max(Decimal('0.00'), gross_gain + annual_income - lower) # Portion of total (income+gain) in this bracket
                
                if upper != Decimal('inf'):
                    taxable_at_this_rate = min(taxable_at_this_rate, upper - lower)

                # Only tax the gain, not the income already covered
                gain_portion_in_this_bracket = max(Decimal('0.00'), min(gross_gain, upper - annual_income - cgt_payable)) # Very tricky logic
                
                # Simpler approach: find the rate for the TOTAL (income + gain)
                effective_income_for_cgt_rate = annual_income + gross_gain
                if effective_income_for_cgt_rate > lower:
                    if upper == Decimal('inf') or effective_income_for_cgt_rate <= upper:
                        cgt_payable = gross_gain * rate
                        break
            else: # If gain pushes income into this new bracket
                taxable_amount = min(remaining_gain, upper - lower) if upper != Decimal('inf') else remaining_gain
                cgt_payable += taxable_amount * rate
                remaining_gain -= taxable_amount
                
    return cgt_payable.quantize(Decimal('0.01'))


# --- Existing stock_reprice_calculator view (no changes needed here) ---
def stock_reprice_calculator(request):
    print(f"DEBUG: User authenticated = {request.user.is_authenticated}")
    print(f"DEBUG: User object = {request.user}")

    form = StockRepriceForm()
    results = {
        'total_cost_price': Decimal('0.00'),
        'current_portfolio_value': Decimal('0.00'),
        'p_l_initial': Decimal('0.00'),
        'new_average_price': Decimal('0.00'),
        'total_investment': Decimal('0.00'),
        'additional_shares_needed': Decimal('0.00'),
        'total_shares_after_purchase': Decimal('0.00'),
        'cost_of_new_shares': Decimal('0.00'),
        'portfolio_value_after_purchase': Decimal('0.00'),
        'p_l_after_purchase': Decimal('0.00'),
        'mode': '',
        'calculation_successful': False,
    }
    calculation_allowed = True
    show_modal_for_signup = False

    if request.method == 'GET':
        if not request.user.is_authenticated:
            free_uses = request.session.get('free_uses_count', 0)
            if free_uses >= FREE_USE_LIMIT:
                calculation_allowed = False
                show_modal_for_signup = True
                messages.info(request, "You've used your free calculation. Please log in or sign up for unlimited access!")
                context = {
                    'form': form,
                    'results': results,
                    'calculation_allowed': calculation_allowed,
                    'show_modal_for_signup': show_modal_for_signup,
                }
                return render(request, 'calculators/stock_reprice_calculator.html', context)

    elif request.method == 'POST':
        form = StockRepriceForm(request.POST)
        if form.is_valid():
            if not request.user.is_authenticated:
                free_uses = request.session.get('free_uses_count', 0)
                if free_uses < FREE_USE_LIMIT:
                    request.session['free_uses_count'] = free_uses + 1
                else:
                    calculation_allowed = False
                    show_modal_for_signup = True
                    messages.info(request, "You've used your free calculation. Please log in or sign up for unlimited access!")
                    context = {
                        'form': form,
                        'results': results,
                        'calculation_allowed': calculation_allowed,
                        'show_modal_for_signup': show_modal_for_signup,
                    }
                    return render(request, 'calculators/stock_reprice_calculator.html', context)
            
            if calculation_allowed:
                stock_symbol = form.cleaned_data['stock_symbol']
                current_shares = form.cleaned_data['current_shares']
                average_buy_price = form.cleaned_data['average_buy_price']
                current_market_price = form.cleaned_data['current_market_price']
                calculation_mode = form.cleaned_data['calculation_mode']

                initial_total_cost_price = current_shares * average_buy_price
                current_portfolio_value = current_shares * current_market_price
                current_profit_loss = current_portfolio_value - initial_total_cost_price

                results.update({
                    'total_cost_price': initial_total_cost_price,
                    'current_portfolio_value': current_portfolio_value,
                    'p_l_initial': current_profit_loss,
                    'calculation_successful': True,
                })

                if calculation_mode == 'shares':
                    additional_shares_to_buy = form.cleaned_data['additional_shares_to_buy']
                    results['mode'] = 'by_shares'

                    if additional_shares_to_buy < 0:
                        messages.error(request, "Additional shares must be zero or a positive number.")
                        results['calculation_successful'] = False
                    else:
                        cost_of_new_shares = additional_shares_to_buy * current_market_price
                        new_total_shares = current_shares + additional_shares_to_buy
                        new_total_investment = initial_total_cost_price + cost_of_new_shares
                        
                        new_average_price = Decimal('0.00')
                        if new_total_shares > 0:
                            new_average_price = new_total_investment / new_total_shares
                        
                        portfolio_value_after_purchase = new_total_shares * current_market_price
                        p_l_after_purchase = portfolio_value_after_purchase - new_total_investment

                        results.update({
                            'new_average_price': new_average_price,
                            'total_investment': new_total_investment,
                            'additional_shares_needed': additional_shares_to_buy,
                            'total_shares_after_purchase': new_total_shares,
                            'cost_of_new_shares': cost_of_new_shares,
                            'portfolio_value_after_purchase': portfolio_value_after_purchase,
                            'p_l_after_purchase': p_l_after_purchase,
                        })

                elif calculation_mode == 'price':
                    target_average_price = form.cleaned_data['target_average_price']
                    results['mode'] = 'by_target_avg_price'

                    if target_average_price <= 0:
                        messages.error(request, "Target average price must be a positive value.")
                        results['calculation_successful'] = False
                    elif target_average_price >= average_buy_price:
                        messages.error(request, "Target average price must be lower than your current average buy price to reprice down.")
                        results['calculation_successful'] = False
                    elif target_average_price <= current_market_price:
                        messages.error(request, "Target average price must be higher than the current market price to be achievable by buying more.")
                        results['calculation_successful'] = False
                    else:
                        denominator = current_market_price - target_average_price
                        if denominator == Decimal('0'):
                            messages.error(request, "Cannot calculate: Target price is equal to current market price.")
                            results['calculation_successful'] = False
                        else:
                            numerator = current_shares * (target_average_price - average_buy_price)
                            additional_shares_needed = numerator / denominator
                            
                            if additional_shares_needed < 0:
                                messages.error(request, "Cannot calculate: The target average price requires selling shares, not buying more.")
                                results['calculation_successful'] = False
                            else:
                                additional_shares_needed = additional_shares_needed.quantize(Decimal('0.0001'))
                                
                                cost_of_new_shares = additional_shares_needed * current_market_price
                                new_total_shares = current_shares + additional_shares_needed
                                new_total_investment = initial_total_cost_price + cost_of_new_shares
                                
                                portfolio_value_after_purchase = new_total_shares * current_market_price
                                p_l_after_purchase = portfolio_value_after_purchase - new_total_investment

                                results.update({
                                    'new_average_price': target_average_price,
                                    'total_investment': new_total_investment,
                                    'additional_shares_needed': additional_shares_needed,
                                    'total_shares_after_purchase': new_total_shares,
                                    'cost_of_new_shares': cost_of_new_shares,
                                    'portfolio_value_after_purchase': portfolio_value_after_purchase,
                                    'p_l_after_purchase': p_l_after_purchase,
                                })
        else: # Form is NOT valid on POST
            messages.error(request, "Please correct the errors below.")
            results['calculation_successful'] = False

    context = {
        'form': form,
        'results': results,
        'calculation_allowed': calculation_allowed,
        'show_modal_for_signup': show_modal_for_signup,
    }
    return render(request, 'calculators/stock_reprice_calculator.html', context)


@login_required
def calculators_index(request):
    calculators = [
        {
            'name': 'Capital Gains Estimator',
            'description': 'Calculate potential capital gains/losses and estimate tax liability based on UK or US rules.',
            'url_name': 'calculators:capital_gains_estimator',
            'icon': 'fas fa-chart-line'
        },
        {
            'name': 'Stock Reprice Calculator',
            'description': 'Adjust historical stock prices for splits, dividends, or re-evaluate performance over time.',
            'url_name': 'calculators:stock_reprice_calculator',
            'icon': 'fas fa-sync-alt'
        },
    ]
    context = {
        'calculators': calculators,
    }
    return render(request, 'calculators/index.html', context) 

def capital_gains_estimator(request): # Removed @login_required to allow free uses for anonymous users
    form = CapitalGainsForm() 
    
    # Initialize all result variables to their default (empty/zero) states
    results = {
        'calculation_successful': False, # Renamed to clearly indicate summary calculation status
        'tax_calculation_successful': False, # New flag for tax-specific calculation status
        'asset_name': '',
        'total_purchase_cost': Decimal('0.00'),
        'total_sale_proceeds': Decimal('0.00'),
        'gross_gain_loss': Decimal('0.00'),
        'holding_period': 'N/A',
        'gain_loss_type': 'N/A',
        'estimated_tax': Decimal('0.00'),
        'net_gain_loss': Decimal('0.00'),
        'tax_country': '',
        'tax_currency': '',
    }

    calculation_allowed = True
    show_modal_for_signup = False

    # --- Free Use Limit Check for GET Request ---
    if request.method == 'GET':
        if not request.user.is_authenticated:
            free_cgt_uses = request.session.get('free_cgt_uses_count', 0)
            if free_cgt_uses >= FREE_CGT_USE_LIMIT:
                calculation_allowed = False
                show_modal_for_signup = True
                messages.info(request, "You've used your free Capital Gains calculation. Please log in or sign up for unlimited access!")
                context = {
                    'form': form,
                    'results': results, # Pass default empty results
                    'calculation_allowed': calculation_allowed,
                    'show_modal_for_signup': show_modal_for_signup,
                }
                return render(request, 'calculators/capital_gains_estimator.html', context)

    # --- Handle POST Request ---
    elif request.method == 'POST':
        form = CapitalGainsForm(request.POST)
        if form.is_valid():
            # --- Free Use Limit Check for POST Request ---
            if not request.user.is_authenticated:
                free_cgt_uses = request.session.get('free_cgt_uses_count', 0)
                if free_cgt_uses < FREE_CGT_USE_LIMIT:
                    request.session['free_cgt_uses_count'] = free_cgt_uses + 1
                else:
                    calculation_allowed = False
                    show_modal_for_signup = True
                    messages.info(request, "You've used your free Capital Gains calculation. Please log in or sign up for unlimited access!")
                    # If not allowed, return immediately without performing calculations
                    context = {
                        'form': form, # Pass the form back to retain user inputs
                        'results': results, # Use default empty results
                        'calculation_allowed': calculation_allowed,
                        'show_modal_for_signup': show_modal_for_signup,
                    }
                    return render(request, 'calculators/capital_gains_estimator.html', context)
            
            # --- Perform Calculations if allowed ---
            if calculation_allowed:
                # Safely get data from cleaned_data using .get() to avoid KeyError
                asset_name = form.cleaned_data.get('asset_name', '')
                purchase_date = form.cleaned_data.get('purchase_date')
                purchase_price = form.cleaned_data.get('purchase_price_per_share', Decimal('0.00'))
                shares_purchased = form.cleaned_data.get('shares_purchased', Decimal('0.00'))
                sale_date = form.cleaned_data.get('sale_date')
                sale_price = form.cleaned_data.get('sale_price_per_share', Decimal('0.00'))
                shares_sold = form.cleaned_data.get('shares_sold', Decimal('0.00')) # Safely get shares_sold
                commission_purchase = form.cleaned_data.get('commission_purchase', Decimal('0.00'))
                commission_sale = form.cleaned_data.get('commission_sale', Decimal('0.00'))
                
                # These are the tax-specific fields, which might not always be filled initially
                tax_rule_country = form.cleaned_data.get('tax_rule_country')
                annual_taxable_income = form.cleaned_data.get('annual_taxable_income')
                us_filing_status = form.cleaned_data.get('us_filing_status')

                # Basic Financial Calculations (always perform these if the form is valid and calculation allowed)
                total_purchase_cost = (purchase_price * shares_purchased) + commission_purchase
                total_sale_proceeds = (sale_price * shares_sold) - commission_sale
                gross_gain_loss = total_sale_proceeds - total_purchase_cost

                holding_period = calculate_holding_period(purchase_date, sale_date)
                gain_loss_type = get_gain_loss_type(purchase_date, sale_date)
                
                # Update general results
                results.update({
                    'calculation_successful': True, # Basic calculation successful
                    'asset_name': asset_name,
                    'total_purchase_cost': total_purchase_cost,
                    'total_sale_proceeds': total_sale_proceeds,
                    'gross_gain_loss': gross_gain_loss,
                    'holding_period': holding_period,
                    'gain_loss_type': gain_loss_type,
                })

                # --- Conditional Tax Calculation ---
                # Only calculate estimated tax if tax_rule_country is provided
                # and annual_taxable_income is provided and gross_gain_loss is positive
                if tax_rule_country and annual_taxable_income is not None and gross_gain_loss > 0:
                    estimated_tax = Decimal('0.00')
                    tax_currency = '£' if tax_rule_country == 'UK' else '$' # Default to $ for US, £ for UK

                    if tax_rule_country == 'UK':
                        estimated_tax = calculate_uk_cgt(gross_gain_loss, annual_taxable_income)
                    elif tax_rule_country == 'US':
                        if us_filing_status: 
                            estimated_tax = calculate_us_cgt(gross_gain_loss, annual_taxable_income, us_filing_status, gain_loss_type)
                        else:
                            messages.warning(request, "Please select a US filing status to estimate US tax.")
                            estimated_tax = Decimal('0.00') # No estimation without filing status
                    
                    net_gain_loss = gross_gain_loss - estimated_tax

                    results.update({
                        'tax_calculation_successful': True, # Tax calculation was attempted/successful
                        'estimated_tax': estimated_tax,
                        'net_gain_loss': net_gain_loss,
                        'tax_country': tax_rule_country, 
                        'tax_currency': tax_currency, 
                    })
                elif gross_gain_loss > 0: # Only prompt for tax if there's a gain
                    messages.info(request, "Enter your tax situation to see estimated tax.")
                    results['tax_calculation_successful'] = False # Indicate tax wasn't calculated
                else: # If no gross gain, no tax applies
                    results['tax_calculation_successful'] = True # Consider it successful as no tax is owed
                    results['net_gain_loss'] = gross_gain_loss # Net = Gross if no tax
                    results['estimated_tax'] = Decimal('0.00')


        else: # Form is NOT valid on POST
            messages.error(request, "Please correct the errors below.")
            results['calculation_successful'] = False # Ensure summary is not shown if form is invalid

    # This single return statement handles all scenarios
    context = {
        'form': form,
        'results': results,
        'calculation_allowed': calculation_allowed,
        'show_modal_for_signup': show_modal_for_signup,
    }
    return render(request, 'calculators/capital_gains_estimator.html', context)