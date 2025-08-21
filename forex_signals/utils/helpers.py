"""
Helper utility functions for forex operations
"""

import re
from typing import Dict, Tuple, Optional
from decimal import Decimal, ROUND_HALF_UP

from ..core.logging import get_logger

logger = get_logger(__name__)


def format_currency_pair(pair: str) -> str:
    """
    Format currency pair to standard format
    
    Args:
        pair: Currency pair string
        
    Returns:
        Formatted currency pair (e.g., 'EURUSD')
        
    Raises:
        ValueError: If pair format is invalid
    """
    # Remove any whitespace and convert to uppercase
    clean_pair = re.sub(r'\s', '', pair.upper())
    
    # Check for valid forex pair format
    if not re.match(r'^[A-Z]{6}$', clean_pair):
        raise ValueError(f"Invalid currency pair format: {pair}. Expected format: EURUSD")
    
    return clean_pair


def calculate_pips(
    pair: str,
    price1: float,
    price2: float
) -> float:
    """
    Calculate pip difference between two prices
    
    Args:
        pair: Currency pair (e.g., 'EURUSD')
        price1: First price
        price2: Second price
        
    Returns:
        Pip difference (price2 - price1)
    """
    # Define pip values for different pair types
    pip_values = {
        # Major pairs with 4 decimal places (0.0001 = 1 pip)
        'EURUSD': 0.0001, 'GBPUSD': 0.0001, 'AUDUSD': 0.0001, 'NZDUSD': 0.0001,
        'USDCHF': 0.0001, 'USDCAD': 0.0001,
        
        # JPY pairs with 2 decimal places (0.01 = 1 pip)
        'USDJPY': 0.01, 'EURJPY': 0.01, 'GBPJPY': 0.01, 'CHFJPY': 0.01,
        'AUDJPY': 0.01, 'CADJPY': 0.01, 'NZDJPY': 0.01,
        
        # Cross pairs (4 decimal places)
        'EURGBP': 0.0001, 'EURCHF': 0.0001, 'EURAUD': 0.0001, 'EURCAD': 0.0001,
        'EURNZD': 0.0001, 'GBPCHF': 0.0001, 'GBPAUD': 0.0001, 'GBPCAD': 0.0001,
        'GBPNZD': 0.0001, 'AUDCHF': 0.0001, 'AUDCAD': 0.0001, 'AUDNZD': 0.0001,
        'CADCHF': 0.0001, 'NZDCHF': 0.0001, 'NZDCAD': 0.0001,
    }
    
    pair = format_currency_pair(pair)
    pip_value = pip_values.get(pair, 0.0001)  # Default to 4 decimal places
    
    price_diff = price2 - price1
    pips = price_diff / pip_value
    
    return round(pips, 1)


def validate_price_range(
    pair: str,
    price: float,
    tolerance_percent: float = 50.0
) -> bool:
    """
    Validate if a price is within reasonable range for a currency pair
    
    Args:
        pair: Currency pair
        price: Price to validate
        tolerance_percent: Tolerance percentage from typical range
        
    Returns:
        True if price is within reasonable range
    """
    # Typical price ranges for major pairs (approximate)
    typical_ranges = {
        'EURUSD': (0.95, 1.35),
        'GBPUSD': (1.15, 1.45),
        'USDJPY': (100, 160),
        'USDCHF': (0.85, 1.10),
        'USDCAD': (1.20, 1.50),
        'AUDUSD': (0.60, 0.85),
        'NZDUSD': (0.55, 0.75),
        'EURJPY': (120, 170),
        'GBPJPY': (140, 200),
        'CHFJPY': (140, 190),
        'EURGBP': (0.80, 0.95),
        'EURAUD': (1.45, 1.75),
        'EURCAD': (1.40, 1.70),
    }
    
    pair = format_currency_pair(pair)
    
    if pair not in typical_ranges:
        # For unknown pairs, accept any positive price
        return price > 0
    
    min_price, max_price = typical_ranges[pair]
    
    # Apply tolerance
    tolerance_factor = tolerance_percent / 100.0
    range_size = max_price - min_price
    tolerance_amount = range_size * tolerance_factor
    
    expanded_min = min_price - tolerance_amount
    expanded_max = max_price + tolerance_amount
    
    return expanded_min <= price <= expanded_max


def calculate_position_size(
    account_balance: float,
    risk_percent: float,
    stop_loss_pips: float,
    pair: str,
    account_currency: str = 'USD'
) -> float:
    """
    Calculate position size based on risk management
    
    Args:
        account_balance: Account balance
        risk_percent: Risk percentage (e.g., 2.0 for 2%)
        stop_loss_pips: Stop loss in pips
        pair: Currency pair
        account_currency: Account currency
        
    Returns:
        Position size in lots
    """
    # Calculate risk amount
    risk_amount = account_balance * (risk_percent / 100.0)
    
    # Calculate pip value (simplified for USD account)
    # This is a simplified calculation - real implementation would need
    # current exchange rates for accurate pip value calculation
    
    pip_values = {
        'EURUSD': 10.0, 'GBPUSD': 10.0, 'AUDUSD': 10.0, 'NZDUSD': 10.0,
        'USDCHF': 10.0, 'USDCAD': 10.0, 'USDJPY': 10.0,
        # For JPY pairs, pip value varies with current rate
        'EURJPY': 10.0, 'GBPJPY': 10.0, 'CHFJPY': 10.0,
        'AUDJPY': 10.0, 'CADJPY': 10.0, 'NZDJPY': 10.0,
    }
    
    pair = format_currency_pair(pair)
    pip_value = pip_values.get(pair, 10.0)  # Default pip value for 1 standard lot
    
    # Calculate position size
    position_size = risk_amount / (stop_loss_pips * pip_value)
    
    return round(position_size, 2)


def format_price(price: float, pair: str) -> str:
    """
    Format price according to currency pair conventions
    
    Args:
        price: Price to format
        pair: Currency pair
        
    Returns:
        Formatted price string
    """
    pair = format_currency_pair(pair)
    
    # JPY pairs typically use 2 decimal places
    if 'JPY' in pair:
        return f"{price:.2f}"
    else:
        # Most other pairs use 4-5 decimal places
        return f"{price:.5f}"


def get_pair_info(pair: str) -> Dict[str, str]:
    """
    Get information about a currency pair
    
    Args:
        pair: Currency pair (e.g., 'EURUSD')
        
    Returns:
        Dictionary with pair information
    """
    pair = format_currency_pair(pair)
    
    if len(pair) != 6:
        raise ValueError(f"Invalid pair format: {pair}")
    
    base_currency = pair[:3]
    quote_currency = pair[3:]
    
    # Currency names
    currency_names = {
        'USD': 'US Dollar',
        'EUR': 'Euro',
        'GBP': 'British Pound',
        'JPY': 'Japanese Yen',
        'CHF': 'Swiss Franc',
        'CAD': 'Canadian Dollar',
        'AUD': 'Australian Dollar',
        'NZD': 'New Zealand Dollar',
        'NOK': 'Norwegian Krone',
        'SEK': 'Swedish Krona',
        'DKK': 'Danish Krone',
    }
    
    return {
        'pair': pair,
        'base_currency': base_currency,
        'quote_currency': quote_currency,
        'base_name': currency_names.get(base_currency, base_currency),
        'quote_name': currency_names.get(quote_currency, quote_currency),
        'description': f"{currency_names.get(base_currency, base_currency)} / {currency_names.get(quote_currency, quote_currency)}"
    }


def is_market_hours(pair: str) -> bool:
    """
    Check if market is open for a currency pair (simplified)
    
    Args:
        pair: Currency pair
        
    Returns:
        True if market is likely open (simplified check)
    """
    import datetime
    
    # Forex market is open 24/5, but this is a simplified check
    # Real implementation would consider holidays and exact session times
    
    now = datetime.datetime.now(datetime.timezone.utc)
    weekday = now.weekday()  # 0 = Monday, 6 = Sunday
    
    # Market closed on weekends
    if weekday == 5:  # Saturday
        return False
    elif weekday == 6:  # Sunday
        # Market opens Sunday evening UTC
        return now.hour >= 21
    else:
        # Monday to Friday - market open
        # (This is simplified - real market has brief closure Friday evening to Sunday evening)
        return True


def calculate_profit_loss(
    pair: str,
    entry_price: float,
    exit_price: float,
    position_size: float,
    position_type: str = 'BUY'
) -> float:
    """
    Calculate profit/loss for a position
    
    Args:
        pair: Currency pair
        entry_price: Entry price
        exit_price: Exit price
        position_size: Position size in lots
        position_type: 'BUY' or 'SELL'
        
    Returns:
        Profit/loss in USD (simplified)
    """
    pips = calculate_pips(pair, entry_price, exit_price)
    
    # Reverse pips for SELL positions
    if position_type.upper() == 'SELL':
        pips = -pips
    
    # Simplified pip value calculation (assuming USD account)
    pip_value_per_lot = 10.0  # Standard lot pip value for most pairs in USD
    
    profit_loss = pips * pip_value_per_lot * position_size
    
    return round(profit_loss, 2)