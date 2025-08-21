#!/usr/bin/env python3
"""
Pre-cache data for 6 AM signal generation
Runs at 5:55 AM to warm up caches and avoid rate limits
"""

import asyncio
import logging
import sys
import os
from datetime import datetime, timedelta
import time

# Setup paths
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))
sys.path.append(os.path.join(os.path.dirname(__file__), 'Signals/src'))

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment
from dotenv import load_dotenv
load_dotenv()

# Import components
from price_validator import get_validated_prices
from api_cache import api_cache

# Change to Signals directory for imports
os.chdir(os.path.join(os.path.dirname(__file__), 'Signals'))
sys.path.insert(0, 'src')

from src.data_fetcher import DataFetcher
from src.technical_analysis import TechnicalAnalyzer

# Change back
os.chdir(os.path.dirname(__file__))

async def pre_cache_forex_data():
    """Pre-cache forex data to avoid rate limits at 6 AM"""
    
    logger.info("=" * 70)
    logger.info("PRE-CACHING FOREX DATA FOR 6 AM SIGNAL GENERATION")
    logger.info("=" * 70)
    
    # Currency pairs to pre-cache
    pairs = ['EURUSD', 'GBPUSD', 'USDJPY', 'CHFJPY', 'USDCAD', 'USDCHF', 
             'EURJPY', 'GBPJPY', 'EURGBP', 'AUDUSD', 'NZDUSD']
    
    # Clear expired cache first
    logger.info("🗑️  Clearing expired cache...")
    api_cache.clear_expired()
    
    # Step 1: Cache validated prices
    logger.info("\n📊 Step 1: Pre-caching validated prices...")
    validated_prices = await get_validated_prices(pairs)
    logger.info(f"✅ Cached {len(validated_prices)} validated prices")
    
    # Step 2: Cache technical data with delays
    logger.info("\n📈 Step 2: Pre-caching technical analysis data...")
    data_fetcher = DataFetcher()
    technical_analyzer = TechnicalAnalyzer()
    
    for i, pair in enumerate(validated_prices.keys()):
        logger.info(f"Caching {pair} technical data...")
        
        # Add delays between pairs to avoid rate limits
        if i > 0:
            delay = 5  # 5 seconds between pairs
            logger.info(f"⏳ Waiting {delay}s to avoid rate limits...")
            time.sleep(delay)
        
        try:
            # Cache different timeframes
            for interval in ['15min', '30min', '1hour', '4hour', 'daily']:
                cache_key = f"twelve_data_{pair}_{interval}"
                
                # Check if already cached
                if api_cache.get(cache_key, 'forex_data'):
                    logger.info(f"  ✅ {interval} already cached")
                    continue
                
                # Fetch and cache
                try:
                    # Use data_fetcher's method directly
                    if hasattr(data_fetcher, 'fetch_candlestick_data'):
                        data = data_fetcher.fetch_candlestick_data(pair, interval)
                        if data:
                            api_cache.set(cache_key, data, 'forex_data')
                            logger.info(f"  💾 Cached {interval} data")
                            time.sleep(1)  # Small delay between timeframes
                except Exception as e:
                    logger.warning(f"  ⚠️  Could not cache {interval}: {e}")
                    
        except Exception as e:
            logger.error(f"❌ Error caching {pair}: {e}")
            continue
    
    # Step 3: Cache economic data (24h TTL, so likely already cached)
    logger.info("\n💰 Step 3: Checking economic data cache...")
    economic_cache_keys = ['fred_interest_rates', 'ecb_rates', 'gdp_data']
    for key in economic_cache_keys:
        if api_cache.get(key, 'economic'):
            logger.info(f"  ✅ {key} already cached (24h TTL)")
        else:
            logger.info(f"  ⚠️  {key} needs refresh")
    
    logger.info("\n" + "=" * 70)
    logger.info("✅ PRE-CACHING COMPLETE")
    logger.info(f"⏰ Ready for 6 AM signal generation")
    logger.info("💡 Rate limits should be avoided with cached data")
    logger.info("=" * 70)
    
    return True

async def main():
    """Main entry point"""
    
    start_time = datetime.now()
    
    try:
        success = await pre_cache_forex_data()
        
        elapsed = (datetime.now() - start_time).total_seconds()
        logger.info(f"\n⏱️  Pre-caching completed in {elapsed:.1f} seconds")
        
        if success:
            logger.info("✅ System ready for 6 AM signal generation")
            return True
        else:
            logger.error("❌ Pre-caching failed")
            return False
            
    except Exception as e:
        logger.error(f"❌ Pre-cache error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)