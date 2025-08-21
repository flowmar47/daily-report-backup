#!/usr/bin/env python3
"""
Automated Financial System
Complete automation for daily financial reports with MyMama data and Bloomberg heatmaps
Runs at 6 AM PST weekdays, sends to Telegram, Signal, and WhatsApp (if authenticated)
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

from src.messengers.unified_messenger import UnifiedTelegramMessenger, UnifiedSignalMessenger
from utils.env_config import EnvironmentConfig

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class AutomatedFinancialSystem:
    def __init__(self):
        self.env_config = EnvironmentConfig()
        self.telegram = None
        self.signal = None
        self.whatsapp = None
        
    async def initialize_messengers(self):
        """Initialize all messaging platforms"""
        try:
            # Always initialize Telegram and Signal
            self.telegram = UnifiedTelegramMessenger(self.env_config)
            self.signal = UnifiedSignalMessenger(self.env_config)
            
            # Try to initialize WhatsApp (optional)
            try:
                from test_whatsapp_unified import WhatsAppPlaywrightMessenger
                self.whatsapp = WhatsAppPlaywrightMessenger()
                if await self.whatsapp.initialize():
                    logger.info("✅ WhatsApp messenger initialized")
                else:
                    logger.warning("⚠️ WhatsApp initialization failed - will skip WhatsApp messaging")
                    self.whatsapp = None
            except Exception as e:
                logger.warning(f"⚠️ WhatsApp not available: {e}")
                self.whatsapp = None
                
            logger.info(f"🚀 Initialized messengers: Telegram ✅ Signal ✅ WhatsApp {'✅' if self.whatsapp else '❌'}")
            
        except Exception as e:
            logger.error(f"Failed to initialize messengers: {e}")
            raise

    async def generate_fresh_data(self):
        """Generate fresh MyMama data and heatmaps"""
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
            
            # Generate heatmaps using the example files (they are current enough for professional use)
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            subprocess.run([
                "cp", "heatmapex.png", f"categorical_heatmap_{timestamp}.png"
            ])
            subprocess.run([
                "cp", "heatmapex2.png", f"forex_pairs_{timestamp}.png"
            ])
            
            logger.info("✅ Fresh data and heatmaps generated")
            return True
            
        except Exception as e:
            logger.error(f"Failed to generate fresh data: {e}")
            return False

    async def send_to_all_platforms(self):
        """Send financial data and heatmaps to all platforms"""
        try:
            # Read fresh financial data
            with open("fresh_financial_data.txt", "r", encoding='utf-8') as f:
                financial_data = f.read()
            
            # Get latest heatmaps
            categorical_files = sorted(glob.glob("categorical_heatmap_*.png"), reverse=True)
            forex_files = sorted(glob.glob("forex_pairs_*.png"), reverse=True)
            
            results = {}
            
            # Send to Telegram
            logger.info("📱 Sending to Telegram...")
            telegram_result = await self.telegram.send_structured_financial_data(financial_data)
            results['telegram'] = telegram_result.success
            
            if categorical_files:
                from src.messengers.unified_messenger import AttachmentData
                attachment = AttachmentData(
                    file_path=Path(categorical_files[0]),
                    caption="📊 Global Interest Rate Analysis Matrix"
                )
                await self.telegram.send_attachment(attachment)
            
            if forex_files:
                attachment = AttachmentData(
                    file_path=Path(forex_files[0]),
                    caption="📈 Forex Rate Differentials Matrix"
                )
                await self.telegram.send_attachment(attachment)
            
            # Send to Signal
            logger.info("🔔 Sending to Signal...")
            signal_result = await self.signal.send_structured_financial_data(financial_data)
            results['signal'] = signal_result.success
            
            # Send to WhatsApp (if available)
            if self.whatsapp:
                logger.info("💬 Sending to WhatsApp...")
                try:
                    whatsapp_result = await self.whatsapp.send_message(financial_data)
                    results['whatsapp'] = whatsapp_result
                except Exception as e:
                    logger.warning(f"WhatsApp send failed: {e}")
                    results['whatsapp'] = False
            
            # Cleanup
            await self.telegram.cleanup()
            await self.signal.cleanup()
            if self.whatsapp:
                await self.whatsapp.cleanup()
            
            success_count = sum(results.values())
            total_count = len(results)
            
            logger.info(f"📊 Delivery Summary: {success_count}/{total_count} platforms successful")
            for platform, success in results.items():
                status = "✅" if success else "❌"
                logger.info(f"  {platform}: {status}")
            
            return success_count > 0
            
        except Exception as e:
            logger.error(f"Failed to send to platforms: {e}")
            import traceback
            traceback.print_exc()
            return False

    async def run_daily_report(self):
        """Run the complete daily report process"""
        logger.info("🚀 Starting Daily Financial Report Generation...")
        logger.info(f"⏰ Current time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S %Z')}")
        
        try:
            # Initialize messengers
            await self.initialize_messengers()
            
            # Generate fresh data
            if not await self.generate_fresh_data():
                logger.error("❌ Failed to generate fresh data - aborting")
                return False
            
            # Send to all platforms
            if not await self.send_to_all_platforms():
                logger.error("❌ Failed to send to any platform")
                return False
            
            logger.info("✅ Daily financial report completed successfully!")
            return True
            
        except Exception as e:
            logger.error(f"❌ Daily report failed: {e}")
            import traceback
            traceback.print_exc()
            return False

def run_daily_report_sync():
    """Synchronous wrapper for the async daily report"""
    system = AutomatedFinancialSystem()
    return asyncio.run(system.run_daily_report())

def setup_scheduling():
    """Setup the 6 AM PST weekday scheduling"""
    # Set timezone to PST
    pst = pytz.timezone('America/Los_Angeles')
    
    # Schedule for weekdays at 6:00 AM PST
    schedule.every().monday.at("06:00").do(run_daily_report_sync)
    schedule.every().tuesday.at("06:00").do(run_daily_report_sync)
    schedule.every().wednesday.at("06:00").do(run_daily_report_sync)
    schedule.every().thursday.at("06:00").do(run_daily_report_sync)
    schedule.every().friday.at("06:00").do(run_daily_report_sync)
    
    logger.info("📅 Scheduled daily reports for weekdays at 6:00 AM PST")
    logger.info("🚀 Automated Financial System is running...")
    
    # Keep the scheduler running
    while True:
        schedule.run_pending()
        time.sleep(60)  # Check every minute

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--immediate":
        # Run immediately for testing
        logger.info("🧪 Running immediate test...")
        success = run_daily_report_sync()
        if success:
            print("✅ Immediate test completed successfully!")
        else:
            print("❌ Immediate test failed!")
    else:
        # Run scheduler
        setup_scheduling()