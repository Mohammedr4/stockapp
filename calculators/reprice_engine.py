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
            raise ValueError(f"You can't average down — the market price (${market_price:.2f}) is already above your average (${average_price:.2f}). Switch to 'Target Average' with a higher target, or use 'Buy Shares' to average up.")
        if target_price <= market_price:
            raise ValueError(f"Target (${target_price:.2f}) must be above the market price (${market_price:.2f}) to average down. You can only pull your average between the market price and your current average.")
    
    # Scenario 2: User wants to average UP
    elif target_price > average_price:
        if market_price <= average_price:
            raise ValueError(f"You can't average up — the market price (${market_price:.2f}) is below your average (${average_price:.2f}). Switch to 'Target Average' with a lower target, or use 'Buy Shares' to average down.")
        if target_price >= market_price:
            raise ValueError(f"Target (${target_price:.2f}) must be below the market price (${market_price:.2f}) to average up. Your target must sit between your current average and the market price.")
    
    # Scenario 3: Target is the same as average
    else:
        raise ValueError("Your target is the same as your current average — nothing would change. Enter a different target price.")
        
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

def calculate_trade_scenario(position: Dict[str, Any], tranches: list) -> Dict[str, Any]:
    """ Calculates a multi-tranche trade scenario. """
    current_shares = Decimal(position['current_shares'])
    average_price = Decimal(position['average_price'])
    market_price = Decimal(position.get('market_price', 0))
    
    total_shares = current_shares
    total_cost = current_shares * average_price
    total_additional_investment = Decimal('0.00')
    
    scenario_steps = []
    lowest_px = market_price

    for tranche in tranches:
        px = Decimal(tranche['price'])
        amount = Decimal(tranche['investment_amount'])
        if px <= 0:
            raise ValueError("Tranche price must be positive.")
        
        shares = amount / px
        
        total_shares += shares
        total_cost += amount
        total_additional_investment += amount
        
        if px < lowest_px:
            lowest_px = px
            
        new_avg = total_cost / total_shares if total_shares > 0 else Decimal('0.00')
        scenario_steps.append({
            "tranche_price": f"{px:.2f}",
            "investment_amount": f"{amount:.2f}",
            "shares_acquired": f"{shares:.4f}",
            "running_total_shares": f"{total_shares:.4f}",
            "running_average_price": f"{new_avg:.2f}",
        })

    final_avg = total_cost / total_shares if total_shares > 0 else Decimal('0.00')
    
    breakeven_recovery_pct = Decimal('0.00')
    if lowest_px > 0:
        breakeven_recovery_pct = ((final_avg - lowest_px) / lowest_px) * 100

    # Also calculate recovery needed if they DID NOT do this scenario
    original_recovery_pct = Decimal('0.00')
    if lowest_px > 0:
        original_recovery_pct = ((average_price - lowest_px) / lowest_px) * 100

    return {
        "final_average_price": f"{final_avg:.2f}",
        "total_shares": f"{total_shares:.4f}",
        "total_additional_investment": f"{total_additional_investment:.2f}",
        "lowest_price_reached": f"{lowest_px:.2f}",
        "breakeven_recovery_percent": f"{breakeven_recovery_pct:.2f}",
        "original_recovery_percent": f"{original_recovery_pct:.2f}",
        "scenario_steps": scenario_steps
    }