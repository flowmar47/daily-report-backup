#!/usr/bin/env python3
"""
Send fresh financial data and heatmaps to Telegram only
"""

import asyncio
import logging
from pathlib import Path
import sys
import os

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

from src.messengers.unified_messenger import UnifiedTelegramMessenger
from utils.env_config import EnvironmentConfig

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def send_to_telegram():
    """Send fresh financial data and heatmaps to Telegram only"""
    try:
        # Initialize environment config
        env_config = EnvironmentConfig()
        
        # Initialize Telegram messenger
        telegram = UnifiedTelegramMessenger(env_config)
        
        # Read the fresh financial data
        with open("fresh_financial_data.txt", "r", encoding='utf-8') as f:
            financial_data = f.read()
        
        # Send financial data
        logger.info("Sending fresh financial data to Telegram...")
        result = await telegram.send_structured_financial_data(financial_data)
        
        if result.success:
            logger.info("✅ Financial data sent successfully")
        else:
            logger.error(f"❌ Failed to send financial data: {result.error}")
        
        # Send heatmaps (use the latest Bloomberg-style heatmaps)
        import glob
        categorical_files = sorted(glob.glob("categorical_heatmap_20250703*.png"), reverse=True)
        forex_files = sorted(glob.glob("forex_pairs_20250703*.png"), reverse=True)
        
        heatmap_files = []
        if categorical_files:
            heatmap_files.append(categorical_files[0])  # Latest categorical
        if forex_files:
            heatmap_files.append(forex_files[0])  # Latest forex
        
        for heatmap_file in heatmap_files:
            if Path(heatmap_file).exists():
                logger.info(f"Sending heatmap: {heatmap_file}")
                from src.messengers.unified_messenger import AttachmentData
                
                attachment = AttachmentData(
                    file_path=Path(heatmap_file),
                    caption=f"📊 Fresh {heatmap_file.replace('_', ' ').replace('.png', '').title()}"
                )
                
                heatmap_result = await telegram.send_attachment(attachment)
                
                if heatmap_result.success:
                    logger.info(f"✅ Heatmap {heatmap_file} sent successfully")
                else:
                    logger.error(f"❌ Failed to send heatmap {heatmap_file}: {heatmap_result.error}")
        
        # Cleanup
        await telegram.cleanup()
        
        print("All data sent to Telegram successfully!")
        
    except Exception as e:
        logger.error(f"Error sending to Telegram: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(send_to_telegram())