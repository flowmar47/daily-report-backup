#!/usr/bin/env python3
"""
Send Validated Real-Time Forex Signals
ONLY sends signals if prices are validated from multiple APIs
"""

import asyncio
import os
import requests
import sys
from datetime import datetime
from dotenv import load_dotenv

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from generate_real_signals import RealTimeSignalGenerator

# Load environment variables
load_dotenv()

def send_telegram_message(message):
    """Send message to Telegram"""
    bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
    group_id = os.getenv('TELEGRAM_GROUP_ID')
    
    if not bot_token or not group_id:
        print("❌ Telegram credentials not found")
        return False
    
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    
    data = {
        'chat_id': group_id,
        'text': message,
        'parse_mode': 'HTML'
    }
    
    try:
        response = requests.post(url, data=data, timeout=10)
        if response.status_code == 200:
            print("✅ Message sent to Telegram successfully")
            return True
        else:
            print(f"❌ Telegram error: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Telegram error: {e}")
        return False

def send_signal_message(message):
    """Send message to Signal via Docker API"""
    signal_url = "http://localhost:8080/v2/send"
    phone_number = os.getenv('SIGNAL_PHONE_NUMBER', '+16572464949')
    group_id = os.getenv('SIGNAL_GROUP_ID', 'group.cUY1YUE5SHRRMW0wQy9SVGMrSWNvVTQrakluaU00YXlBeVBscUdLUFdMTT0=')
    
    data = {
        'number': phone_number,
        'recipients': [group_id],
        'message': message
    }
    
    try:
        response = requests.post(signal_url, json=data, timeout=10)
        if response.status_code == 201:
            print("✅ Message sent to Signal successfully")
            return True
        else:
            print(f"❌ Signal error: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Signal error: {e}")
        return False

async def main():
    """Generate and send validated signals"""
    
    print("🔍 GENERATING VALIDATED FOREX SIGNALS")
    print("=" * 50)
    print("⏳ Fetching real-time prices from multiple APIs...")
    print("⏳ Validating price consensus across sources...")
    print("⏳ Generating signals only with validated data...")
    
    generator = RealTimeSignalGenerator()
    
    try:
        # Generate signals with validated prices
        result = await generator.generate_signals()
        
        if not result:
            print("\n❌ SIGNAL GENERATION FAILED")
            print("No validated prices available or insufficient data quality")
            print("NO MESSAGES WILL BE SENT to prevent fake data transmission")
            return False
        
        # Extract the message
        signal_message = result['message']
        
        print(f"\n✅ SIGNALS GENERATED SUCCESSFULLY")
        print(f"📊 Validated prices from {len(result['validated_prices'])} sources")
        print(f"🎯 Generated {len(result['signals'])} trading signals")
        print(f"⏰ Timestamp: {result['timestamp'].strftime('%Y-%m-%d %H:%M:%S UTC')}")
        
        print(f"\n📤 SENDING TO MESSENGERS...")
        print("=" * 50)
        print(signal_message)
        print("=" * 50)
        
        # Send to both platforms
        telegram_success = send_telegram_message(signal_message)
        signal_success = send_signal_message(signal_message)
        
        print("\n" + "="*50)
        print("DELIVERY STATUS:")
        print("="*50)
        print(f"Telegram: {'✅ SENT' if telegram_success else '❌ FAILED'}")
        print(f"Signal: {'✅ SENT' if signal_success else '❌ FAILED'}")
        print("="*50)
        
        if telegram_success or signal_success:
            print("✅ VALIDATED SIGNALS SENT SUCCESSFULLY!")
            print("💰 All prices were validated from multiple API sources")
            return True
        else:
            print("❌ Failed to send signals to any messenger")
            return False
            
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        print("NO MESSAGES WILL BE SENT due to error")
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    
    if success:
        print(f"\n🎉 SUCCESS: Real-time validated signals sent at {datetime.now().strftime('%H:%M:%S')}")
    else:
        print(f"\n⚠️  NO SIGNALS SENT: Data validation failed or insufficient sources")
    
    sys.exit(0 if success else 1)