# calculators/drip_engine.py
from decimal import Decimal

def calculate_drip_projection(
    initial_principal: Decimal,
    annual_contribution: Decimal,
    dividend_yield_percent: Decimal,
    annual_appreciation_percent: Decimal,
    years_to_grow: int
) -> dict:
    """
    Calculates the compounding growth of a dividend reinvestment plan (DRIP) over a given timescale.
    Assumes contributions and dividends are reinvested annually for simplicity.

    Returns a year-by-year projection list and summary statistics.
    """
    if years_to_grow <= 0 or years_to_grow > 50:
        raise ValueError("Years to grow must be between 1 and 50.")
    if initial_principal < 0 or annual_contribution < 0:
        raise ValueError("Principal and contributions cannot be negative.")

    current_principal = initial_principal
    total_contributions = initial_principal
    
    # Pre-calculate decimals
    div_yield = dividend_yield_percent / Decimal('100.0')
    appreciation = annual_appreciation_percent / Decimal('100.0')

    yearly_data = []

    for year in range(1, years_to_grow + 1):
        # 1. Start of year contributions (simplified to beginning of year)
        if year > 1:
             current_principal += annual_contribution
             total_contributions += annual_contribution

        # 2. Calculate Growth and Dividends on the balance
        yearly_dividend = current_principal * div_yield
        yearly_growth = current_principal * appreciation

        # 3. End of year balance (reinvesting the dividend)
        end_of_year_balance = current_principal + yearly_dividend + yearly_growth
        
        yearly_data.append({
            'year': year,
            'start_balance': f"{current_principal:.2f}",
            'contributions_to_date': f"{total_contributions:.2f}",
            'dividend_earned': f"{yearly_dividend:.2f}",
            'capital_appreciation': f"{yearly_growth:.2f}",
            'end_balance': f"{end_of_year_balance:.2f}"
        })
        
        # Set up for next year
        current_principal = end_of_year_balance

    total_dividends_earned = sum(Decimal(y['dividend_earned']) for y in yearly_data)
    total_capital_growth = sum(Decimal(y['capital_appreciation']) for y in yearly_data)
    final_balance = current_principal

    return {
        'summary': {
            'total_contributions': f"{total_contributions:.2f}",
            'total_dividends_earned': f"{total_dividends_earned:.2f}",
            'total_capital_growth': f"{total_capital_growth:.2f}",
            'final_balance': f"{final_balance:.2f}"
        },
        'projection': yearly_data
    }
