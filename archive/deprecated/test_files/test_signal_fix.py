#!/usr/bin/env python3
"""
Test Signal messenger fix for pending membership issue
"""

import asyncio
import os
import sys
from pathlib import Path
from datetime import datetime

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

# Import the unified messenger
from src.messengers.unified_messenger import UnifiedSignalMessenger
from utils.env_config import EnvironmentConfig

async def test_signal_delivery():
    """Test Signal message delivery after fix"""
    print("=" * 60)
    print("TESTING SIGNAL MESSAGE DELIVERY FIX")
    print("=" * 60)
    
    try:
        # Initialize environment config
        env_config = EnvironmentConfig('daily_report')
        
        # Create Signal messenger
        print("\n1. Initializing Signal messenger...")
        signal_messenger = UnifiedSignalMessenger(env_config)
        await signal_messenger._initialize_client()
        
        # Test message
        test_message = f"""TEST MESSAGE - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

This is a test message to verify Signal delivery fix.

If you receive this message, the pending membership issue has been resolved.

The message is being sent from: +16572463906
To group: Ohms Alerts Reports

Please confirm receipt of this message."""
        
        print("\n2. Sending test message to Signal group...")
        print(f"   From: {signal_messenger.config['phone_number']}")
        print(f"   To: {signal_messenger.config['group_id']}")
        
        # Send the message
        result = await signal_messenger.send_message(test_message)
        
        # Check result
        if result.success:
            print("\n[SUCCESS] Message sent successfully!")
            print(f"   Message ID: {result.message_id}")
            print(f"   Timestamp: {result.timestamp}")
            if result.metadata:
                print(f"   Metadata: {result.metadata}")
        else:
            print("\n[FAILED] Message delivery failed!")
            print(f"   Error: {result.error}")
            print(f"   Status: {result.status}")
        
        # Clean up
        await signal_messenger.cleanup()
        
        print("\n" + "=" * 60)
        print("TEST COMPLETE")
        print("=" * 60)
        
        return result.success
        
    except Exception as e:
        print(f"\n[ERROR] Test failed with exception: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(test_signal_delivery())
    sys.exit(0 if success else 1)