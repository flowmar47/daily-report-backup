#!/usr/bin/env python3
"""
Complete platform test: Signal, Telegram, and WhatsApp with heatmaps
"""

import asyncio
import os
import sys
import time
import logging
from datetime import datetime
from pathlib import Path

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def send_to_signal_and_telegram():
    """Send messages to Signal and Telegram using unified messenger"""
    try:
        # Import unified messenger
        sys.path.append(os.path.dirname(os.path.abspath(__file__)))
        from src.messengers.unified_messenger import UnifiedMultiMessenger
        
        # Create test message
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        test_message = f"""📊 OHMS FINANCIAL ALERTS - COMPLETE SYSTEM TEST

🔔 Daily Financial Report - {timestamp}

📈 FOREX PAIRS
EURUSD - High: 1.1158, Low: 1.0238, Action: SELL
GBPUSD - High: 1.2745, Low: 1.2156, Action: BUY

📊 OPTIONS TRADES  
QQQ - Strike: 521.68, Status: TRADE IN PROFIT
SPY - Strike: 455.00, Status: MONITORING

💼 EARNINGS UPDATES
NVDA - Earnings Date: Next Week
AAPL - Post-earnings analysis available

⚡ System Status: ALL PLATFORMS OPERATIONAL
📱 Signal: ✅ Connected
📱 Telegram: ✅ Connected  
📱 WhatsApp: 🔄 Testing

Generated: {timestamp}"""

        # Initialize messenger for Signal and Telegram only
        platforms = ['telegram', 'signal']
        multi_messenger = UnifiedMultiMessenger(platforms)
        
        logger.info("Sending test message to Signal and Telegram...")
        
        # Send to both platforms
        results = await multi_messenger.send_structured_financial_data(test_message)
        
        # Analyze results
        success_count = 0
        for platform, result in results.items():
            if result.success:
                logger.info(f"✅ {platform.upper()}: Message sent successfully")
                success_count += 1
            else:
                logger.error(f"❌ {platform.upper()}: Failed - {result.error}")
        
        # Send heatmap images
        heatmap_files = [
            "/home/ohms/OhmsAlertsReports/daily-report/categorical_heatmap_20250703_102238.png",
            "/home/ohms/OhmsAlertsReports/daily-report/forex_pairs_20250703_102238.png"
        ]
        
        for heatmap_path in heatmap_files:
            if os.path.exists(heatmap_path):
                caption = f"Financial Heatmap - {os.path.basename(heatmap_path)}"
                try:
                    heatmap_results = await multi_messenger.send_image_to_all(heatmap_path, caption)
                    for platform, result in heatmap_results.items():
                        if result.success:
                            logger.info(f"✅ {platform.upper()}: Heatmap sent successfully")
                        else:
                            logger.error(f"❌ {platform.upper()}: Heatmap failed - {result.error}")
                except Exception as e:
                    logger.warning(f"Heatmap sending not supported in current version: {e}")
        
        # Cleanup
        await multi_messenger.cleanup()
        
        logger.info(f"Signal/Telegram test completed: {success_count}/{len(platforms)} platforms successful")
        return success_count > 0
        
    except Exception as e:
        logger.error(f"Error in Signal/Telegram test: {e}")
        import traceback
        traceback.print_exc()
        return False

def send_to_whatsapp():
    """Send messages to WhatsApp using Selenium"""
    try:
        from whatsapp_messenger_fixed import WhatsAppMessenger
        
        messenger = WhatsAppMessenger()
        
        # Setup driver
        if not messenger.setup_driver():
            logger.error("Failed to setup WhatsApp driver")
            return False
        
        # Authenticate (will require QR scan if not already authenticated)
        if not messenger.authenticate():
            logger.error("Failed to authenticate with WhatsApp")
            return False
        
        # Test group name - MODIFY THIS TO YOUR ACTUAL GROUP NAME
        group_name = "Ohms Financial Alerts"
        
        # Create WhatsApp test message
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        whatsapp_message = f"""🔔 OHMS FINANCIAL ALERTS - WhatsApp Integration Test

📊 Daily Financial Report - {timestamp}

💹 FOREX SIGNALS
• EURUSD: SELL at 1.1158
• GBPUSD: BUY at 1.2156

📈 OPTIONS ALERTS
• QQQ Strike 521.68: IN PROFIT
• SPY Strike 455.00: MONITORING

📱 Platform Status:
✅ Signal: Connected
✅ Telegram: Connected
✅ WhatsApp: NOW CONNECTED!

Heatmaps will follow in separate messages...

Generated: {timestamp}"""
        
        # Send text message
        logger.info("Sending message to WhatsApp...")
        success = messenger.send_message(group_name, whatsapp_message)
        
        if success:
            # Send heatmap images
            heatmap_files = [
                "/home/ohms/OhmsAlertsReports/daily-report/categorical_heatmap_20250703_102238.png",
                "/home/ohms/OhmsAlertsReports/daily-report/forex_pairs_20250703_102238.png"
            ]
            
            for i, heatmap_path in enumerate(heatmap_files):
                if os.path.exists(heatmap_path):
                    caption = f"📊 Financial Heatmap {i+1}/2 - {timestamp}"
                    logger.info(f"Sending heatmap {i+1} to WhatsApp...")
                    messenger.send_image(group_name, heatmap_path, caption)
                    time.sleep(3)  # Delay between images
        
        messenger.close()
        return success
        
    except Exception as e:
        logger.error(f"Error in WhatsApp test: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """Main test function"""
    logger.info("🚀 Starting complete platform test...")
    
    # Test Signal and Telegram (async)
    signal_telegram_success = await send_to_signal_and_telegram()
    
    # Test WhatsApp (sync)
    logger.info("\n📱 Testing WhatsApp integration...")
    logger.info("NOTE: If this is the first time, you'll need to scan the QR code")
    
    whatsapp_success = send_to_whatsapp()
    
    # Summary
    logger.info("\n📋 TEST SUMMARY:")
    logger.info(f"Signal/Telegram: {'✅ SUCCESS' if signal_telegram_success else '❌ FAILED'}")
    logger.info(f"WhatsApp: {'✅ SUCCESS' if whatsapp_success else '❌ FAILED'}")
    
    total_success = signal_telegram_success and whatsapp_success
    
    if total_success:
        logger.info("\n🎉 ALL PLATFORMS OPERATIONAL!")
        logger.info("Your financial alerts system is ready to send to Signal, Telegram, and WhatsApp!")
    else:
        logger.info("\n⚠️  Some platforms had issues - check logs above")
    
    return total_success

if __name__ == "__main__":
    asyncio.run(main())