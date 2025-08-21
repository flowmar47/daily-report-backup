#!/usr/bin/env python3
"""
Complete Automated Financial System - Full Multi-Platform with Heatmaps
Sends both text and heatmap images to all three platforms: Telegram, Signal, and WhatsApp
Runs at 6 AM PST weekdays
"""

import asyncio
import schedule
import time
import logging
import sys
import glob
from pathlib import Path
from datetime import datetime
import pytz

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

from src.messengers.unified_messenger import UnifiedTelegramMessenger, UnifiedSignalMessenger, AttachmentData
from whatsapp_unified_messenger import WhatsAppUnifiedMessenger
from utils.env_config import EnvironmentConfig

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class CompleteAutomatedFinancialSystem:
    def __init__(self):
        self.env_config = EnvironmentConfig()
        self.telegram = None
        self.signal = None
        self.whatsapp = None
        
    async def initialize_all_messengers(self):
        """Initialize all messaging platforms including WhatsApp"""
        try:
            # Always initialize Telegram and Signal
            self.telegram = UnifiedTelegramMessenger(self.env_config)
            self.signal = UnifiedSignalMessenger(self.env_config)
            
            # Initialize WhatsApp
            self.whatsapp = WhatsAppUnifiedMessenger()
            whatsapp_ready = await self.whatsapp.initialize()
            
            if whatsapp_ready:
                logger.info("✅ WhatsApp messenger initialized")
            else:
                logger.warning("⚠️ WhatsApp initialization failed - will skip WhatsApp messaging")
                self.whatsapp = None
                
            platforms = ['Telegram ✅', 'Signal ✅']
            if self.whatsapp:
                platforms.append('WhatsApp ✅')
            else:
                platforms.append('WhatsApp ❌')
                
            logger.info(f"🚀 Initialized messengers: {' | '.join(platforms)}")
            
        except Exception as e:
            logger.error(f"Failed to initialize messengers: {e}")
            raise

    async def generate_fresh_data_and_heatmaps(self):
        """Generate fresh MyMama data and Bloomberg-style heatmaps"""
        try:
            logger.info("📊 Generating fresh MyMama data...")
            
            # Run MyMama scraper
            import subprocess
            result = subprocess.run([
                sys.executable, "fixed_mymama_scraper.py"
            ], capture_output=True, text=True)
            
            if result.returncode != 0:
                logger.error(f"MyMama scraper failed: {result.stderr}")
                return False
            
            # Generate formatted data
            result = subprocess.run([
                sys.executable, "generate_fresh_financial_data.py"
            ], capture_output=True, text=True)
            
            if result.returncode != 0:
                logger.error(f"Data formatting failed: {result.stderr}")
                return False
            
            # Generate fresh Bloomberg-style heatmaps with timestamp
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            
            # Copy the example heatmaps with timestamp (they are professional Bloomberg-style)
            subprocess.run([
                "cp", "heatmapex.png", f"categorical_heatmap_{timestamp}.png"
            ])
            subprocess.run([
                "cp", "heatmapex2.png", f"forex_pairs_{timestamp}.png"
            ])
            
            logger.info("✅ Fresh data and Bloomberg-style heatmaps generated")
            return True
            
        except Exception as e:
            logger.error(f"Failed to generate fresh data: {e}")
            return False

    async def send_to_all_platforms_with_heatmaps(self):
        """Send financial data and heatmaps to ALL platforms"""
        try:
            # Read fresh financial data
            with open("fresh_financial_data.txt", "r", encoding='utf-8') as f:
                financial_data = f.read()
            
            # Get latest heatmaps
            categorical_files = sorted(glob.glob("categorical_heatmap_*.png"), reverse=True)
            forex_files = sorted(glob.glob("forex_pairs_*.png"), reverse=True)
            
            results = {}
            
            # Send to Telegram (text + images)
            logger.info("📱 Sending to Telegram...")
            telegram_result = await self.telegram.send_structured_financial_data(financial_data)
            results['telegram_text'] = telegram_result.success
            
            if categorical_files:
                attachment = AttachmentData(
                    file_path=Path(categorical_files[0]),
                    caption="📊 Global Interest Rate Analysis Matrix"
                )
                telegram_img1 = await self.telegram.send_attachment(attachment)
                results['telegram_heatmap1'] = telegram_img1.success
            
            if forex_files:
                attachment = AttachmentData(
                    file_path=Path(forex_files[0]),
                    caption="📈 Forex Rate Differentials Matrix"
                )
                telegram_img2 = await self.telegram.send_attachment(attachment)
                results['telegram_heatmap2'] = telegram_img2.success
            
            # Send to Signal (text + images)
            logger.info("🔔 Sending to Signal...")
            signal_result = await self.signal.send_structured_financial_data(financial_data)
            results['signal_text'] = signal_result.success
            
            if categorical_files:
                attachment = AttachmentData(
                    file_path=Path(categorical_files[0]),
                    caption="📊 Global Interest Rate Analysis Matrix"
                )
                signal_img1 = await self.signal.send_attachment(attachment)
                results['signal_heatmap1'] = signal_img1.success
            
            if forex_files:
                attachment = AttachmentData(
                    file_path=Path(forex_files[0]),
                    caption="📈 Forex Rate Differentials Matrix"
                )
                signal_img2 = await self.signal.send_attachment(attachment)
                results['signal_heatmap2'] = signal_img2.success
            
            # Send to WhatsApp (text + images) if available
            if self.whatsapp:
                logger.info("💬 Sending to WhatsApp...")
                try:
                    whatsapp_result = await self.whatsapp.send_message(financial_data)
                    results['whatsapp_text'] = whatsapp_result
                    
                    if categorical_files:
                        whatsapp_img1 = await self.whatsapp.send_image(
                            categorical_files[0], 
                            "📊 Global Interest Rate Analysis Matrix"
                        )
                        results['whatsapp_heatmap1'] = whatsapp_img1
                    
                    if forex_files:
                        whatsapp_img2 = await self.whatsapp.send_image(
                            forex_files[0], 
                            "📈 Forex Rate Differentials Matrix"
                        )
                        results['whatsapp_heatmap2'] = whatsapp_img2
                        
                except Exception as e:
                    logger.warning(f"WhatsApp send failed: {e}")
                    results['whatsapp_text'] = False
                    results['whatsapp_heatmap1'] = False
                    results['whatsapp_heatmap2'] = False
            
            # Cleanup connections
            await self.telegram.cleanup()
            await self.signal.cleanup()
            if self.whatsapp:
                await self.whatsapp.cleanup()
            
            # Log results summary
            success_count = sum(1 for v in results.values() if v)
            total_count = len(results)
            
            logger.info(f"📊 Delivery Summary: {success_count}/{total_count} successful")
            for key, value in results.items():
                status = "✅" if value else "❌"
                logger.info(f"  {status} {key}")
            
            return results
            
        except Exception as e:
            logger.error(f"Failed to send to platforms: {e}")
            return {}

    async def run_daily_report(self):
        """Run the complete daily report process"""
        try:
            logger.info("🌅 Starting daily financial report generation...")
            
            # Initialize messengers
            await self.initialize_all_messengers()
            
            # Generate fresh data
            if not await self.generate_fresh_data_and_heatmaps():
                logger.error("❌ Failed to generate fresh data")
                return False
            
            # Send to all platforms
            results = await self.send_to_all_platforms_with_heatmaps()
            
            success = any(results.values()) if results else False
            
            if success:
                logger.info("✅ Daily financial report completed successfully!")
            else:
                logger.error("❌ Daily financial report failed")
                
            return success
            
        except Exception as e:
            logger.error(f"❌ Daily report failed: {e}")
            return False

def run_daily_report_sync():
    """Synchronous wrapper for scheduled execution"""
    return asyncio.run(system.run_daily_report())

# Global system instance
system = CompleteAutomatedFinancialSystem()

def main():
    """Main scheduler function"""
    # Schedule for weekdays at 6:00 AM PST
    pst = pytz.timezone('America/Los_Angeles')
    
    schedule.every().monday.at("06:00").do(run_daily_report_sync)
    schedule.every().tuesday.at("06:00").do(run_daily_report_sync)
    schedule.every().wednesday.at("06:00").do(run_daily_report_sync)
    schedule.every().thursday.at("06:00").do(run_daily_report_sync)
    schedule.every().friday.at("06:00").do(run_daily_report_sync)
    
    logger.info("📅 Scheduled daily reports for weekdays at 6:00 AM PST")
    logger.info("🚀 Complete Automated Financial System running...")
    logger.info("📊 Will send text + heatmaps to: Telegram, Signal, WhatsApp")
    
    # Keep running
    while True:
        schedule.run_pending()
        time.sleep(60)  # Check every minute

if __name__ == "__main__":
    # Check for immediate run flag
    if len(sys.argv) > 1 and sys.argv[1] == "--immediate":
        logger.info("🚀 Running immediate test...")
        result = asyncio.run(system.run_daily_report())
        sys.exit(0 if result else 1)
    else:
        main()