#!/usr/bin/env python3
"""
Simple script to send alerts to Telegram and Signal only
"""

import asyncio
import logging
import sys
import json
from pathlib import Path

# Add src to path
sys.path.append(str(Path(__file__).parent / 'src'))

from src.messengers.unified_messenger import UnifiedTelegramMessenger, UnifiedSignalMessenger, MessageStatus
from src.data_processors.template_generator import StructuredTemplateGenerator
from utils.env_config import EnvironmentConfig

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def send_alerts_simple():
    """Send alerts to Telegram and Signal"""
    try:
        # Load latest real alerts
        alerts_file = Path(__file__).parent / 'real_alerts_only' / 'latest_real_alerts.json'
        
        if not alerts_file.exists():
            logger.error("No latest alerts file found")
            return
        
        with open(alerts_file, 'r') as f:
            alerts_data = json.load(f)
        
        # Generate structured report
        template_gen = StructuredTemplateGenerator()
        structured_report = template_gen.generate_structured_message(alerts_data)
        
        # Initialize messengers directly
        env_config = EnvironmentConfig('daily_report')
        messengers = {}
        
        try:
            messengers['telegram'] = UnifiedTelegramMessenger(env_config)
            logger.info("✅ Telegram messenger initialized")
        except Exception as e:
            logger.error(f"Failed to initialize Telegram: {e}")
        
        try:
            messengers['signal'] = UnifiedSignalMessenger(env_config)
            logger.info("✅ Signal messenger initialized")
        except Exception as e:
            logger.error(f"Failed to initialize Signal: {e}")
        
        # Send to each messenger
        for platform, messenger in messengers.items():
            try:
                result = await messenger.send_structured_financial_data(structured_report)
                if result.success:
                    logger.info(f"✅ {platform}: Message sent successfully")
                else:
                    logger.error(f"❌ {platform}: Failed - {result.error}")
            except Exception as e:
                logger.error(f"❌ {platform}: Exception - {e}")
        
        # Cleanup
        for messenger in messengers.values():
            await messenger.cleanup()
        
        # Send heatmaps
        heatmap_dir = Path(__file__).parent / 'heatmaps' / 'reports'
        latest_heatmap = None
        
        if heatmap_dir.exists():
            heatmap_dirs = sorted([d for d in heatmap_dir.iterdir() if d.is_dir()], reverse=True)
            if heatmap_dirs:
                latest_heatmap = heatmap_dirs[0]
                logger.info(f"📊 Found latest heatmap: {latest_heatmap.name}")
        
        if latest_heatmap:
            categorical = latest_heatmap / 'categorical_heatmap.png'
            forex_pairs = latest_heatmap / 'forex_pairs_heatmap.png'
            
            from src.messengers.unified_messenger import AttachmentData
            
            for messenger_name, messenger in messengers.items():
                try:
                    if categorical.exists():
                        attachment = AttachmentData(
                            file_path=categorical,
                            caption="Interest Rate Categorical Analysis",
                            filename="categorical_heatmap.png"
                        )
                        result = await messenger.send_attachment(attachment)
                        if result.success:
                            logger.info(f"✅ {messenger_name}: Categorical heatmap sent")
                        else:
                            logger.error(f"❌ {messenger_name}: Failed to send categorical heatmap - {result.error}")
                    
                    if forex_pairs.exists():
                        attachment = AttachmentData(
                            file_path=forex_pairs,
                            caption="Forex Pairs Differential Matrix",
                            filename="forex_pairs_heatmap.png"
                        )
                        result = await messenger.send_attachment(attachment)
                        if result.success:
                            logger.info(f"✅ {messenger_name}: Forex pairs heatmap sent")
                        else:
                            logger.error(f"❌ {messenger_name}: Failed to send forex heatmap - {result.error}")
                            
                except Exception as e:
                    logger.error(f"❌ {messenger_name}: Failed to send heatmaps - {e}")
        
    except Exception as e:
        logger.error(f"Failed to send alerts: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(send_alerts_simple())