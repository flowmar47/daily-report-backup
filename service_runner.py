#!/usr/bin/env python3
"""
Enhanced Service Runner for Ohms Daily Alerts
Ensures robust 24/7 operation with Signal and Telegram integration
"""
import os
import sys
import time
import schedule
import asyncio
import logging
import signal
import json
from pathlib import Path
from datetime import datetime
import subprocess
from messenger_compatibility import TelegramMessenger, SignalMessenger

# Add project to path
sys.path.insert(0, str(Path(__file__).parent))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('logs/service_runner.log')
    ]
)
logger = logging.getLogger('service_runner')

# Load configuration
with open('config.json', 'r') as f:
    CONFIG = json.load(f)

class ServiceRunner:
    """Main service runner with enhanced reliability"""
    
    def __init__(self):
        self.running = True
        self.setup_signal_handlers()
        self.ensure_environment()
        
    def setup_signal_handlers(self):
        """Set up graceful shutdown handlers"""
        signal.signal(signal.SIGTERM, self.handle_shutdown)
        signal.signal(signal.SIGINT, self.handle_shutdown)
        
    def handle_shutdown(self, signum, frame):
        """Handle graceful shutdown"""
        logger.info(f"Received signal {signum}, shutting down gracefully...")
        self.running = False
        
    def ensure_environment(self):
        """Ensure environment is properly configured"""
        # Create necessary directories
        dirs = ['logs', 'reports', 'cache', 'browser_sessions', '/home/ohms/tmp']
        for dir_path in dirs:
            Path(dir_path).mkdir(exist_ok=True)
            
        # Set environment variables
        os.environ['TMPDIR'] = '/home/ohms/tmp'
        os.environ['TZ'] = 'America/Los_Angeles'
        
        # Ensure Playwright is installed
        self.ensure_playwright()
        
    def ensure_playwright(self):
        """Ensure Playwright browsers are installed"""
        try:
            logger.info("Checking Playwright installation...")
            result = subprocess.run(
                ['playwright', 'install', 'chromium'],
                capture_output=True,
                text=True
            )
            if result.returncode == 0:
                logger.info("✅ Playwright Chromium is installed")
            else:
                logger.warning(f"Playwright installation warning: {result.stderr}")
        except Exception as e:
            logger.error(f"Could not verify Playwright: {e}")
    
    async def run_daily_report_with_signal(self):
        """Run daily report with Signal and Telegram integration"""
        logger.info("🚀 Starting daily report with Signal and Telegram...")
        
        try:
            # Import the main automation
            from main import DailyReportAutomation
            
            # Run the main automation
            automation = DailyReportAutomation()
            await automation.run_daily_report()
            
            logger.info("✅ Daily report completed successfully")
            
        except Exception as e:
            logger.error(f"❌ Error in daily report: {e}", exc_info=True)
            
            # Send error notification
            await self.send_error_notification(str(e))
    
    async def send_error_notification(self, error_msg):
        """Send error notification to administrators"""
        try:
            # Try to send via Telegram
            try:
                telegram = TelegramMessenger(CONFIG['messengers']['telegram'])
                await telegram.send_message(error_message)
            except:
                pass
                
            # Try to send via Signal
            try:
                signal_messenger = SignalMessenger(CONFIG['messengers']['signal'])
                await signal_messenger.send_message(error_message)
            except:
                pass
                
        except Exception as e:
            logger.error(f"Could not send error notification: {e}")
    
    def health_check(self):
        """Perform system health check"""
        checks = {
            'signal_api': self.check_signal_api(),
            'playwright': self.check_playwright(),
            'disk_space': self.check_disk_space(),
            'memory': self.check_memory()
        }
        
        healthy = all(checks.values())
        if not healthy:
            logger.warning(f"Health check failed: {checks}")
            
        return healthy
    
    def check_signal_api(self):
        """Check if Signal API is running"""
        try:
            import requests
            response = requests.get('http://localhost:8080/v1/health', timeout=5)
            return response.status_code == 200
        except:
            return False
    
    def check_playwright(self):
        """Check if Playwright is properly installed"""
        playwright_path = Path.home() / '.cache' / 'ms-playwright'
        return playwright_path.exists()
    
    def check_disk_space(self):
        """Check available disk space"""
        import shutil
        stat = shutil.disk_usage('/')
        # Require at least 1GB free
        return stat.free > 1_000_000_000
    
    def check_memory(self):
        """Check available memory"""
        try:
            with open('/proc/meminfo') as f:
                for line in f:
                    if line.startswith('MemAvailable:'):
                        available = int(line.split()[1]) * 1024  # Convert to bytes
                        # Require at least 500MB available
                        return available > 500_000_000
        except:
            return True  # Assume OK if we can't check
        return False
    
    def run_scheduled_job(self):
        """Wrapper for scheduled job execution"""
        logger.info("📅 Scheduled job triggered")
        
        # Perform health check first
        if not self.health_check():
            logger.error("Health check failed, skipping run")
            return
            
        # Run the async job
        asyncio.run(self.run_daily_report_with_signal())
    
    def run(self):
        """Main service loop"""
        logger.info("🏃 Ohms Daily Alerts Service starting...")
        logger.info(f"📅 Scheduled for {CONFIG['app_settings']['report_days']} at {CONFIG['app_settings']['report_time']} PST")
        
        # Schedule daily reports
        report_time = CONFIG['app_settings']['report_time']
        report_days = CONFIG['app_settings']['report_days']
        
        for day in report_days:
            getattr(schedule.every(), day).at(report_time).do(self.run_scheduled_job)
            
        logger.info(f"✅ Scheduled for {', '.join(report_days)} at {report_time}")
        
        # Also schedule hourly health checks
        schedule.every().hour.do(lambda: logger.info(f"Health: {self.health_check()}"))
        
        # Main service loop
        while self.running:
            try:
                schedule.run_pending()
                time.sleep(30)  # Check every 30 seconds
                
            except KeyboardInterrupt:
                logger.info("Service stopped by user")
                break
                
            except Exception as e:
                logger.error(f"Unexpected error in service loop: {e}", exc_info=True)
                time.sleep(60)  # Wait before retrying
                
        logger.info("Service shutting down...")

def main():
    """Main entry point"""
    runner = ServiceRunner()
    runner.run()

if __name__ == "__main__":
    main()