#!/usr/bin/env python3
"""
Test script for enhanced browserbase scraper
"""
import asyncio
import logging
import sys
import os

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def test_enhanced_scraper():
    """Test the enhanced scraper with error handling"""
    try:
        logger.info("🧪 Testing Enhanced BrowserBase Scraper...")
        
        from enhanced_browserbase_scraper import EnhancedBrowserBaseScraper
        
        logger.info("✅ Successfully imported EnhancedBrowserBaseScraper")
        
        # Initialize scraper
        scraper = EnhancedBrowserBaseScraper()
        logger.info("✅ Successfully initialized scraper")
        
        # Test scraping
        result = await scraper.scrape_data()
        
        if result.get('success'):
            logger.info(f"✅ Scraping successful!")
            if 'validation' in result:
                logger.info(f"📊 Data validation: {result['validation']}")
            if 'duration' in result:
                logger.info(f"⏱️ Duration: {result['duration']:.2f}s")
            if 'output_file' in result:
                logger.info(f"📁 Output file: {result['output_file']}")
            
            # Log data summary
            data = result.get('data', {})
            logger.info(f"📈 Data summary:")
            logger.info(f"   Forex alerts: {len(data.get('forex_alerts', []))}")
            logger.info(f"   Options alerts: {len(data.get('options_alerts', []))}")
            logger.info(f"   Swing trades: {len(data.get('swing_trades', []))}")
            logger.info(f"   Day trades: {len(data.get('day_trades', []))}")
            logger.info(f"   Processed forecasts: {len(data.get('processed_forecasts', []))}")
            logger.info(f"   Has real data: {data.get('has_real_data', False)}")
            
            return True
        else:
            logger.error(f"❌ Scraping failed: {result.get('error')}")
            return False
            
    except Exception as e:
        logger.error(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(test_enhanced_scraper())
    if success:
        print("✅ Enhanced scraper test completed successfully!")
    else:
        print("❌ Enhanced scraper test failed!")
        sys.exit(1)