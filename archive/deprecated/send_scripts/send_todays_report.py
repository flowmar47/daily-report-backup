#!/usr/bin/env python3
"""
Send today's financial report and heatmaps to all platforms
"""

import asyncio
import sys
import logging
from pathlib import Path
from datetime import datetime

# Add the project root to Python path
sys.path.insert(0, str(Path(__file__).parent))

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

async def send_todays_report():
    """Send today's financial report and heatmaps"""
    logger.info("📊 Sending today's financial report and heatmaps...")
    
    try:
        # Import main automation
        from main import DailyReportAutomation
        
        # Create instance
        automation = DailyReportAutomation()
        
        # Run the report
        logger.info("🔄 Running daily report workflow...")
        await automation.run_daily_report()
        
        logger.info("✅ Successfully sent report and heatmaps to all platforms!")
        return True
        
    except Exception as e:
        logger.error(f"❌ Error: {e}")
        return False

async def main():
    """Main function"""
    logger.info("🚀 Starting financial data distribution...")
    logger.info("📤 Sending to Signal, Telegram, and WhatsApp...")
    
    success = await send_todays_report()
    
    if success:
        logger.info("\n🎉 SUCCESS! Today's report sent to all platforms!")
        logger.info("✅ Financial report sent")
        logger.info("✅ Categorical heatmap sent")
        logger.info("✅ Forex pairs heatmap sent")
    else:
        logger.error("\n❌ Failed to send report")

if __name__ == "__main__":
    asyncio.run(main())