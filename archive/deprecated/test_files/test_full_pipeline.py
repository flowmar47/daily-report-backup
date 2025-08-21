#!/usr/bin/env python3
"""Test the full daily report pipeline manually"""

import asyncio
import logging
from main import DailyReportAutomation

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def main():
    """Run the daily report manually"""
    try:
        logger.info("Starting manual test of daily report pipeline...")
        
        # Create the automation instance
        automation = DailyReportAutomation()
        
        # Run the daily report
        await automation.run_daily_report()
        
        logger.info("Manual test completed successfully!")
        
    except Exception as e:
        logger.error(f"Manual test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())