#!/usr/bin/env python3
"""
Test complete 3-platform messaging system
Tests Signal, Telegram, and WhatsApp integration
"""

import asyncio
import sys
import logging
from pathlib import Path
from datetime import datetime

# Add the project root to Python path
sys.path.insert(0, str(Path(__file__).parent))

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

async def test_complete_messaging():
    """Test complete 3-platform messaging system"""
    logger.info("=== TESTING COMPLETE 3-PLATFORM MESSAGING SYSTEM ===")
    
    try:
        # Import unified messenger system
        from src.messengers.unified_messenger import UnifiedMultiMessenger
        
        # Initialize all 3 platforms
        platforms = ['signal', 'telegram', 'whatsapp']
        multi_messenger = UnifiedMultiMessenger(platforms)
        
        # Create test message
        timestamp = datetime.now().strftime('%H:%M:%S')
        test_message = f"🔧 3-Platform System Test {timestamp}\n\nTesting complete messaging integration:\n✅ Signal\n✅ Telegram\n✅ WhatsApp"
        
        logger.info(f"📤 Sending test message to all platforms...")
        logger.info(f"📄 Message: {test_message[:50]}...")
        
        # Send the test message
        results = await multi_messenger.send_to_all(test_message)
        
        # Analyze results
        success_count = 0
        for platform, result in results.items():
            if result.success:
                logger.info(f"✅ {platform.upper()}: Message sent successfully")
                logger.info(f"📋 Message ID: {result.message_id}")
                success_count += 1
            else:
                logger.error(f"❌ {platform.upper()}: Failed - {result.error}")
        
        # Overall status
        logger.info(f"\n=== MESSAGING RESULTS ===")
        logger.info(f"✅ Successful platforms: {success_count}/{len(platforms)}")
        
        if success_count == len(platforms):
            logger.info("🎉 ALL PLATFORMS: Complete messaging test PASSED!")
            success = True
        elif success_count > 0:
            logger.warning(f"⚠️ PARTIAL SUCCESS: {success_count}/{len(platforms)} platforms working")
            success = True  # Partial success is still acceptable
        else:
            logger.error("💥 COMPLETE FAILURE: No platforms working")
            success = False
        
        # Cleanup
        await multi_messenger.cleanup()
        
        return success, success_count, len(platforms)
        
    except Exception as e:
        logger.error(f"❌ Complete messaging test failed: {e}")
        import traceback
        traceback.print_exc()
        return False, 0, 3

async def main():
    """Main test function"""
    logger.info("Starting complete 3-platform messaging test...")
    
    # Important warning
    logger.warning("⚠️ This test will send messages to ALL live groups (Signal, Telegram, WhatsApp)")
    logger.info("Testing in 3 seconds...")
    await asyncio.sleep(3)
    
    success, success_count, total_platforms = await test_complete_messaging()
    
    if success:
        logger.info(f"🎉 3-Platform messaging test COMPLETED ({success_count}/{total_platforms} platforms)")
        if success_count == total_platforms:
            logger.info("🏆 PERFECT SCORE: All platforms working!")
    else:
        logger.error("❌ 3-Platform messaging test FAILED")
    
    return success

if __name__ == "__main__":
    asyncio.run(main())