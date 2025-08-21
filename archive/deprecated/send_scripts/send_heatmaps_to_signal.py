#!/usr/bin/env python3
"""
Send today's heatmaps to Signal only
"""

import asyncio
import os
import sys
import logging

# Add src directory to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from messenger_compatibility import SignalMessenger

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def send_heatmaps_to_signal():
    """Send today's heatmaps to Signal group"""
    logger.info("📤 Sending today's heatmaps to Signal...")
    
    # Setup Signal messenger
    signal_config = {
        'phone_number': os.getenv('SIGNAL_PHONE_NUMBER'),
        'group_id': os.getenv('SIGNAL_GROUP_ID'),
        'api_url': 'http://localhost:8080',
        'signal_cli_path': 'signal-cli',
        'enabled': True
    }
    signal = SignalMessenger(signal_config)
    
    # Test connection
    logger.info("🔗 Testing Signal connection...")
    connection_test = await signal.test_connection()
    if not connection_test:
        logger.error("❌ Signal not available")
        return False
    
    logger.info("✅ Signal connection successful")
    
    # Find latest heatmap files
    heatmap_dir = os.path.join(os.path.dirname(__file__), 'heatmaps', 'reports')
    
    # Find the latest categorical and forex heatmaps
    categorical_files = []
    forex_files = []
    
    for root, dirs, files in os.walk(heatmap_dir):
        for file in files:
            if 'categorical_heatmap' in file and file.endswith('.png'):
                categorical_files.append(os.path.join(root, file))
            elif 'forex_pairs' in file and file.endswith('.png'):
                forex_files.append(os.path.join(root, file))
    
    if not categorical_files or not forex_files:
        logger.error("❌ No heatmap files found. Generate them first with: python daily_heatmap_sender.py")
        return False
    
    # Use the latest files
    categorical_path = max(categorical_files, key=os.path.getmtime)
    forex_path = max(forex_files, key=os.path.getmtime)
    
    logger.info(f"📊 Found categorical heatmap: {categorical_path}")
    logger.info(f"💱 Found forex heatmap: {forex_path}")
    
    success_count = 0
    
    # Send categorical heatmap
    logger.info("📤 Sending categorical heatmap to Signal...")
    try:
        result = await signal.send_attachment(
            categorical_path,
            "📊 Global Interest Rates - Categorical Analysis"
        )
        
        if result.status.value in ['success']:
            logger.info("✅ Categorical heatmap sent to Signal successfully")
            success_count += 1
        else:
            logger.warning(f"⚠️ Categorical heatmap failed: {result.error}")
            
    except Exception as e:
        logger.error(f"❌ Error sending categorical heatmap: {e}")
    
    # Send forex heatmap  
    logger.info("📤 Sending forex heatmap to Signal...")
    try:
        result = await signal.send_attachment(
            forex_path,
            "🌍 Forex Pairs Differential Matrix"
        )
        
        if result.status.value in ['success']:
            logger.info("✅ Forex heatmap sent to Signal successfully")
            success_count += 1
        else:
            logger.warning(f"⚠️ Forex heatmap failed: {result.error}")
            
    except Exception as e:
        logger.error(f"❌ Error sending forex heatmap: {e}")
    
    if success_count == 2:
        logger.info("🎉 Both heatmaps sent to Signal successfully!")
        return True
    elif success_count == 1:
        logger.warning("⚠️ Only one heatmap sent successfully")
        return True
    else:
        logger.error("❌ Failed to send heatmaps to Signal")
        return False


if __name__ == "__main__":
    success = asyncio.run(send_heatmaps_to_signal())
    sys.exit(0 if success else 1)