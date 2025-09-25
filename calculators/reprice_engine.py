# calculators/reprice_engine.py
from decimal import Decimal
from typing import Dict, Any

def calculate_reprice_by_shares(position: Dict[str, Any], additional_shares: Decimal) -> Dict[str, Any]:
    """ Calculates the new average price after buying more shares. """
    current_shares = Decimal(position['current_shares'])
    average_price = Decimal(position['average_price'])
    market_price = Decimal(position['market_price'])

    if current_shares < 0 or average_price < 0 or market_price < 0 or additional_shares < 0:
        raise ValueError("Inputs cannot be negative.")

    initial_cost = current_shares * average_price
    initial_value = current_shares * market_price
    initial_pnl = initial_value - initial_cost

    additional_cost = additional_shares * market_price
    
    total_shares = current_shares + additional_shares
    total_cost = initial_cost + additional_cost
    
    new_average_price = total_cost / total_shares if total_shares > 0 else Decimal('0.00')

    return {
        "initial_pnl": f"{initial_pnl:.2f}",
        "new_average_price": f"{new_average_price:.2f}",
        "total_shares": f"{total_shares:.4f}",
        "additional_investment": f"{additional_cost:.2f}",
        "total_investment": f"{total_cost:.2f}"
    }

def calculate_reprice_by_target(position: Dict[str, Any], target_price: Decimal) -> Dict[str, Any]:
    """ Calculates the number of shares needed to reach a target average price. """
    current_shares = Decimal(position['current_shares'])
    average_price = Decimal(position['average_price'])
    market_price = Decimal(position['market_price'])
    
    if target_price >= average_price:
        raise ValueError("Target price must be lower than the current average price.")
    if market_price <= 0:
        raise ValueError("Market price must be positive.")
    if target_price <= market_price:
        raise ValueError("Target price must be higher than the current market price.")
        
    initial_cost = current_shares * average_price
    initial_value = current_shares * market_price
    initial_pnl = initial_value - initial_cost
        
    numerator = current_shares * (average_price - target_price)
    denominator = target_price - market_price
    
    additional_shares_needed = numerator / denominator if denominator != 0 else Decimal('0.00')
    additional_cost = additional_shares_needed * market_price
    total_shares = current_shares + additional_shares_needed
    total_cost = initial_cost + additional_cost

    return {
        "initial_pnl": f"{initial_pnl:.2f}",
        "additional_shares_needed": f"{additional_shares_needed:.4f}",
        "total_shares": f"{total_shares:.4f}",
        "additional_investment": f"{additional_cost:.2f}",
        "total_investment": f"{total_cost:.2f}"
    }