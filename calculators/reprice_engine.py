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
    additional_cost = additional_shares * market_price
    
    total_shares = current_shares + additional_shares
    total_cost = initial_cost + additional_cost
    
    new_average_price = total_cost / total_shares if total_shares > 0 else Decimal('0.00')

    return {
        "new_average_price": f"{new_average_price:.2f}",
        "total_shares": f"{total_shares:.4f}",
        "additional_investment": f"{additional_cost:.2f}",
    }

def calculate_reprice_by_target(position: Dict[str, Any], target_price: Decimal) -> Dict[str, Any]:
    """ Calculates the number of shares needed to reach a target average price. """
    current_shares = Decimal(position['current_shares'])
    average_price = Decimal(position['average_price'])
    market_price = Decimal(position['market_price'])
    
    if market_price <= 0:
        raise ValueError("Market price must be positive.")

    # Scenario 1: User wants to average DOWN
    if target_price < average_price:
        if market_price >= average_price:
            raise ValueError(f"Cannot average down. The market price (${market_price}) is already higher than your average price (${average_price}).")
        if target_price <= market_price:
            raise ValueError(f"Target price (${target_price}) must be higher than the market price (${market_price}) to average down.")
    
    # Scenario 2: User wants to average UP
    elif target_price > average_price:
        if market_price <= average_price:
            raise ValueError(f"Cannot average up. The market price (${market_price}) is lower than your average price (${average_price}).")
        if target_price >= market_price:
            raise ValueError(f"Target price (${target_price}) must be lower than the market price (${market_price}) to average up.")
    
    # Scenario 3: Target is the same as average
    else:
        raise ValueError("Target price cannot be the same as your current average price.")
        
    numerator = current_shares * (average_price - target_price)
    denominator = target_price - market_price
    
    additional_shares_needed = numerator / denominator
    additional_cost = additional_shares_needed * market_price
    total_shares = current_shares + additional_shares_needed

    return {
        "additional_shares_needed": f"{additional_shares_needed:.4f}",
        "total_shares": f"{total_shares:.4f}",
        "additional_investment": f"{additional_cost:.2f}",
    }