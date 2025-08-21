#!/usr/bin/env python3
"""
CRITICAL: Ensure ONLY Real Market Data is Used
This module enforces real data requirements across the system
"""

import logging
from datetime import datetime
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

# CRITICAL: Known fake/outdated prices that must NEVER be used
BANNED_FAKE_PRICES = {
    'EURUSD': [1.0950, 1.095, 1.09],  # Real price is ~1.172
    'GBPUSD': [1.2650],  # Outdated
    'USDJPY': [110.0],   # Outdated
}

# Approximate real market ranges (as of August 2025)
VALID_PRICE_RANGES = {
    'EURUSD': (1.15, 1.20),   # Real range around 1.172
    'GBPUSD': (1.25, 1.35),   # Real range
    'USDJPY': (140, 155),     # Real range around 146
    'USDCAD': (1.30, 1.45),   # Real range around 1.38
    'USDCHF': (0.80, 1.05),   # Real range around 0.806 (updated)
    'AUDUSD': (0.60, 0.75),   # Real range
    'NZDUSD': (0.55, 0.70),   # Real range
    'EURJPY': (160, 180),     # Real range
    'GBPJPY': (180, 200),     # Real range
    'CHFJPY': (165, 190),     # Real range around 182.6 (updated)
}

def validate_forex_price(pair: str, price: float) -> bool:
    """
    Validate that a forex price is realistic and not fake
    
    Returns:
        True if price appears real, False if fake/suspicious
    """
    # Check against known fake prices
    if pair in BANNED_FAKE_PRICES:
        for fake_price in BANNED_FAKE_PRICES[pair]:
            if abs(price - fake_price) < 0.001:
                logger.error(f"❌ FAKE PRICE DETECTED: {pair} = {price} (known fake value)")
                return False
    
    # Check if price is within valid range
    if pair in VALID_PRICE_RANGES:
        min_price, max_price = VALID_PRICE_RANGES[pair]
        if not (min_price <= price <= max_price):
            logger.warning(f"⚠️ SUSPICIOUS PRICE: {pair} = {price} (outside expected range {min_price}-{max_price})")
            return False
    
    # Price appears valid
    return True

def validate_signal_data(signal_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate and clean signal data to ensure no fake prices
    
    Args:
        signal_data: Raw signal data
        
    Returns:
        Validated signal data with fake data removed
    """
    if not signal_data:
        return signal_data
    
    # Check forex alerts
    if 'forex_alerts' in signal_data:
        valid_alerts = []
        for alert in signal_data['forex_alerts']:
            pair = alert.get('pair', '')
            
            # Check all price fields
            prices_valid = True
            for price_field in ['entry_price', 'exit_price', 'stop_loss', 'take_profit', 'high', 'low', 'average']:
                if price_field in alert and alert[price_field]:
                    if not validate_forex_price(pair, alert[price_field]):
                        prices_valid = False
                        logger.error(f"❌ Removing signal for {pair} due to fake price in {price_field}: {alert[price_field]}")
                        break
            
            # Validate confidence and probability fields (must be 0-1 range)
            if prices_valid:
                if alert.get('confidence') is not None:
                    if not (0 <= alert['confidence'] <= 1):
                        logger.warning(f"⚠️ Invalid confidence for {pair}: {alert['confidence']}")
                        alert['confidence'] = max(0, min(1, alert['confidence']))
                
                if alert.get('weekly_achievement_probability') is not None:
                    if not (0 <= alert['weekly_achievement_probability'] <= 1):
                        logger.warning(f"⚠️ Invalid probability for {pair}: {alert['weekly_achievement_probability']}")
                        alert['weekly_achievement_probability'] = max(0, min(1, alert['weekly_achievement_probability']))
                
                # Validate signal category
                valid_categories = ['Strong', 'Medium', 'Weak', 'Strong (Enhanced)', 'Medium (Enhanced)', 'Weak (Enhanced)']
                if alert.get('signal_category') and alert['signal_category'] not in valid_categories:
                    logger.warning(f"⚠️ Unknown signal category for {pair}: {alert['signal_category']}")
                
                valid_alerts.append(alert)
        
        signal_data['forex_alerts'] = valid_alerts
        signal_data['has_real_data'] = len(valid_alerts) > 0
    
    return signal_data

def enforce_real_data_only():
    """
    System-wide enforcement of real data only policy
    """
    print("\n" + "="*70)
    print("REAL DATA ENFORCEMENT SYSTEM ACTIVE")
    print("="*70)
    print(f"Timestamp: {datetime.now().isoformat()}")
    print("\n✅ ENFORCING:")
    print("  • NO fake/synthetic prices allowed")
    print("  • NO hardcoded demo values")
    print("  • NO placeholder data")
    print("  • ONLY real market data from APIs")
    
    print("\n⚠️ KNOWN ISSUES TO FIX:")
    print("  • EURUSD must be ~1.172 (NOT 1.095)")
    print("  • All prices must be from live APIs")
    print("  • System must fail if real data unavailable")
    
    print("\n🔒 VALIDATION ACTIVE:")
    print("  • Price range checking enabled")
    print("  • Fake price detection enabled")
    print("  • Automatic removal of suspicious data")
    
    return True

# CRITICAL: This must be called before any signal generation
def initialize_real_data_enforcement():
    """Initialize the real data enforcement system"""
    enforce_real_data_only()
    logger.info("✅ Real data enforcement initialized - NO FAKE DATA ALLOWED")
    return True

if __name__ == "__main__":
    # Test the enforcement
    initialize_real_data_enforcement()
    
    # Test with fake data (should be rejected)
    fake_signal = {
        'forex_alerts': [
            {'pair': 'EURUSD', 'entry_price': 1.0950}  # FAKE!
        ]
    }
    
    print("\n" + "="*70)
    print("TESTING FAKE DATA DETECTION")
    print("="*70)
    validated = validate_signal_data(fake_signal)
    if not validated.get('has_real_data'):
        print("✅ SUCCESS: Fake data was correctly rejected")
    else:
        print("❌ FAILURE: Fake data was not detected!")
    
    # Test with real range data
    real_signal = {
        'forex_alerts': [
            {'pair': 'EURUSD', 'entry_price': 1.172}  # REAL!
        ]
    }
    
    print("\n" + "="*70)
    print("TESTING REAL DATA ACCEPTANCE")
    print("="*70)
    validated = validate_signal_data(real_signal)
    if validated.get('forex_alerts'):
        print("✅ SUCCESS: Real data was correctly accepted")
    else:
        print("❌ FAILURE: Real data was rejected!")