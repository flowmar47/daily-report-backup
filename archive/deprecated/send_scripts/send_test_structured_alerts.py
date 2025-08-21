#!/usr/bin/env python3
"""
Test script to send structured financial alerts to Signal and Telegram.
Demonstrates the new structured template format.
"""

import asyncio
import sys
from pathlib import Path

# Add the project root to the path
sys.path.insert(0, str(Path(__file__).parent))

from src.data_processors.template_generator import StructuredTemplateGenerator, format_message_for_platform
from messenger_compatibility import SignalMessenger, TelegramMessenger


def create_test_financial_data():
    """Create test financial data in the expected format."""
    return {
        'has_real_data': True,
        'timestamp': '2025-01-04 08:00:00',
        'source_url': 'https://www.mymama.uk/copy-of-alerts-essentials-1',
        'forex_alerts': {
            'EURUSD': {
                'high': '1.1250',
                'average': '1.1100', 
                'low': '1.0950',
                'signal': 'BUY',
                'trade_type': 'MT4 BUY < 1.1000',
                'exit': '1.1200',
                'trade_status': 'TRADE IN PROFIT',
                'special_badge': 'NEW!'
            },
            'GBPUSD': {
                'high': '1.2850',
                'average': '1.2700',
                'low': '1.2550', 
                'signal': 'SELL',
                'trade_type': 'MT4 SELL > 1.2800',
                'exit': '1.2600'
            }
        },
        'swing_trades': [
            {
                'company': 'Apple Inc.',
                'ticker': 'AAPL',
                'earnings_date': 'January 30, 2025',
                'current_price': '$225.50',
                'rationale': 'Strong Q4 results expected with record iPhone sales and continued services growth. AI integration driving upgrade cycles.'
            }
        ],
        'day_trades': [
            {
                'company': 'Tesla Inc.',
                'ticker': 'TSLA', 
                'earnings_date': 'January 29, 2025',
                'current_price': '$380.25',
                'rationale': 'Q4 delivery numbers exceeded expectations. Strong demand for Model Y in international markets creates trading opportunities.'
            }
        ],
        'options_data': [
            {
                'ticker': 'QQQ',
                'high_52week': '520.75',
                'low_52week': '415.25',
                'call_strike': 'CALL > 515.00',
                'put_strike': 'PUT < 510.00',
                'status': 'TRADE IN PROFIT'
            }
        ]
    }


async def test_signal_structured_message():
    """Test sending structured message to Signal."""
    print("📱 Testing Signal Structured Message")
    print("-" * 50)
    
    try:
        from messengers.signal_messenger import SignalMessenger
        from src.config.settings import settings
        
        # Get Signal configuration
        signal_config = settings.get_signal_config()
        
        if not signal_config.get('phone_number') or not signal_config.get('group_id'):
            print("⚠️ Signal not configured - skipping test")
            return False
        
        # Initialize Signal messenger
        signal_messenger = SignalMessenger(signal_config)
        
        # Test connection
        connection_ok = await signal_messenger.test_connection()
        if not connection_ok:
            print("❌ Signal connection test failed")
            return False
        
        # Create test data
        financial_data = create_test_financial_data()
        
        # Send structured financial data
        result = await signal_messenger.send_structured_financial_data(financial_data)
        
        if result.status.name == 'SUCCESS':
            print("✅ Signal structured message sent successfully!")
            return True
        else:
            print(f"❌ Signal send failed: {result.error}")
            return False
            
    except Exception as e:
        print(f"❌ Signal test error: {e}")
        return False


async def test_telegram_structured_message():
    """Test sending structured message to Telegram."""
    print("💬 Testing Telegram Structured Message")
    print("-" * 50)
    
    try:
        from messengers.telegram_messenger import TelegramMessenger
        from src.config.settings import settings
        
        # Get Telegram configuration
        telegram_config = settings.get_telegram_config()
        
        if not telegram_config.get('bot_token') or not telegram_config.get('chat_id'):
            print("⚠️ Telegram not configured - skipping test")
            return False
        
        # Initialize Telegram messenger
        telegram_messenger = TelegramMessenger(telegram_config)
        
        # Test connection
        connection_ok = await telegram_messenger.test_connection()
        if not connection_ok:
            print("❌ Telegram connection test failed")
            return False
        
        # Create test data
        financial_data = create_test_financial_data()
        
        # Send structured financial data
        result = await telegram_messenger.send_structured_financial_data(financial_data)
        
        if result.status.name == 'SUCCESS':
            print("✅ Telegram structured message sent successfully!")
            return True
        else:
            print(f"❌ Telegram send failed: {result.error}")
            return False
            
    except Exception as e:
        print(f"❌ Telegram test error: {e}")
        return False


def test_template_formatting():
    """Test the template formatting for different platforms."""
    print("🎨 Testing Template Formatting")
    print("-" * 50)
    
    financial_data = create_test_financial_data()
    
    # Test Signal format
    signal_message = format_message_for_platform(financial_data, "signal")
    print("📱 Signal Format Preview:")
    print(signal_message[:200] + "..." if len(signal_message) > 200 else signal_message)
    print()
    
    # Test Telegram format
    telegram_message = format_message_for_platform(financial_data, "telegram")
    print("💬 Telegram Format Preview:")
    print(telegram_message[:200] + "..." if len(telegram_message) > 200 else telegram_message)
    print()
    
    return True


async def main():
    """Main test function."""
    print("🚀 Testing Structured Financial Alerts System")
    print("=" * 60)
    
    # Test template formatting
    test_template_formatting()
    
    # Test actual messaging (if configured)
    print("\n📨 Testing Live Messaging (if configured)")
    print("-" * 50)
    
    # Test Signal
    signal_success = await test_signal_structured_message()
    
    print()
    
    # Test Telegram  
    telegram_success = await test_telegram_structured_message()
    
    print("\n📊 Test Summary")
    print("-" * 50)
    print(f"📱 Signal: {'✅ SUCCESS' if signal_success else '❌ FAILED/SKIPPED'}")
    print(f"💬 Telegram: {'✅ SUCCESS' if telegram_success else '❌ FAILED/SKIPPED'}")
    
    if signal_success or telegram_success:
        print("\n🎉 At least one messaging platform is working correctly!")
    else:
        print("\n⚠️ No messaging platforms could be tested - check configuration")
    
    print("\n💡 To configure messengers, update your .env file with:")
    print("   SIGNAL_PHONE_NUMBER, SIGNAL_GROUP_ID")
    print("   TELEGRAM_BOT_TOKEN, TELEGRAM_GROUP_ID")


if __name__ == "__main__":
    asyncio.run(main())