#!/usr/bin/env python3
"""Test the scraper's ability to extract swing and day trades"""

import asyncio
import logging
from real_only_mymama_scraper import RealOnlyMyMamaScraper

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def main():
    """Test scraper extraction"""
    try:
        logger.info("Testing scraper extraction...")
        
        scraper = RealOnlyMyMamaScraper()
        result = await scraper.get_real_alerts_only()
        
        if result.get('has_real_data'):
            logger.info(f"Extraction results:")
            logger.info(f"- Forex: {len(result.get('forex_alerts', {}))}")
            logger.info(f"- Options: {len(result.get('options_data', []))}")
            logger.info(f"- Swing Trades: {len(result.get('swing_trades', []))}")
            logger.info(f"- Day Trades: {len(result.get('day_trades', []))}")
            logger.info(f"- Earnings: {len(result.get('earnings_releases', []))}")
            
            # Show swing trades
            swing_trades = result.get('swing_trades', [])
            if swing_trades:
                print("\nSWING TRADES FOUND:")
                for trade in swing_trades:
                    print(f"  - {trade['ticker']} - {trade['company']}")
                    print(f"    Earnings: {trade.get('earnings_date', 'N/A')}")
                    print(f"    Analysis: {trade.get('analysis', 'N/A')[:100]}...")
            else:
                print("\nNO SWING TRADES FOUND")
            
            # Show day trades
            day_trades = result.get('day_trades', [])
            if day_trades:
                print("\nDAY TRADES FOUND:")
                for trade in day_trades:
                    print(f"  - {trade['ticker']} - {trade['company']}")
                    print(f"    Why: {trade.get('why_day_trade', 'N/A')[:100]}...")
            else:
                print("\nNO DAY TRADES FOUND")
        else:
            logger.error("No data extracted")
            
    except Exception as e:
        logger.error(f"Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())