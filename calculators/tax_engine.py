# calculators/tax_engine.py
from decimal import Decimal
from datetime import date
from typing import List, Tuple, TypedDict
from dateutil.relativedelta import relativedelta # You will need to install this: pip install python-dateutil

# --- Data Structures ---
class TransactionLot(TypedDict):
    date: date
    quantity: Decimal
    price: Decimal
    fees: Decimal

# --- Core Logic ---

def calculate_fifo_cost_basis(purchase_lots: List[TransactionLot], sold_quantity: Decimal) -> Tuple[Decimal, Decimal]:
    """Calculates the cost basis for a sale using the FIFO method."""
    purchase_lots.sort(key=lambda lot: lot['date'])
    total_cost_basis = Decimal('0.00')
    total_fees = Decimal('0.00')
    quantity_to_account_for = sold_quantity
    
    total_owned_quantity = sum(lot['quantity'] for lot in purchase_lots)
    if sold_quantity > total_owned_quantity:
        raise ValueError(f"Sale quantity ({sold_quantity}) exceeds total owned quantity ({total_owned_quantity}).")

    for lot in purchase_lots:
        if quantity_to_account_for <= 0:
            break

        cost_per_share = lot['price']
        fees_per_share = lot.get('fees', Decimal('0.00')) / lot['quantity'] if lot['quantity'] > 0 else Decimal('0.00')

        if lot['quantity'] <= quantity_to_account_for:
            total_cost_basis += lot['quantity'] * cost_per_share
            total_fees += lot.get('fees', Decimal('0.00'))
            quantity_to_account_for -= lot['quantity']
        else:
            total_cost_basis += quantity_to_account_for * cost_per_share
            total_fees += quantity_to_account_for * fees_per_share
            quantity_to_account_for = 0
    
    return total_cost_basis, total_fees

from .tax_config import UK_TAX_CONFIG, US_SHORT_TERM_BRACKETS, US_LONG_TERM_BRACKETS
    
def get_holding_period_and_type(purchase_date: date, sale_date: date) -> Tuple[str, str]:
    """Determines the holding period and whether the gain is short-term or long-term."""
    if not purchase_date or not sale_date:
        return "N/A", "N/A"
        
    delta = relativedelta(sale_date, purchase_date)
    period_str = f"{delta.years}y, {delta.months}m, {delta.days}d"
    
    # PROFESSIONAL FIX: Long term requires STRICTLY greater than one year of holding
    gain_type = "Long-Term" if sale_date > purchase_date + relativedelta(years=1) else "Short-Term"
    
    return period_str, gain_type

# --- Jurisdiction-Specific Tax Logic ---

def calculate_uk_cgt(gross_gain: Decimal, annual_income: Decimal) -> Decimal:
    """Calculates UK Capital Gains Tax (CGT) using external config."""
    if gross_gain <= 0:
        return Decimal('0.00')
        
    exempt = UK_TAX_CONFIG['ANNUAL_EXEMPT_AMOUNT']
    threshold = UK_TAX_CONFIG['BASIC_RATE_THRESHOLD']
    basic_rate = UK_TAX_CONFIG['BASIC_RATE_CGT']
    higher_rate = UK_TAX_CONFIG['HIGHER_RATE_CGT']
        
    taxable_gain = max(Decimal('0.00'), gross_gain - exempt)
    if taxable_gain <= 0:
        return Decimal('0.00')
        
    remaining_basic_rate_band = max(Decimal('0.00'), threshold - annual_income)
    basic_rate_gain = min(remaining_basic_rate_band, taxable_gain)
    higher_rate_gain = max(Decimal('0.00'), taxable_gain - basic_rate_gain)
        
    cgt_payable = (basic_rate_gain * basic_rate) + (higher_rate_gain * higher_rate)
    return cgt_payable.quantize(Decimal('0.01'))

def calculate_us_cgt(gross_gain: Decimal, annual_income: Decimal, filing_status: str, gain_type: str) -> Decimal:
    """Estimates US Capital Gains Tax using external config brackets."""
    if gross_gain <= 0:
        return Decimal('0.00')

    if gain_type == "Short-Term":
        total_income = annual_income + gross_gain
        for bracket in US_SHORT_TERM_BRACKETS:
             if bracket['up_to'] == Decimal('Infinity') or total_income <= bracket['up_to']:
                 return (gross_gain * bracket['rate']).quantize(Decimal('0.01'))

    else:
        brackets = US_LONG_TERM_BRACKETS.get(filing_status, US_LONG_TERM_BRACKETS['single']) # Fallback to single if invalid
        for bracket in brackets:
            if bracket['up_to'] == Decimal('Infinity') or annual_income <= bracket['up_to']:
                 return (gross_gain * bracket['rate']).quantize(Decimal('0.01'))
        
    return Decimal('0.00')