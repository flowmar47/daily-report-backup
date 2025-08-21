#!/usr/bin/env python3
"""
Send heatmaps to Signal using direct HTTP API
"""

import asyncio
import os
import sys
import logging
import aiohttp
import json

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def send_to_signal_api(file_path: str, message: str):
    """Send file to Signal using HTTP API"""
    api_url = "http://localhost:8080"
    phone_number = os.getenv('SIGNAL_PHONE_NUMBER', '+16572463906')
    group_id = os.getenv('SIGNAL_GROUP_ID', 'group.cUY1YUE5SHRRMW0wQy9SVGMrSWNvVTQrakluaU00YXlBeVBscUdLUFdMTT0=')
    
    logger.info(f"📱 Using Signal phone: {phone_number}")
    logger.info(f"👥 Using Signal group: {group_id}")
    
    try:
        async with aiohttp.ClientSession() as session:
            # Prepare the multipart form data
            data = aiohttp.FormData()
            data.add_field('number', phone_number)
            data.add_field('recipients[]', group_id)
            data.add_field('message', message)
            
            # Add the attachment
            with open(file_path, 'rb') as f:
                data.add_field('attachment', f, filename=os.path.basename(file_path))
                
                # Send the request
                async with session.post(f"{api_url}/v2/send", data=data, timeout=30) as response:
                    if response.status == 201:
                        logger.info(f"✅ File sent successfully: {os.path.basename(file_path)}")
                        return True
                    else:
                        response_text = await response.text()
                        logger.error(f"❌ Signal API error {response.status}: {response_text}")
                        return False
                        
    except Exception as e:
        logger.error(f"❌ Error sending to Signal: {e}")
        return False


async def send_heatmaps_signal_direct():
    """Send heatmaps directly to Signal via HTTP API"""
    logger.info("📤 Sending heatmaps to Signal via direct HTTP API...")
    
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
        logger.error("❌ No heatmap files found")
        return False
    
    # Use the latest files
    categorical_path = max(categorical_files, key=os.path.getmtime)
    forex_path = max(forex_files, key=os.path.getmtime)
    
    logger.info(f"📊 Found categorical heatmap: {categorical_path}")
    logger.info(f"💱 Found forex heatmap: {forex_path}")
    
    success_count = 0
    
    # Send categorical heatmap
    logger.info("📤 Sending categorical heatmap...")
    success = await send_to_signal_api(
        categorical_path,
        "📊 Global Interest Rates - Categorical Analysis"
    )
    if success:
        success_count += 1
    
    # Wait a moment between sends
    await asyncio.sleep(2)
    
    # Send forex heatmap
    logger.info("📤 Sending forex heatmap...")
    success = await send_to_signal_api(
        forex_path,
        "🌍 Forex Pairs Differential Matrix"
    )
    if success:
        success_count += 1
    
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
    success = asyncio.run(send_heatmaps_signal_direct())
    sys.exit(0 if success else 1)