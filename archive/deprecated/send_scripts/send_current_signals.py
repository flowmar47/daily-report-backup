#!/usr/bin/env python3
"""
Send Current Generated Signals - Direct Messaging
"""

import os
import requests
import json
from datetime import datetime

# Load environment variables
from dotenv import load_dotenv
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

def main():
    """Send the current signals"""
    
    # The signal report from the demo generation
    signal_report = f"""FOREX PAIRS

Pair: USDCAD
High: 1.39350
Average: 1.38500
Low: 1.38500
MT4 Action: MT4 BUY
Exit: 1.39350

Pair: CHFJPY
High: 164.50000
Average: 164.50000
Low: 163.60000
MT4 Action: MT4 SELL
Exit: 163.60000

Pair: USDJPY
High: 147.76000
Average: 146.80000
Low: 146.80000
MT4 Action: MT4 BUY
Exit: 147.76000"""

    print("📤 Sending signals to messengers...")
    print(f"\n{signal_report}\n")
    
    # Send to both platforms
    telegram_success = send_telegram_message(signal_report)
    signal_success = send_signal_message(signal_report)
    
    print("\n" + "="*50)
    print("DELIVERY STATUS:")
    print("="*50)
    print(f"Telegram: {'✅ SENT' if telegram_success else '❌ FAILED'}")
    print(f"Signal: {'✅ SENT' if signal_success else '❌ FAILED'}")
    print("="*50)
    
    if telegram_success or signal_success:
        print("✅ SIGNALS SENT SUCCESSFULLY!")
        return True
    else:
        print("❌ Failed to send signals")
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)