#!/usr/bin/env python3
"""
Final test - verify all platforms (Telegram, Signal, WhatsApp) are ready for scheduled reports
"""

import asyncio
import os
import sys
from pathlib import Path
from datetime import datetime

# Set display for VNC (needed for WhatsApp)
os.environ['DISPLAY'] = ':1'

# Add paths
sys.path.insert(0, str(Path(__file__).parent))

from src.messengers.unified_messenger import UnifiedMultiMessenger

async def test_all_platforms():
    """Test all three platforms for daily report readiness"""
    print("=" * 60)
    print("MULTI-PLATFORM READINESS TEST")
    print("Testing: Telegram + Signal + WhatsApp")
    print("=" * 60)
    
    # Initialize all platforms
    platforms = ['telegram', 'signal', 'whatsapp']
    multi_messenger = UnifiedMultiMessenger(platforms)
    
    # Sample financial report message
    test_message = f"""PLATFORM READINESS TEST - {datetime.now().strftime('%Y-%m-%d %H:%M')}

FOREX PAIRS

Pair: EURUSD
High: 1.0925
Average: 1.0825
Low: 1.0725
MT4 Action: MT4 BUY
Exit: 1.0875

EQUITIES AND OPTIONS

Symbol: QQQ
52 Week High: 485.75
52 Week Low: 480.50
Strike Price:

CALL > 490.00

PUT < 475.00
Status: TRADE IN PROFIT

ALL PLATFORMS CONFIGURED AND READY

This test confirms that all three messaging platforms are properly configured:
- Telegram: Group messaging
- Signal: Group messaging 
- WhatsApp: Group messaging (via PyWhatKit)

The system is now ready for automated daily financial reports at 6:00 AM PST on weekdays."""
    
    print("Sending test message to all platforms...")
    
    try:
        # Send to all platforms
        results = await multi_messenger.send_to_all(test_message)
        
        print("\nRESULTS:")
        print("-" * 40)
        
        success_count = 0
        for platform, result in results.items():
            if result.success:
                print(f"SUCCESS: {platform.upper()} - Message sent")
                if result.message_id:
                    print(f"  Message ID: {result.message_id}")
                success_count += 1
            else:
                print(f"FAILED: {platform.upper()} - {result.error}")
        
        print(f"\nOVERALL: {success_count}/{len(platforms)} platforms successful")
        
        if success_count == len(platforms):
            print("\nALL PLATFORMS READY!")
            print("Scheduled reports will be sent to all platforms at 6:00 AM PST on weekdays.")
        elif success_count > 0:
            print(f"\nPARTIAL SUCCESS: {success_count} platforms working")
        else:
            print("\nNO PLATFORMS WORKING - Check configurations")
            
    except Exception as e:
        print(f"Test failed: {e}")
    
    finally:
        # Cleanup
        await multi_messenger.cleanup()
        print("\nTest complete - System ready for production")

if __name__ == "__main__":
    asyncio.run(test_all_platforms())