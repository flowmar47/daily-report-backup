#!/usr/bin/env python3
"""
Debug test for unified messenger to identify Signal issues
"""

import asyncio
import logging
import sys
from pathlib import Path

# Add paths for imports
sys.path.append(str(Path(__file__).parent / 'src'))
sys.path.append(str(Path(__file__).parent / 'src' / 'messengers'))

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def test_unified_messenger():
    """Test unified messenger with detailed debugging"""
    
    try:
        # Import after path setup
        from messengers.unified_messenger import UnifiedMultiMessenger, UnifiedSignalMessenger, UnifiedTelegramMessenger
        from utils.env_config import EnvironmentConfig
        
        logger.info("Starting unified messenger debug test...")
        
        # Test 1: Initialize individual messengers
        logger.info("\n=== Test 1: Initialize individual messengers ===")
        env_config = EnvironmentConfig('daily_report')
        
        # Test Telegram messenger
        logger.info("\nTesting Telegram messenger...")
        try:
            telegram_messenger = UnifiedTelegramMessenger(env_config)
            telegram_result = await telegram_messenger.send_message("Test from unified messenger debug - Telegram")
            logger.info(f"Telegram result: {telegram_result}")
        except Exception as e:
            logger.error(f"Telegram error: {e}", exc_info=True)
        
        # Test Signal messenger
        logger.info("\nTesting Signal messenger...")
        try:
            signal_messenger = UnifiedSignalMessenger(env_config)
            signal_result = await signal_messenger.send_message("Test from unified messenger debug - Signal")
            logger.info(f"Signal result: {signal_result}")
        except Exception as e:
            logger.error(f"Signal error: {e}", exc_info=True)
        
        # Test 2: Test multi-messenger
        logger.info("\n=== Test 2: Test MultiMessenger ===")
        try:
            multi_messenger = UnifiedMultiMessenger(['telegram', 'signal'])
            results = await multi_messenger.send_to_all("Test from unified multi-messenger")
            
            for platform, result in results.items():
                logger.info(f"{platform}: {result}")
                
            await multi_messenger.cleanup()
        except Exception as e:
            logger.error(f"Multi-messenger error: {e}", exc_info=True)
        
        # Test 3: Test structured financial data
        logger.info("\n=== Test 3: Test structured financial data ===")
        test_data = """FOREX PAIRS

Pair: EURUSD
High: 1.1158
Average: 1.0742
Low: 1.0238
MT4 Action: MT4 SELL
Exit: 1.0850"""
        
        try:
            multi_messenger = UnifiedMultiMessenger(['telegram', 'signal'])
            results = await multi_messenger.send_structured_financial_data(test_data)
            
            for platform, result in results.items():
                logger.info(f"{platform} structured data result: {result}")
                
            await multi_messenger.cleanup()
        except Exception as e:
            logger.error(f"Structured data error: {e}", exc_info=True)
            
    except Exception as e:
        logger.error(f"Test failed: {e}", exc_info=True)

if __name__ == "__main__":
    asyncio.run(test_unified_messenger())