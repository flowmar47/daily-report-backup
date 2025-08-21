#!/usr/bin/env python3
"""Test sending the latest financial data to messengers"""

import asyncio
import json
import logging
from pathlib import Path
from src.messengers.unified_messenger import UnifiedMultiMessenger
from src.data_processors.template_generator import StructuredTemplateGenerator

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def main():
    """Test sending latest data"""
    try:
        # Load the latest real alerts
        data_file = Path('real_alerts_only/latest_real_alerts.json')
        if not data_file.exists():
            logger.error("No latest data file found")
            return
        
        with open(data_file, 'r') as f:
            financial_data = json.load(f)
        
        logger.info(f"Loaded data: {len(financial_data.get('forex_alerts', {}))} forex, {len(financial_data.get('options_data', []))} options")
        
        # Generate the structured message
        generator = StructuredTemplateGenerator()
        message = generator.generate_structured_message(financial_data)
        
        if not message or message == "No financial signals available today.":
            logger.warning("No structured message generated")
            return
        
        logger.info("Generated message:")
        print("-" * 60)
        print(message)
        print("-" * 60)
        
        # Send via unified messenger
        logger.info("Sending to Signal and Telegram...")
        multi_messenger = UnifiedMultiMessenger(['telegram', 'signal'])
        
        results = await multi_messenger.send_structured_financial_data(message)
        
        # Log results
        for platform, result in results.items():
            if result.success:
                logger.info(f"SUCCESS {platform}: Message sent (ID: {result.message_id})")
            else:
                logger.error(f"FAILED {platform}: {result.error}")
        
        await multi_messenger.cleanup()
        
    except Exception as e:
        logger.error(f"Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())