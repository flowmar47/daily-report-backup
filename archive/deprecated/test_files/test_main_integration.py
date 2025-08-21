#!/usr/bin/env python3
"""
Test the main.py integration with the new plaintext format.
"""

import sys
import asyncio
from pathlib import Path

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

from main import DailyReportAutomation


async def test_main_integration():
    """Test the main report generation with plaintext format."""
    print("🧪 Testing Main Integration with Plaintext Format")
    print("=" * 60)
    
    # Create sample financial data
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
            }
        ],
        'swing_trades': [
            {
                'company': 'JOYY Inc.',
                'ticker': 'JOYY',
                'earnings_date': 'May 26, 2025',
                'current_price': '$47.67',
                'rationale': 'Strong Q1 2025 performance with revenue growth.'
            }
        ],
        'day_trades': [
            {
                'company': 'PDD Holdings Inc.',
                'ticker': 'PDD',
                'earnings_date': 'May 27, 2025',
                'current_price': '$95.60',
                'rationale': 'Volatility opportunity from Q1 results.'
            }
        ]
    }
    
    # Create automation instance
    automation = DailyReportAutomation()
    
    # Test generate_report method
    print("📊 Testing generate_report method...")
    try:
        report = await automation.generate_report(sample_data)
        
        if report:
            print("✅ generate_report SUCCESS")
            print("\n📄 GENERATED REPORT:")
            print("=" * 50)
            print(report)
            print("=" * 50)
            
            # Check if it's the plaintext format (no emojis in main content)
            emoji_indicators = ['📊', '🔴', '🟢', '📈', '⚡', '🎯']
            has_emojis = any(emoji in report for emoji in emoji_indicators)
            
            plaintext_indicators = ['FOREX PAIRS', 'MT4 Action:', 'Symbol:', 'PREMIUM SWING TRADES']
            has_plaintext = any(indicator in report for indicator in plaintext_indicators)
            
            print(f"\n🔍 Format Analysis:")
            print(f"Has emojis: {'❌ YES (bad)' if has_emojis else '✅ NO (good)'}")
            print(f"Has plaintext indicators: {'✅ YES (good)' if has_plaintext else '❌ NO (bad)'}")
            
            if not has_emojis and has_plaintext:
                print("✅ SUCCESS: Using plaintext format as expected!")
                return True
            else:
                print("❌ FAILURE: Still using emoji format")
                return False
        else:
            print("❌ generate_report returned None")
            return False
            
    except Exception as e:
        print(f"❌ generate_report FAILED: {e}")
        return False


async def test_legacy_report():
    """Test the legacy report method."""
    print("\n🧪 Testing _generate_legacy_report method...")
    
    sample_data = {
        'has_real_data': True,
        'forex_alerts': {
            'EURUSD': {
                'high': '1.1158',
                'average': '1.0742',
                'low': '1.0238',
                'signal': 'SELL',
                'trade_type': 'MT4 SELL',
                'exit': '1.0850'
            }
        }
    }
    
    automation = DailyReportAutomation()
    
    try:
        legacy_report = automation._generate_legacy_report(sample_data, "2025-06-10 08:00:00")
        
        if legacy_report:
            print("✅ _generate_legacy_report SUCCESS")
            print(f"Report preview: {legacy_report[:100]}...")
            
            # Check format
            has_plaintext = 'FOREX PAIRS' in legacy_report and 'MT4 Action:' in legacy_report
            print(f"Has plaintext format: {'✅ YES' if has_plaintext else '❌ NO'}")
            
            return has_plaintext
        else:
            print("❌ _generate_legacy_report returned None")
            return False
            
    except Exception as e:
        print(f"❌ _generate_legacy_report FAILED: {e}")
        return False


async def main():
    """Run integration tests."""
    print("🚀 Testing Main.py Integration with Plaintext Format")
    print("=" * 80)
    
    # Test main report generation
    main_success = await test_main_integration()
    
    # Test legacy fallback
    legacy_success = await test_legacy_report()
    
    print("\n" + "=" * 80)
    print("🎯 FINAL INTEGRATION TEST RESULTS:")
    print(f"Main generate_report: {'✅ PASS' if main_success else '❌ FAIL'}")
    print(f"Legacy fallback: {'✅ PASS' if legacy_success else '❌ FAIL'}")
    
    if main_success and legacy_success:
        print("\n🎉 MAIN.PY INTEGRATION SUCCESSFUL!")
        print("✅ Both primary and fallback methods use plaintext format")
        print("✅ Tomorrow's scheduled report will use the correct format")
        print("✅ No more emoji-based format will be sent")
        return True
    else:
        print("\n❌ Integration tests failed")
        return False


if __name__ == "__main__":
    result = asyncio.run(main())
    sys.exit(0 if result else 1)