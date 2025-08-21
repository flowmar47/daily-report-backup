#!/usr/bin/env python3
"""
Test main system with enhanced browserbase scraper
"""
import asyncio
import logging
import sys
import os
from datetime import datetime

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def test_main_system():
    """Test the main system with enhanced scraper"""
    try:
        logger.info("🧪 Testing Main System with Enhanced BrowserBase Scraper...")
        
        from main import DailyReportAutomation
        
        # Initialize the main automation system
        automation = DailyReportAutomation()
        logger.info("✅ Successfully initialized DailyReportAutomation")
        
        # Test market data collection
        logger.info("📊 Testing market data collection...")
        market_data = await automation.collect_market_data()
        
        if market_data and market_data.get('has_real_data'):
            logger.info(f"✅ Market data collection successful!")
            
            # Count different types of data
            forex_count = len(market_data.get('forex_alerts', []))
            options_count = len(market_data.get('options_alerts', []))
            swing_count = len(market_data.get('swing_trades', []))
            day_count = len(market_data.get('day_trades', []))
            processed_count = len(market_data.get('processed_forecasts', []))
            
            logger.info(f"📈 Data counts:")
            logger.info(f"   Forex: {forex_count}")
            logger.info(f"   Options: {options_count}")
            logger.info(f"   Swing: {swing_count}")
            logger.info(f"   Day: {day_count}")
            logger.info(f"   Processed: {processed_count}")
            
            # Test report generation
            logger.info("📝 Testing report generation...")
            report = await automation.generate_report(market_data)
            
            if report:
                logger.info(f"✅ Report generation successful!")
                logger.info(f"📄 Report length: {len(report)} characters")
                
                # Show first few lines of report
                lines = report.split('\n')[:5]
                logger.info("📋 Report preview:")
                for line in lines:
                    logger.info(f"   {line}")
                
                return True
            else:
                logger.warning("⚠️ No report generated")
                return False
        else:
            logger.warning("⚠️ No market data collected")
            return False
            
    except Exception as e:
        logger.error(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(test_main_system())
    if success:
        print("✅ Main system test completed successfully!")
    else:
        print("❌ Main system test failed!")
        sys.exit(1)