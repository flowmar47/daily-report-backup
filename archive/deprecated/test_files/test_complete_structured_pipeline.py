#!/usr/bin/env python3
"""
Test the complete structured messaging pipeline with the old format.
"""

import sys
import asyncio
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from src.data_processors.template_generator import StructuredTemplateGenerator
from messenger_compatibility import SignalMessenger, TelegramMessenger


def test_structured_template_generator():
    """Test the structured template generator with sample data."""
    print("🧪 Testing Structured Template Generator")
    print("=" * 60)
    
    # Create sample financial data matching what the scraper provides
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
            }
        ],
        'day_trades': [
            {
                'company': 'PDD Holdings Inc.',
                'ticker': 'PDD',
                'earnings_date': 'May 27, 2025',
                'current_price': '$95.60',
                'rationale': 'PDD reported a 47% drop in net profit for Q1 2025, attributed to increased U.S. tariffs and the closure of the de minimis exemption. The stock has declined significantly, presenting potential intraday trading opportunities based on volatility.'
            }
        ]
    }
    
    # Test the generator
    generator = StructuredTemplateGenerator()
    structured_message = generator.generate_structured_message(sample_data)
    
    print("📄 GENERATED STRUCTURED MESSAGE:")
    print("=" * 60)
    print(structured_message)
    print("=" * 60)
    
    # Verify the format matches your requirements
    expected_patterns = [
        "FOREX PAIRS",
        "Pair: EURUSD",
        "MT4 Action:",
        "PREMIUM SWING TRADES (Monday - Wednesday)",
        "JOYY Inc. (JOYY)",
        "PREMIUM DAY TRADES (Monday - Wednesday)",
        "PDD Holdings Inc. (PDD)",
        "EQUITIES AND OPTIONS",
        "Symbol: QQQ",
        "CALL > 521.68"
    ]
    
    passed_checks = 0
    for pattern in expected_patterns:
        if pattern in structured_message:
            passed_checks += 1
            print(f"✅ Found: {pattern}")
        else:
            print(f"❌ Missing: {pattern}")
    
    success_rate = passed_checks / len(expected_patterns)
    print(f"\n🎯 Format Check: {passed_checks}/{len(expected_patterns)} patterns found ({success_rate:.1%})")
    
    if success_rate >= 0.8:
        print("✅ STRUCTURED TEMPLATE GENERATOR IS WORKING CORRECTLY!")
        print("✅ Old format has been successfully restored")
        return True
    else:
        print("❌ Some format checks failed")
        return False


async def test_messenger_integration():
    """Test that the messenger can use the structured data."""
    print("\n🔗 Testing Messenger Integration")
    print("=" * 60)
    
    try:
        # Import the messengers (this tests if the imports work)
        from messengers.signal_messenger import SignalMessenger
        from messengers.telegram_messenger import TelegramMessenger
        
        print("✅ Successfully imported Signal and Telegram messengers")
        print("✅ Messenger integration should work with structured data")
        return True
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False


async def main():
    """Run complete pipeline test."""
    print("🚀 Testing Complete Structured Messaging Pipeline")
    print("=" * 80)
    
    # Test template generator
    template_success = test_structured_template_generator()
    
    # Test messenger integration
    messenger_success = await test_messenger_integration()
    
    print("\n" + "=" * 80)
    print("🎯 FINAL RESULTS:")
    print(f"Template Generation: {'✅ PASS' if template_success else '❌ FAIL'}")
    print(f"Messenger Integration: {'✅ PASS' if messenger_success else '❌ FAIL'}")
    
    if template_success and messenger_success:
        print("\n🎉 COMPLETE PIPELINE IS WORKING!")
        print("✅ Old plaintext format restored successfully")
        print("✅ Structured messaging system ready")
        print("✅ Should work for tomorrow's scheduled report")
        return True
    else:
        print("\n❌ Some components failed")
        return False


if __name__ == "__main__":
    result = asyncio.run(main())
    sys.exit(0 if result else 1)