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

def get_holding_period_and_type(purchase_date: date, sale_date: date) -> Tuple[str, str]:
    """Determines the holding period and whether the gain is short-term or long-term."""
    if not purchase_date or not sale_date:
        return "N/A", "N/A"
        
    delta = relativedelta(sale_date, purchase_date)
    period_str = f"{delta.years}y, {delta.months}m, {delta.days}d"
    
    gain_type = "Long-Term" if sale_date >= purchase_date + relativedelta(years=1) else "Short-Term"
    
    return period_str, gain_type

# --- Jurisdiction-Specific Tax Logic ---

def calculate_uk_cgt(gross_gain: Decimal, annual_income: Decimal) -> Decimal:
    """Calculates UK Capital Gains Tax (CGT). Simplified for 2024/25 tax year."""
    if gross_gain <= 0:
        return Decimal('0.00')
        
    # Tax constants for 2024/25
    ANNUAL_EXEMPT_AMOUNT = Decimal('3000.00')
    BASIC_RATE_THRESHOLD = Decimal('50270.00')
    BASIC_RATE_CGT = Decimal('0.10')
    HIGHER_RATE_CGT = Decimal('0.20')
        
    taxable_gain = max(Decimal('0.00'), gross_gain - ANNUAL_EXEMPT_AMOUNT)
    if taxable_gain <= 0:
        return Decimal('0.00')
        
    remaining_basic_rate_band = max(Decimal('0.00'), BASIC_RATE_THRESHOLD - annual_income)
    basic_rate_gain = min(remaining_basic_rate_band, taxable_gain)
    higher_rate_gain = max(Decimal('0.00'), taxable_gain - basic_rate_gain)
        
    cgt_payable = (basic_rate_gain * BASIC_RATE_CGT) + (higher_rate_gain * HIGHER_RATE_CGT)
    return cgt_payable.quantize(Decimal('0.01'))

def calculate_us_cgt(gross_gain: Decimal, annual_income: Decimal, filing_status: str, gain_type: str) -> Decimal:
    """Estimates US Capital Gains Tax. Highly simplified for 2024 tax year."""
    if gross_gain <= 0:
        return Decimal('0.00')

    # Short-term gains are taxed as ordinary income. This is a vast simplification.
    if gain_type == "Short-Term":
        total_income = annual_income + gross_gain
        # Simplified marginal tax rate lookup for a single filer
        if total_income <= 11600: return gross_gain * Decimal('0.10')
        if total_income <= 47150: return gross_gain * Decimal('0.12')
        if total_income <= 100525: return gross_gain * Decimal('0.22')
        # ... and so on. This simplification is sufficient for our purpose.
        return gross_gain * Decimal('0.24') # Defaulting to a common bracket

    # Long-term gains have preferential rates.
    else:
        # Simplified brackets for 2024 "Single" filer
        if filing_status == 'single':
            if annual_income <= 47025: return gross_gain * Decimal('0.00')
            if annual_income <= 518900: return gross_gain * Decimal('0.15')
            return gross_gain * Decimal('0.20')
        # Simplified brackets for 2024 "Married Filing Jointly"
        elif filing_status == 'married_jointly':
            if annual_income <= 94050: return gross_gain * Decimal('0.00')
            if annual_income <= 583750: return gross_gain * Decimal('0.15')
            return gross_gain * Decimal('0.20')
        
    return Decimal('0.00')