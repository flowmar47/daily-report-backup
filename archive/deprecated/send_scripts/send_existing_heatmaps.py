#!/usr/bin/env python3
"""
Send Existing Heatmaps
Use the most recent heatmaps that were already generated
"""

import asyncio
import subprocess
import logging
import json
import requests
from pathlib import Path
from datetime import datetime

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Telegram config
TELEGRAM_BOT_TOKEN = "7695859844:AAE_PxUOckN57S5eGyFKVW4fp4pReR0zzMI"
TELEGRAM_GROUP_ID = "-1002548864790"

async def send_heatmap_to_telegram(image_path, caption):
    """Send heatmap image to Telegram"""
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendPhoto"
        
        with open(image_path, 'rb') as image_file:
            files = {'photo': image_file}
            data = {
                'chat_id': TELEGRAM_GROUP_ID,
                'caption': caption
            }
            
            response = requests.post(url, data=data, files=files, timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                if result.get('ok'):
                    logger.info(f"✅ TELEGRAM: Heatmap sent successfully ({image_path.name})")
                    return True
                else:
                    logger.error(f"❌ TELEGRAM: API error - {result.get('description')}")
                    return False
            else:
                logger.error(f"❌ TELEGRAM: HTTP {response.status_code}: {response.text}")
                return False
                
    except Exception as e:
        logger.error(f"❌ TELEGRAM: Failed to send {image_path.name} - {e}")
        return False

async def send_notification_to_signal(message):
    """Send notification to Signal"""
    try:
        payload = {
            'number': '+16572463906',
            'recipients': ['group.ZmFLQ25IUTBKbWpuNFdpaDdXTjVoVXpYOFZtNGVZZ1lYRGdwMWpMcW0zMD0='],
            'message': message
        }
        
        cmd = [
            'curl', '-X', 'POST',
            'http://localhost:8080/v2/send',
            '-H', 'Content-Type: application/json',
            '-d', json.dumps(payload),
            '--max-time', '30'
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=35)
        
        if result.returncode == 0:
            logger.info(f"✅ SIGNAL: Notification sent")
            return True
        else:
            logger.error(f"❌ SIGNAL: Failed - {result.stderr}")
            return False
            
    except Exception as e:
        logger.error(f"❌ SIGNAL: Exception - {e}")
        return False

async def main():
    """Send most recent heatmaps"""
    logger.info("=" * 60)
    logger.info("SENDING EXISTING HEATMAPS - Emergency Recovery")
    logger.info("=" * 60)
    
    heatmap_dir = Path("/home/ohms/OhmsAlertsReports/heatmaps_package/core_files")
    
    # Find most recent heatmap files
    categorical_files = list(heatmap_dir.glob("categorical_heatmap_*.png"))
    forex_files = list(heatmap_dir.glob("forex_pairs_*.png"))
    
    # Sort by modification time (most recent first)
    categorical_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
    forex_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
    
    if not categorical_files or not forex_files:
        logger.error("❌ No heatmap files found")
        return
    
    # Get the most recent files
    latest_categorical = categorical_files[0]
    latest_forex = forex_files[0]
    
    logger.info(f"📊 Using categorical heatmap: {latest_categorical.name}")
    logger.info(f"📊 Using forex pairs heatmap: {latest_forex.name}")
    
    # Send to Telegram
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M PST")
    
    categorical_success = await send_heatmap_to_telegram(
        latest_categorical, 
        f"📊 Interest Rate Categorical Analysis - {timestamp}"
    )
    
    forex_success = await send_heatmap_to_telegram(
        latest_forex, 
        f"📊 Forex Pairs Differential Matrix - {timestamp}"
    )
    
    # Send notification to Signal
    signal_success = await send_notification_to_signal(
        f"📊 Interest Rate Heatmaps sent to Telegram - {timestamp}\n"
        f"- Categorical Analysis: {latest_categorical.name}\n"
        f"- Forex Pairs Matrix: {latest_forex.name}"
    )
    
    # Summary
    success_count = sum([categorical_success, forex_success, signal_success])
    logger.info(f"📊 HEATMAP DELIVERY SUMMARY: {success_count}/3 deliveries successful")
    
    if success_count >= 2:
        logger.info("✅ Heatmap delivery completed successfully!")
    else:
        logger.warning("⚠️ Partial success in heatmap delivery")

if __name__ == "__main__":
    asyncio.run(main())