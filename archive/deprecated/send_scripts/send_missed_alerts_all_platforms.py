#!/usr/bin/env python3
"""
Send missed financial alerts to all platforms including WhatsApp
"""

import asyncio
import logging
import sys
from pathlib import Path

# Add src to path
sys.path.append(str(Path(__file__).parent / 'src'))

from src.messengers.unified_messenger import UnifiedMultiMessenger
from src.data_processors.template_generator import StructuredTemplateGenerator
import json

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def send_latest_alerts():
    """Send the latest financial alerts to all platforms"""
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
        
        # Send to all platforms
        multi_messenger = UnifiedMultiMessenger()
        results = await multi_messenger.send_structured_financial_data(structured_report)
        
        # Log results
        for platform, result in results.items():
            if result.success:
                logger.info(f"✅ {platform}: Message sent successfully")
            else:
                logger.error(f"❌ {platform}: Failed - {result.error}")
        
        # Send heatmaps if available
        heatmap_dir = Path(__file__).parent / 'heatmaps' / 'reports'
        latest_heatmap = None
        
        # Find latest heatmap directory
        if heatmap_dir.exists():
            heatmap_dirs = sorted([d for d in heatmap_dir.iterdir() if d.is_dir()], reverse=True)
            if heatmap_dirs:
                latest_heatmap = heatmap_dirs[0]
        
        if latest_heatmap:
            categorical = latest_heatmap / 'categorical_heatmap.png'
            forex_pairs = latest_heatmap / 'forex_pairs_heatmap.png'
            
            attachments = []
            if categorical.exists():
                from src.messengers.unified_messenger import AttachmentData
                attachments.append(AttachmentData(
                    file_path=categorical,
                    caption="Interest Rate Categorical Analysis",
                    filename="categorical_heatmap.png"
                ))
            
            if forex_pairs.exists():
                from src.messengers.unified_messenger import AttachmentData
                attachments.append(AttachmentData(
                    file_path=forex_pairs,
                    caption="Forex Pairs Differential Matrix",
                    filename="forex_pairs_heatmap.png"
                ))
            
            if attachments:
                logger.info(f"📊 Sending {len(attachments)} heatmap images...")
                attachment_results = await multi_messenger.send_attachments(attachments)
                
                for platform, results in attachment_results.items():
                    success_count = sum(1 for r in results if r.success)
                    logger.info(f"📊 {platform}: {success_count}/{len(results)} attachments sent")
        
        await multi_messenger.cleanup()
        
    except Exception as e:
        logger.error(f"Failed to send alerts: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(send_latest_alerts())