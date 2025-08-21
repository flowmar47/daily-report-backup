#!/usr/bin/env python3
"""
Enhanced Daily Report Runner
Runs both MyMama alerts and interest rate heatmaps
"""

import asyncio
import sys
import os
import logging

# Add src directory to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from main import DailyReportAutomation
from daily_heatmap_sender import DailyHeatmapSender

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/enhanced_daily.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


async def run_enhanced_daily_report():
    """Run both MyMama report and heatmaps"""
    logger.info("🚀 Starting enhanced daily report with heatmaps...")
    
    overall_success = True
    
    # Step 1: Run the standard MyMama daily report
    logger.info("📊 Step 1: Running MyMama daily report...")
    try:
        automation = DailyReportAutomation()
        mymama_success = await automation.run_daily_report()
        
        if mymama_success:
            logger.info("✅ MyMama daily report completed successfully")
        else:
            logger.warning("⚠️ MyMama daily report had issues")
            overall_success = False
            
    except Exception as e:
        logger.error(f"❌ Error in MyMama report: {e}")
        overall_success = False
    
    # Step 2: Generate and send heatmaps
    logger.info("🌡️ Step 2: Generating and sending interest rate heatmaps...")
    try:
        heatmap_sender = DailyHeatmapSender()
        heatmap_success = await heatmap_sender.run_daily_heatmaps()
        
        if heatmap_success:
            logger.info("✅ Interest rate heatmaps completed successfully")
        else:
            logger.warning("⚠️ Interest rate heatmaps had issues")
            overall_success = False
            
    except Exception as e:
        logger.error(f"❌ Error in heatmap generation: {e}")
        overall_success = False
    
    # Summary
    if overall_success:
        logger.info("🎉 Enhanced daily report completed successfully!")
    else:
        logger.warning("⚠️ Enhanced daily report completed with some issues")
    
    return overall_success


def run_enhanced_daily_report_sync():
    """Synchronous wrapper for scheduled execution"""
    return asyncio.run(run_enhanced_daily_report())


if __name__ == "__main__":
    success = asyncio.run(run_enhanced_daily_report())
    sys.exit(0 if success else 1)