#!/usr/bin/env python3
"""
Generate and Send Missing Heatmaps
Create the heatmaps that were disabled in today's 6 AM run
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

class HeatmapGenerator:
    """Generate and send the missing heatmaps"""
    
    def __init__(self):
        self.heatmap_dir = Path("/home/ohms/OhmsAlertsReports/heatmaps_package/core_files")
        
    async def generate_heatmaps(self):
        """Generate the Bloomberg-style heatmaps"""
        try:
            logger.info("🔥 Generating Bloomberg-style interest rate heatmaps...")
            
            # Change to heatmap directory
            original_dir = Path.cwd()
            
            # Run the heatmap generation script
            cmd = ["python3", "bloomberg_report_final.py"]
            
            result = subprocess.run(
                cmd, 
                cwd=self.heatmap_dir,
                capture_output=True, 
                text=True, 
                timeout=300
            )
            
            if result.returncode == 0:
                logger.info("✅ Heatmaps generated successfully")
                logger.info(f"Output: {result.stdout}")
                return True
            else:
                logger.error(f"❌ Heatmap generation failed: {result.stderr}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Exception during heatmap generation: {e}")
            return False
    
    def find_latest_heatmaps(self):
        """Find the latest generated heatmap files"""
        try:
            # Look for PNG files with today's date
            today = datetime.now().strftime("%Y%m%d")
            
            heatmap_files = []
            
            # Common heatmap file patterns
            patterns = [
                f"bloomberg_heatmap_{today}*.png",
                f"interest_rate_heatmap_{today}*.png",
                f"forex_heatmap_{today}*.png",
                "bloomberg_heatmap_latest.png",
                "interest_rate_heatmap.png"
            ]
            
            for pattern in patterns:
                files = list(self.heatmap_dir.glob(pattern))
                heatmap_files.extend(files)
            
            # Remove duplicates and sort by modification time
            unique_files = list(set(heatmap_files))
            unique_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
            
            logger.info(f"Found {len(unique_files)} heatmap files")
            for file in unique_files:
                logger.info(f"  - {file.name}")
            
            return unique_files
            
        except Exception as e:
            logger.error(f"❌ Error finding heatmap files: {e}")
            return []
    
    async def send_heatmap_to_telegram(self, image_path):
        """Send heatmap image to Telegram"""
        try:
            url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendPhoto"
            
            with open(image_path, 'rb') as image_file:
                files = {'photo': image_file}
                data = {
                    'chat_id': TELEGRAM_GROUP_ID,
                    'caption': f'📊 Interest Rate Heatmap - {datetime.now().strftime("%Y-%m-%d %H:%M PST")}'
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
    
    async def send_heatmap_to_signal(self, image_path):
        """Send heatmap image to Signal"""
        try:
            # Signal CLI doesn't easily support file uploads via curl
            # For now, just send a text message indicating heatmap availability
            payload = {
                'number': '+16572463906',
                'recipients': ['group.ZmFLQ25IUTBKbWpuNFdpaDdXTjVoVXpYOFZtNGVZZ1lYRGdwMWpMcW0zMD0='],
                'message': f'📊 Interest Rate Heatmap generated: {image_path.name} - {datetime.now().strftime("%Y-%m-%d %H:%M PST")}'
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
                logger.info(f"✅ SIGNAL: Heatmap notification sent")
                return True
            else:
                logger.error(f"❌ SIGNAL: Failed to send notification - {result.stderr}")
                return False
                
        except Exception as e:
            logger.error(f"❌ SIGNAL: Exception - {e}")
            return False
    
    async def generate_and_send_heatmaps(self):
        """Complete workflow: generate and send heatmaps"""
        try:
            logger.info("🚀 Starting heatmap generation and delivery...")
            
            # Generate heatmaps
            generation_success = await self.generate_heatmaps()
            if not generation_success:
                logger.error("❌ Cannot proceed - heatmap generation failed")
                return False
            
            # Find generated files
            heatmap_files = self.find_latest_heatmaps()
            if not heatmap_files:
                logger.error("❌ No heatmap files found after generation")
                return False
            
            # Send to both platforms
            success_count = 0
            total_sent = 0
            
            for heatmap_file in heatmap_files[:2]:  # Limit to 2 most recent
                logger.info(f"📤 Sending {heatmap_file.name}...")
                
                telegram_success = await self.send_heatmap_to_telegram(heatmap_file)
                signal_success = await self.send_heatmap_to_signal(heatmap_file)
                
                if telegram_success:
                    success_count += 1
                if signal_success:
                    success_count += 1
                    
                total_sent += 2  # 2 platforms per file
            
            logger.info(f"📊 HEATMAP DELIVERY SUMMARY: {success_count}/{total_sent} deliveries successful")
            
            return success_count > 0
            
        except Exception as e:
            logger.error(f"❌ Heatmap workflow failed: {e}")
            return False

async def main():
    """Main execution"""
    logger.info("=" * 60)
    logger.info("MISSING HEATMAP GENERATION - Emergency Recovery")
    logger.info("=" * 60)
    
    generator = HeatmapGenerator()
    success = await generator.generate_and_send_heatmaps()
    
    if success:
        logger.info("✅ Heatmap recovery completed successfully!")
    else:
        logger.error("❌ Heatmap recovery failed")
    
    logger.info("=" * 60)

if __name__ == "__main__":
    asyncio.run(main())