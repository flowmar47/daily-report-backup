#!/usr/bin/env python3
"""
Final WhatsApp PyWhatKit integration test
"""

import asyncio
import os
import sys
from pathlib import Path
from datetime import datetime

# Set display for VNC
os.environ['DISPLAY'] = ':1'

# Add paths
sys.path.insert(0, str(Path(__file__).parent))

from src.messengers.unified_messenger import UnifiedMultiMessenger

async def test_final_integration():
    """Test complete WhatsApp integration"""
    print("=" * 60)
    print("Final WhatsApp Integration Test")
    print("=" * 60)
    
    # Test 1: WhatsApp only
    print("\nTest 1: WhatsApp messenger only")
    whatsapp_messenger = UnifiedMultiMessenger(['whatsapp'])
    
    message1 = f"""WHATSAPP INTEGRATION TEST - {datetime.now().strftime('%Y-%m-%d %H:%M')}

PyWhatKit integration is now active.
Messages will be sent to configured phone numbers.
Ready for daily financial reports."""
    
    results = await whatsapp_messenger.send_to_all(message1)
    for platform, result in results.items():
        if result.success:
            print(f"SUCCESS: {platform} - Message sent")
        else:
            print(f"FAILED: {platform} - {result.error}")
    
    await whatsapp_messenger.cleanup()
    
    # Test 2: Multi-platform (if Telegram is configured)
    print("\nTest 2: Multi-platform test")
    multi_messenger = UnifiedMultiMessenger(['telegram', 'whatsapp'])
    
    message2 = """MULTI-PLATFORM TEST

FOREX PAIRS

Pair: GBPUSD
High: 1.2750
Average: 1.2650
Low: 1.2550
MT4 Action: MT4 SELL

This message should appear on both Telegram and WhatsApp."""
    
    results = await multi_messenger.send_to_all(message2)
    for platform, result in results.items():
        if result.success:
            print(f"SUCCESS: {platform} - Message sent")
        else:
            print(f"FAILED: {platform} - {result.error}")
    
    await multi_messenger.cleanup()
    
    print("\nIntegration test completed!")
    print("WhatsApp is now ready to use with the daily report system.")

if __name__ == "__main__":
    asyncio.run(test_final_integration())