#!/usr/bin/env python3
"""
Test Telegram + Signal for Monday 6 AM PST scheduling
"""

import asyncio
import sys
from pathlib import Path
from datetime import datetime

# Add paths
sys.path.insert(0, str(Path(__file__).parent))

from src.messengers.unified_messenger import UnifiedMultiMessenger

async def test_telegram_signal():
    """Test Telegram and Signal for scheduled reports"""
    print("=" * 60)
    print("TELEGRAM + SIGNAL READINESS TEST")
    print("Ready for Monday 6 AM PST scheduling")
    print("=" * 60)
    
    # Initialize working platforms
    platforms = ['telegram', 'signal']
    multi_messenger = UnifiedMultiMessenger(platforms)
    
    # Test message
    test_message = f"""DAILY FINANCIAL REPORT TEST - {datetime.now().strftime('%Y-%m-%d %H:%M')}

FOREX PAIRS

Pair: EURUSD
High: 1.0925
Average: 1.0800
Low: 1.0675
MT4 Action: MT4 BUY
Exit: 1.0850

EQUITIES AND OPTIONS

Symbol: QQQ
52 Week High: 495.75
52 Week Low: 489.25
Strike Price:

CALL > 500.00

PUT < 485.00
Status: TRADE IN PROFIT

AUTOMATED WEEKDAY REPORTS CONFIRMED

The system is ready for automated daily financial reports at 6:00 AM PST on weekdays.

Current platforms configured:
- Telegram: Working
- Signal: Working
- WhatsApp: Integration in progress

Reports will be sent automatically starting Monday morning."""
    
    print("Sending test to working platforms...")
    
    try:
        # Send to working platforms
        results = await multi_messenger.send_to_all(test_message)
        
        print("\nRESULTS:")
        print("-" * 40)
        
        success_count = 0
        for platform, result in results.items():
            if result.success:
                print(f"SUCCESS: {platform.upper()} - Ready for Monday")
                success_count += 1
            else:
                print(f"FAILED: {platform.upper()} - {result.error}")
        
        print(f"\nWORKING PLATFORMS: {success_count}/{len(platforms)}")
        
        if success_count == len(platforms):
            print("\nSYSTEM READY FOR MONDAY 6 AM PST!")
            print("Automated reports will be sent to working platforms.")
        else:
            print(f"\nPARTIAL READINESS: {success_count} platform(s) working")
            
    except Exception as e:
        print(f"Test failed: {e}")
    
    finally:
        # Cleanup
        await multi_messenger.cleanup()
        print("\nReadiness test complete")

if __name__ == "__main__":
    asyncio.run(test_telegram_signal())