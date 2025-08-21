#!/usr/bin/env python3
"""
Test sending with recent working data to verify messaging functionality
"""

import asyncio
import json
import os
import sys
import logging
from datetime import datetime
from pathlib import Path

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def test_messaging_with_recent_data():
    """Test messaging using recent working data"""
    try:
        # Use recent working data file
        data_file = "/home/ohms/OhmsAlertsReports/daily-report/output/mymama/mymama_data_20250625_091940.json"
        
        if not os.path.exists(data_file):
            logger.error(f"Data file not found: {data_file}")
            return False
            
        # Import unified messenger
        sys.path.append(os.path.dirname(os.path.abspath(__file__)))
        from src.messengers.unified_messenger import UnifiedMultiMessenger
        
        # Create test message
        test_message = """🔔 DAILY FINANCIAL ALERTS - TEST MESSAGE

📊 FOREX PAIRS
EURUSD - High: 1.1158, Low: 1.0238, Action: SELL

📈 OPTIONS TRADES  
QQQ - Strike: 521.68, Status: TRADE IN PROFIT

⏰ Generated: {}

This is a test message to verify messaging functionality.""".format(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

        # Initialize messenger for all platforms
        platforms = ['telegram', 'signal', 'whatsapp']
        multi_messenger = UnifiedMultiMessenger(platforms)
        
        logger.info("Sending test message to all platforms...")
        
        # Send to all platforms
        results = await multi_messenger.send_structured_financial_data(test_message)
        
        # Analyze results
        success_count = 0
        for platform, result in results.items():
            if result.success:
                logger.info(f"✅ {platform.upper()}: Message sent successfully")
                success_count += 1
            else:
                logger.error(f"❌ {platform.upper()}: Failed - {result.error}")
        
        # Cleanup
        await multi_messenger.cleanup()
        
        logger.info(f"Test completed: {success_count}/{len(platforms)} platforms successful")
        
        return success_count > 0
        
    except Exception as e:
        logger.error(f"Error in test messaging: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """Main function"""
    logger.info("Testing messaging functionality with recent data...")
    
    success = await test_messaging_with_recent_data()
    
    if success:
        logger.info("✅ Messaging test completed successfully!")
    else:
        logger.error("❌ Messaging test failed")
    
    return success

if __name__ == "__main__":
    asyncio.run(main())