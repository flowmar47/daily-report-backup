#!/usr/bin/env python3
"""
Run Full Automation Script
Executes the complete financial alerts workflow with structured template format
"""

import asyncio
import sys
import logging
from pathlib import Path
from datetime import datetime

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from main import DailyReportAutomation

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/full_automation.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


async def run_full_automation():
    """Run the complete automation workflow"""
    try:
        logger.info("=" * 60)
        logger.info("🚀 Starting Full Financial Alerts Automation")
        logger.info(f"📅 Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info("=" * 60)
        
        # Initialize automation
        automation = DailyReportAutomation()
        
        # Run the daily report workflow
        await automation.run_daily_report()
        
        logger.info("✅ Full automation completed successfully!")
        
    except Exception as e:
        logger.error(f"❌ Automation failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


def main():
    """Main entry point"""
    logger.info("🔧 Initializing full automation run...")
    
    # Run the automation
    asyncio.run(run_full_automation())


if __name__ == "__main__":
    main()