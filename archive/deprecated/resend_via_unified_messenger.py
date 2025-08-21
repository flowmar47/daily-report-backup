#!/usr/bin/env python3
"""
Resend via Unified Messenger - Test actual Signal delivery
"""

import asyncio
import json
import logging
import os
from datetime import datetime
from pathlib import Path

# Add paths for imports
import sys
sys.path.append('/home/ohms/OhmsAlertsReports/src/daily_report')
sys.path.append('/home/ohms/OhmsAlertsReports/src')

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Set environment variables
os.environ.setdefault('SIGNAL_PHONE_NUMBER', '+16572463906')
os.environ.setdefault('SIGNAL_GROUP_ID', 'group.ZmFLQ25IUTBKbWpuNFdpaDdXTjVoVXpYOFZtNGVZZ1lYRGdwMWpMcW0zMD0=')
os.environ.setdefault('SIGNAL_API_URL', 'http://localhost:8080')
os.environ.setdefault('TELEGRAM_BOT_TOKEN', '7695859844:AAE_PxUOckN57S5eGyFKVW4fp4pReR0zzMI')
os.environ.setdefault('TELEGRAM_GROUP_ID', '-1002548864790')

async def send_via_unified_messenger():
    """Test both Signal and Telegram delivery using the unified messenger"""
    try:
        # Import the unified messenger
        from messengers.unified_messenger import send_structured_financial_data
        
        # Load today's financial data
        data_file = 'real_alerts_only/real_alerts_20250702_060141.json'
        with open(data_file, 'r', encoding='utf-8') as f:
            financial_data = json.load(f)
        
        # Format a simple test message with today's data
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M PST")
        
        # Create structured financial data from today's real data
        forex_section = "FOREX PAIRS\n\n"
        for pair, data in financial_data.get('forex_alerts', {}).items():
            forex_section += f"Pair: {pair}\n"
            forex_section += f"High: {data.get('high', 'N/A')}\n"
            forex_section += f"Average: {data.get('average', 'N/A')}\n"
            forex_section += f"Low: {data.get('low', 'N/A')}\n"
            forex_section += f"MT4 Action: MT4 {data.get('signal', 'N/A')}\n"
            forex_section += f"Exit: {data.get('exit', 'N/A')}\n\n"
        
        test_message = f"DAILY FINANCIAL ALERTS - {timestamp}\n\n{forex_section}=" * 50
        
        logger.info("📤 Sending via unified messenger...")
        
        # Send the structured financial data
        results = await send_structured_financial_data(test_message)
        
        # Log results
        for platform, result in results.items():
            if result.success:
                logger.info(f"✅ {platform.upper()}: Message sent successfully (ID: {result.message_id})")
            else:
                logger.error(f"❌ {platform.upper()}: Failed - {result.error}")
        
        return all(result.success for result in results.values())
        
    except Exception as e:
        logger.error(f"❌ Unified messenger test failed: {e}")
        return False

async def main():
    """Main test execution"""
    logger.info("=" * 60)
    logger.info("TESTING UNIFIED MESSENGER - Signal & Telegram Delivery")
    logger.info("=" * 60)
    
    success = await send_via_unified_messenger()
    
    if success:
        logger.info("✅ All platforms delivered successfully!")
    else:
        logger.error("❌ Some platforms failed delivery")

if __name__ == "__main__":
    asyncio.run(main())