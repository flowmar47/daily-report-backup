#!/usr/bin/env python3
"""
Enhanced Daily Scheduler - Production Version
Schedules both MyMama alerts and interest rate heatmaps
"""

import schedule
import time
import logging
from run_enhanced_daily_report import run_enhanced_daily_report_sync

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/enhanced_scheduler.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


def scheduled_enhanced_report():
    """Wrapper function for scheduled execution"""
    logger.info("⏰ Scheduled enhanced daily report starting...")
    try:
        success = run_enhanced_daily_report_sync()
        if success:
            logger.info("✅ Scheduled enhanced daily report completed successfully")
        else:
            logger.warning("⚠️ Scheduled enhanced daily report had issues")
    except Exception as e:
        logger.error(f"❌ Error in scheduled enhanced report: {e}")


def main():
    """Main scheduler entry point"""
    logger.info("📅 Enhanced Daily Scheduler starting...")
    
    # Schedule for weekdays at 6:00 AM PST
    schedule.every().monday.at("06:00").do(scheduled_enhanced_report)
    schedule.every().tuesday.at("06:00").do(scheduled_enhanced_report)
    schedule.every().wednesday.at("06:00").do(scheduled_enhanced_report)
    schedule.every().thursday.at("06:00").do(scheduled_enhanced_report)
    schedule.every().friday.at("06:00").do(scheduled_enhanced_report)
    
    logger.info("📋 Scheduled enhanced daily reports for weekdays at 06:00 PST")
    logger.info("🔄 Scheduler running - waiting for scheduled times...")
    
    # Keep the service running
    while True:
        try:
            schedule.run_pending()
            time.sleep(60)  # Check every minute
        except KeyboardInterrupt:
            logger.info("🛑 Scheduler stopped by user")
            break
        except Exception as e:
            logger.error(f"❌ Unexpected scheduler error: {e}")
            time.sleep(300)  # Wait 5 minutes before retrying


if __name__ == "__main__":
    main()