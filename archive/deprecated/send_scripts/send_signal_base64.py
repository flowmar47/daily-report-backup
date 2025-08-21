#!/usr/bin/env python3
"""
Send heatmaps to Signal using base64 encoding
"""

import asyncio
import os
import sys
import logging
import requests
import base64
import json

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def send_to_signal_base64(file_path: str, message: str):
    """Send file to Signal using base64 encoding"""
    api_url = "http://localhost:8080"
    phone_number = '+16572463906'
    group_id = 'group.cUY1YUE5SHRRMW0wQy9SVGMrSWNvVTQrakluaU00YXlBeVBscUdLUFdMTT0='
    
    try:
        # Read and encode file as base64
        with open(file_path, 'rb') as f:
            file_data = f.read()
            file_base64 = base64.b64encode(file_data).decode('utf-8')
        
        # Prepare the JSON payload
        payload = {
            "number": phone_number,
            "recipients": [group_id],
            "message": message,
            "base64_attachments": [file_base64]
        }
        
        # Send the request
        response = requests.post(
            f"{api_url}/v2/send",
            headers={'Content-Type': 'application/json'},
            data=json.dumps(payload),
            timeout=30
        )
        
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
    logger.info("📤 Sending today's heatmaps to Signal (base64 method)...")
    
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
    success = send_to_signal_base64(
        categorical_path,
        "📊 Global Interest Rates - Categorical Analysis"
    )
    if success:
        success_count += 1
    
    # Wait a moment between sends
    await asyncio.sleep(3)
    
    # Send forex heatmap
    logger.info("📤 Sending forex heatmap...")
    success = send_to_signal_base64(
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