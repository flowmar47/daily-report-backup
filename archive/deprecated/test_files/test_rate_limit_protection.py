#!/usr/bin/env python3
"""
Test Rate Limit Protection
Verifies the system can generate signals at 6 AM without hitting API limits
"""

import asyncio
import time
from datetime import datetime
import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from dotenv import load_dotenv
load_dotenv()

async def test_rate_limits():
    """Test that we can generate signals without rate limit issues"""
    
    print("="*70)
    print("RATE LIMIT PROTECTION TEST")
    print("="*70)
    print("This test simulates 6 AM signal generation")
    print("Checking if rate limits are properly handled...")
    print("="*70)
    
    # Test 1: Pre-cache data
    print("\n1️⃣ Testing Pre-Cache (5:55 AM simulation)...")
    start = time.time()
    
    result = os.system("python pre_cache_signals.py > /dev/null 2>&1")
    
    if result == 0:
        print(f"✅ Pre-cache successful ({time.time()-start:.1f}s)")
    else:
        print("❌ Pre-cache failed")
        return False
    
    # Test 2: Wait for cache to be ready
    print("\n2️⃣ Waiting 5 seconds (simulating 5:55 to 6:00 AM)...")
    await asyncio.sleep(5)
    
    # Test 3: Generate signals using cached data
    print("\n3️⃣ Testing Signal Generation (6:00 AM simulation)...")
    start = time.time()
    
    from price_validator import get_validated_prices
    
    # This should use cached data and not hit rate limits
    pairs = ['EURUSD', 'GBPUSD', 'USDJPY']
    prices = await get_validated_prices(pairs)
    
    elapsed = time.time() - start
    
    if prices and len(prices) >= 2:
        print(f"✅ Got {len(prices)} prices in {elapsed:.1f}s (cached)")
        for pair, price in prices.items():
            print(f"   {pair}: {price}")
    else:
        print("❌ Failed to get prices")
        return False
    
    # Test 4: Verify no rate limits hit
    if elapsed < 2.0:  # Should be fast if using cache
        print("\n✅ RATE LIMIT PROTECTION WORKING!")
        print("   - Pre-cache at 5:55 AM loads data")
        print("   - 6:00 AM uses cached data")
        print("   - No API rate limits hit")
        return True
    else:
        print("\n⚠️  Slow response - may be hitting rate limits")
        return False

async def main():
    """Main test runner"""
    
    print(f"🕐 Current time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    success = await test_rate_limits()
    
    print("\n" + "="*70)
    if success:
        print("✅ RATE LIMIT TEST PASSED")
        print("System ready for 6 AM daily signal generation")
        print("No rate limit issues expected")
    else:
        print("❌ RATE LIMIT TEST FAILED")
        print("System may have issues at 6 AM")
    print("="*70)
    
    return success

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)