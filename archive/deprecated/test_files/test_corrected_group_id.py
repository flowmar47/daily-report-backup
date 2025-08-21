#!/usr/bin/env python3
"""
Test the corrected WhatsApp group ID with ?mode=ac_c parameter
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

from src.messengers.whatsapp_pywhatkit_messenger import WhatsAppPyWhatKitMessenger
from utils.env_config import EnvironmentConfig

async def test_corrected_group_id():
    """Test WhatsApp with corrected group ID"""
    print("=" * 60)
    print("Testing Corrected WhatsApp Group ID")
    print("=" * 60)
    
    # Initialize environment config
    env_config = EnvironmentConfig('daily_report')
    
    # Initialize WhatsApp messenger
    whatsapp = WhatsAppPyWhatKitMessenger(env_config)
    
    try:
        # Initialize client
        await whatsapp._initialize_client()
        
        # Check what group ID is being used
        group_ids = whatsapp.config.get('group_ids', [])
        print(f"Group ID configured: {group_ids}")
        
        # Test message
        test_message = f"""GROUP ID CORRECTION TEST - {datetime.now().strftime('%Y-%m-%d %H:%M')}

Testing WhatsApp group messaging with corrected group ID:
LT4OVYECfxj5vwvoYGXDRn?mode=ac_c

This confirms the group ID parameter is working correctly.

Ready for scheduled daily financial reports!"""
        
        print("Sending test message with corrected group ID...")
        
        # Send test message
        result = await whatsapp.send_message(test_message)
        
        if result.success:
            print("SUCCESS: Message sent with corrected group ID!")
            print(f"Message ID: {result.message_id}")
            if result.metadata:
                print(f"Metadata: {result.metadata}")
        else:
            print(f"FAILED: {result.error}")
            
    except Exception as e:
        print(f"Test failed with error: {e}")
        
    finally:
        # Cleanup
        await whatsapp.cleanup()
        print("Test completed")

if __name__ == "__main__":
    asyncio.run(test_corrected_group_id())