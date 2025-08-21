#!/usr/bin/env python3
"""
Simple verification that the plaintext format is working.
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from src.data_processors.template_generator import StructuredTemplateGenerator


def verify_fix():
    """Verify the plaintext format is working correctly."""
    print("🔍 Verifying Plaintext Format Fix")
    print("=" * 50)
    
    # Sample data exactly like what gets sent to groups
    sample_data = {
        'has_real_data': True,
        'forex_alerts': {
            'EURUSD': {
                'high': '1.1158',
                'average': '1.0742',
                'low': '1.0238',
                'signal': 'SELL',
                'trade_type': 'MT4 SELL',
                'exit': '1.0850',
                'trade_status': 'TRADE IN PROFIT'
            },
            'GBPUSD': {
                'high': '1.3301',
                'average': '1.3046',
                'low': '1.2168',
                'signal': 'SELL',
                'trade_type': 'MT4 SELL',
                'exit': '1.2933'
            },
            'USDJPY': {
                'high': '0.9142',
                'average': '0.8842',
                'low': '0.8542',
                'signal': 'BUY',
                'trade_type': 'MT4 BUY',
                'exit': 'TBD'
            },
            'USDCHF': {
                'high': '0.9142',
                'average': '0.8842',
                'low': '0.8542',
                'signal': 'BUY',
                'trade_type': 'MT4 BUY',
                'exit': '0.8881'
            },
            'USDCAD': {
                'high': '1.4571',
                'average': '1.4119',
                'low': '1.3419',
                'signal': 'SELL',
                'trade_type': 'MT4 SELL',
                'exit': '1.3837'
            },
            'AUDUSD': {
                'high': '0.6943',
                'average': '0.6681',
                'low': '0.6088',
                'signal': 'SELL',
                'trade_type': 'MT4 SELL',
                'exit': '0.6217'
            }
        },
        'options_data': [
            {
                'ticker': 'QQQ',
                'high_52week': '480.92',
                'low_52week': '478.13',
                'call_strike': 'CALL > 521.68',
                'put_strike': 'PUT < N/A',
                'status': 'TRADE IN PROFIT'
            },
            {
                'ticker': 'SPY',
                'high_52week': '536.89',
                'low_52week': '409.21',
                'call_strike': 'CALL > 591.12',
                'put_strike': 'PUT < N/A',
                'status': 'TRADE IN PROFIT'
            },
            {
                'ticker': 'IWM',
                'high_52week': '200.58',
                'low_52week': '198.83',
                'call_strike': 'CALL > 206.74',
                'put_strike': 'PUT < 204.14',
                'status': 'TRADE IN PROFIT'
            },
            {
                'ticker': 'NVDA',
                'high_52week': '128.16',
                'low_52week': '122.30',
                'call_strike': 'CALL > 136.73',
                'put_strike': 'PUT < 132.79',
                'status': 'TRADE IN PROFIT'
            },
            {
                'ticker': 'TSLA',
                'high_52week': '479.70',
                'low_52week': '258.35',
                'call_strike': 'CALL > 352.42',
                'put_strike': 'PUT < N/A',
                'status': 'TRADE IN PROFIT'
            }
        ],
        'swing_trades': [
            {
                'company': 'JOYY Inc.',
                'ticker': 'JOYY',
                'earnings_date': 'May 26, 2025',
                'current_price': '$47.67',
                'rationale': 'JOYY reported Q1 2025 revenue of $494.4 million, with non-GAAP operating profit reaching $31 million, a 25% year-over-year increase. The company also returned $71.6 million to shareholders through dividends and buybacks. This strong financial performance suggests potential for continued upward momentum.'
            },
            {
                'company': 'EHang Holdings Ltd.',
                'ticker': 'EH',
                'earnings_date': 'May 26, 2025',
                'current_price': '$15.88',
                'rationale': 'EHang reported Q1 2025 earnings, maintaining its full-year guidance. As a pioneer in autonomous aerial vehicles, positive earnings and steady guidance may attract investor interest, potentially leading to a price increase.'
            },
            {
                'company': 'Hesai Group',
                'ticker': 'HSAI',
                'earnings_date': 'May 26, 2025',
                'current_price': '$19.12',
                'rationale': 'Hesai reported a 46% year-over-year revenue increase in Q1 2025 and a significant reduction in net loss. The company\'s growth in LiDAR shipments indicates strong demand, which could drive the stock higher in the short term.'
            }
        ],
        'day_trades': [
            {
                'company': 'PDD Holdings Inc.',
                'ticker': 'PDD',
                'earnings_date': 'May 27, 2025',
                'current_price': '$95.60',
                'rationale': 'PDD reported a 47% drop in net profit for Q1 2025, attributed to increased U.S. tariffs and the closure of the de minimis exemption. The stock has declined significantly, presenting potential intraday trading opportunities based on volatility.'
            },
            {
                'company': 'AutoZone Inc.',
                'ticker': 'AZO',
                'earnings_date': 'May 27, 2025',
                'current_price': '$3,731.45',
                'rationale': 'AutoZone reported mixed Q3 2025 results, with revenue beating expectations but net income falling short. The stock\'s high price and sensitivity to earnings news make it suitable for intraday trading strategies.'
            },
            {
                'company': 'Marvell Technology Inc',
                'ticker': 'MRVL',
                'earnings_date': 'May 29, 2025',
                'current_price': '$65.03',
                'rationale': 'Marvell reported quarterly earnings of $0.61 per share on revenue of $1.88 billion. The stock has shown a slight increase of approximately 0.7% today, indicating potential for intraday trading strategies.'
            }
        ]
    }
    
    # Generate the structured message
    generator = StructuredTemplateGenerator()
    structured_message = generator.generate_structured_message(sample_data)
    
    print("📄 NEW PLAINTEXT FORMAT OUTPUT:")
    print("=" * 50)
    print(structured_message)
    print("=" * 50)
    
    # Verify it matches your requirements
    required_elements = [
        "FOREX PAIRS",
        "Pair: EURUSD",
        "MT4 Action: MT4 SELL",
        "Exit: 1.0850",
        "PREMIUM SWING TRADES (Monday - Wednesday)",
        "JOYY Inc. (JOYY)",
        "PREMIUM DAY TRADES (Monday - Wednesday)",
        "PDD Holdings Inc. (PDD)",
        "EQUITIES AND OPTIONS",
        "Symbol: QQQ",
        "CALL > 521.68",
        "Status: TRADE IN PROFIT"
    ]
    
    # Check against wrong format elements
    wrong_elements = [
        "📊 Daily Financial Report",
        "🔴 EURUSD - SELL",
        "📈 Entry:",
        "Trade Type:",
        "Ticker: QQQ"
    ]
    
    print("\n✅ VERIFICATION RESULTS:")
    
    # Check required elements
    missing_required = []
    for element in required_elements:
        if element in structured_message:
            print(f"✅ Found: {element}")
        else:
            missing_required.append(element)
            print(f"❌ Missing: {element}")
    
    # Check for wrong elements
    found_wrong = []
    for element in wrong_elements:
        if element in structured_message:
            found_wrong.append(element)
            print(f"❌ Found wrong element: {element}")
    
    success = len(missing_required) == 0 and len(found_wrong) == 0
    
    print(f"\n🎯 OVERALL RESULT: {'✅ SUCCESS' if success else '❌ FAILURE'}")
    
    if success:
        print("✅ The plaintext format is working perfectly!")
        print("✅ Tomorrow's report will use the correct format")
        print("✅ No more emoji-based messages will be sent")
    else:
        if missing_required:
            print(f"❌ Missing required elements: {missing_required}")
        if found_wrong:
            print(f"❌ Found wrong format elements: {found_wrong}")
    
    return success


if __name__ == "__main__":
    success = verify_fix()
    sys.exit(0 if success else 1)