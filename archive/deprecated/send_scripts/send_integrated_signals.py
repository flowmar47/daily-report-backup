#!/usr/bin/env python3
"""
Production Integrated Signal Sender
Generates and sends high-quality validated signals
Includes automatic 6 AM scheduling
"""

import asyncio
import os
import requests
import sys
import schedule
import time
import threading
from datetime import datetime
from dotenv import load_dotenv

from integrated_signal_generator import generate_daily_signals

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

async def generate_and_send_signals():
    """Generate and send integrated signals"""
    
    print("🚀 INTEGRATED FOREX SIGNAL GENERATION")
    print("=" * 60)
    print("⏳ Validating prices from multiple APIs...")
    print("⏳ Running comprehensive technical analysis...")
    print("⏳ Analyzing economic fundamentals...")
    print("⏳ Processing market sentiment...")
    print("⏳ Applying adaptive signal filtering...")
    
    try:
        # Generate signals using integrated system
        result = await generate_daily_signals()
        
        if not result:
            print("\n❌ SIGNAL GENERATION FAILED")
            print("No validated data available or insufficient signal quality")
            print("NO MESSAGES SENT to prevent transmission of unvalidated data")
            return False
        
        # Extract the clean message
        signal_message = result['message']
        
        print(f"\n✅ SIGNALS GENERATED SUCCESSFULLY")
        print(f"📊 Validated prices: {len(result['validated_prices'])} pairs")
        print(f"🎯 Quality signals: {result['signal_count']}")
        print(f"⏰ Generated: {result['timestamp'].strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"🔍 Source: {result['source']}")
        
        print(f"\n📤 SENDING TO GROUPS...")
        print("=" * 60)
        print(signal_message)
        print("=" * 60)
        
        # Send to both platforms
        telegram_success = send_telegram_message(signal_message)
        signal_success = send_signal_message(signal_message)
        
        print("\n" + "="*60)
        print("DELIVERY STATUS:")
        print("="*60)
        print(f"Telegram: {'✅ SENT' if telegram_success else '❌ FAILED'}")
        print(f"Signal: {'✅ SENT' if signal_success else '❌ FAILED'}")
        print("="*60)
        
        if telegram_success or signal_success:
            print("✅ INTEGRATED SIGNALS SENT SUCCESSFULLY!")
            print("💎 All signals validated through multi-API consensus")
            print("📈 Technical + Economic + Sentiment analysis complete")
            
            # Log signal details for tracking
            print("\n📋 SIGNAL SUMMARY:")
            for i, signal in enumerate(result['signals'], 1):
                print(f"{i}. {signal['pair']} {signal['action']} - {signal['target_pips']} pips "
                      f"(Strength: {signal['signal_strength']:.2f}, Confidence: {signal['confidence']:.2f})")
            
            return True
        else:
            print("❌ Failed to send signals to any messenger")
            return False
            
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        print("NO MESSAGES SENT due to system error")
        return False

def run_scheduled_signal_generation():
    """Run signal generation (called by scheduler)"""
    print(f"\n🕕 SCHEDULED SIGNAL GENERATION - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    try:
        success = asyncio.run(generate_and_send_signals())
        if success:
            print("✅ Scheduled signal generation completed successfully")
        else:
            print("⚠️  Scheduled signal generation failed - no signals sent")
    except Exception as e:
        print(f"❌ Scheduled signal generation error: {e}")

def setup_daily_schedule():
    """Setup automatic daily scheduling at 6 AM"""
    
    # Schedule for 6:00 AM every weekday
    schedule.every().monday.at("06:00").do(run_scheduled_signal_generation)
    schedule.every().tuesday.at("06:00").do(run_scheduled_signal_generation)
    schedule.every().wednesday.at("06:00").do(run_scheduled_signal_generation)
    schedule.every().thursday.at("06:00").do(run_scheduled_signal_generation)
    schedule.every().friday.at("06:00").do(run_scheduled_signal_generation)
    
    print("📅 AUTOMATIC SCHEDULING CONFIGURED:")
    print("⏰ Daily signals at 6:00 AM (Monday-Friday)")
    print("🔄 System will run continuously...")
    
    # Run scheduler in background thread
    def run_scheduler():
        while True:
            schedule.run_pending()
            time.sleep(60)  # Check every minute
    
    scheduler_thread = threading.Thread(target=run_scheduler, daemon=True)
    scheduler_thread.start()
    
    return scheduler_thread

async def main():
    """Main function - immediate generation + scheduling"""
    
    print("🎯 INTEGRATED SIGNAL SYSTEM STARTING...")
    print("=" * 60)
    
    # Setup automatic scheduling first
    scheduler_thread = setup_daily_schedule()
    
    # Run immediate signal generation
    print("\n🚀 RUNNING IMMEDIATE SIGNAL GENERATION:")
    success = await generate_and_send_signals()
    
    if success:
        print(f"\n🎉 SUCCESS: Integrated signals sent at {datetime.now().strftime('%H:%M:%S')}")
    else:
        print(f"\n⚠️  NO SIGNALS SENT: Validation failed or insufficient quality")
    
    # Keep scheduler running
    print(f"\n📡 SCHEDULER STATUS: Running (Thread: {scheduler_thread.is_alive()})")
    print("🔄 Next scheduled run: Tomorrow at 6:00 AM")
    print("💡 Press Ctrl+C to stop the scheduler")
    
    try:
        # Keep the main process alive for scheduling
        while True:
            await asyncio.sleep(3600)  # Sleep for 1 hour
            current_time = datetime.now().strftime('%H:%M')
            if current_time == "06:00":
                print(f"⏰ Scheduled time reached: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    except KeyboardInterrupt:
        print("\n👋 Scheduler stopped by user")
    
    return success

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)