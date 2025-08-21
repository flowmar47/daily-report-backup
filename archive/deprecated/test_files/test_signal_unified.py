#!/usr/bin/env python3
"""
Test Signal with unified messenger
"""

import asyncio
import logging
import sys
from pathlib import Path

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

from src.messengers.unified_messenger import UnifiedSignalMessenger
from utils.env_config import EnvironmentConfig

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def test_signal_unified():
    """Test Signal with unified messenger"""
    try:
        # Initialize environment config
        env_config = EnvironmentConfig()
        
        # Initialize Signal messenger
        signal = UnifiedSignalMessenger(env_config)
        
        # Send test message
        logger.info("Sending test message via unified Signal messenger...")
        result = await signal.send_message("🧪 Test message from unified Signal messenger system")
        
        if result.success:
            logger.info(f"✅ Message sent successfully: {result.message_id}")
        else:
            logger.error(f"❌ Failed to send message: {result.error}")
        
        # Cleanup
        await signal.cleanup()
        
        return result.success
        
    except Exception as e:
        logger.error(f"Error testing Signal: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(test_signal_unified())
    if success:
        print("✅ Signal unified messenger working!")
    else:
        print("❌ Signal unified messenger failed")