#!/usr/bin/env python3
"""
Send heatmaps to Signal using correct API format
"""

import asyncio
import os
import sys
import logging
import requests

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def send_to_signal_attachment(file_path: str, message: str):
    """Send file to Signal using requests (sync)"""
    api_url = "http://localhost:8080"
    phone_number = '+16572463906'
    group_id = 'group.cUY1YUE5SHRRMW0wQy9SVGMrSWNvVTQrakluaU00YXlBeVBscUdLUFdMTT0='
    
    try:
        # Prepare the multipart form data
        files = {
            'attachment': (os.path.basename(file_path), open(file_path, 'rb'), 'image/png')
        }
        
        data = {
            'number': phone_number,
            'recipients[]': group_id,
            'message': message
        }
        
        # Send the request
        response = requests.post(f"{api_url}/v2/send", files=files, data=data, timeout=30)
        
        # Close the file
        files['attachment'][1].close()
        
        if response.status_code == 201:
            logger.info(f"✅ File sent successfully: {os.path.basename(file_path)}")
            return True
        else:
            logger.error(f"❌ Signal API error {response.status_code}: {response.text}")
            return False
            
    except Exception as e:
        logger.error(f"❌ Error sending to Signal: {e}")
        return False


async def send_heatmaps_to_signal():
    """Send heatmaps to Signal"""
    logger.info("📤 Sending today's heatmaps to Signal...")
    
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
    success = send_to_signal_attachment(
        categorical_path,
        "📊 Global Interest Rates - Categorical Analysis"
    )
    if success:
        success_count += 1
    
    # Wait a moment between sends
    await asyncio.sleep(3)
    
    # Send forex heatmap
    logger.info("📤 Sending forex heatmap...")
    success = send_to_signal_attachment(
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
    success = asyncio.run(send_heatmaps_to_signal())
    if success:
        print("\n✅ Heatmaps delivered to Signal group!")
    else:
        print("\n❌ Failed to deliver heatmaps")
    sys.exit(0 if success else 1)