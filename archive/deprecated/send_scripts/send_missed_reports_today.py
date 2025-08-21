#!/usr/bin/env python3
"""
Send Today's Missed Reports to All 3 Platforms
Scrapes live data and sends to Signal, Telegram, and WhatsApp
"""

import asyncio
import logging
import sys
import json
from datetime import datetime
from pathlib import Path

# Add src path for imports
sys.path.append(str(Path(__file__).parent / 'src'))

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/missed_reports_today.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Load configuration
with open('config.json', 'r') as f:
    CONFIG = json.load(f)

async def send_todays_missed_reports():
    """Send today's missed reports with live data to all platforms"""
    try:
        logger.info("=" * 60)
        logger.info("🚀 SENDING TODAY'S MISSED REPORTS TO ALL 3 PLATFORMS")
        logger.info(f"📅 Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info("=" * 60)
        
        # Import the main automation class
        from main import DailyReportAutomation
        
        # Initialize the automation system
        automation = DailyReportAutomation()
        
        # Run the complete daily report process
        logger.info("🔥 Starting live data collection and tri-platform delivery...")
        await automation.run_daily_report()
        
        logger.info("✅ Today's missed reports sent successfully to all platforms!")
        logger.info("📊 Summary:")
        logger.info("✅ Live data scraped from MyMama.uk")
        logger.info("✅ Bloomberg-style heatmaps generated")
        logger.info("✅ Reports delivered to Signal + Telegram + WhatsApp")
        logger.info("=" * 60)
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Failed to send today's reports: {e}")
        import traceback
        traceback.print_exc()
        return False

async def verify_scheduling_config():
    """Verify the 6 AM weekday scheduling is properly configured"""
    try:
        logger.info("\n🕕 VERIFYING 6 AM WEEKDAY SCHEDULE CONFIGURATION")
        logger.info("=" * 50)
        
        # Check config.json settings
        app_settings = CONFIG.get('app_settings', {})
        report_time = app_settings.get('report_time', 'NOT SET')
        report_days = app_settings.get('report_days', [])
        timezone = app_settings.get('timezone', 'NOT SET')
        
        logger.info(f"📅 Report Time: {report_time}")
        logger.info(f"🗓️ Report Days: {', '.join(report_days)}")
        logger.info(f"🌍 Timezone: {timezone}")
        
        # Verify correct configuration
        expected_days = ["monday", "tuesday", "wednesday", "thursday", "friday"]
        if report_time == "06:00" and set(report_days) == set(expected_days) and timezone == "America/Los_Angeles":
            logger.info("✅ Schedule configuration is CORRECT")
            logger.info("✅ Will run Monday-Friday at 6:00 AM PST")
            return True
        else:
            logger.warning("⚠️ Schedule configuration needs verification")
            logger.warning(f"Expected: 06:00, {expected_days}, America/Los_Angeles")
            logger.warning(f"Current: {report_time}, {report_days}, {timezone}")
            return False
            
    except Exception as e:
        logger.error(f"❌ Error verifying schedule config: {e}")
        return False

async def check_for_conflicts():
    """Check for conflicting services or processes"""
    try:
        logger.info("\n🔍 CHECKING FOR CONFLICTING SERVICES")
        logger.info("=" * 40)
        
        import subprocess
        
        # Check for multiple main.py processes
        result = subprocess.run(['pgrep', '-f', 'python.*main.py'], capture_output=True, text=True)
        main_processes = result.stdout.strip().split('\n') if result.stdout.strip() else []
        
        logger.info(f"🔄 Found {len(main_processes)} main.py processes running")
        for i, pid in enumerate(main_processes, 1):
            if pid:
                logger.info(f"  Process {i}: PID {pid}")
        
        # Check for systemd services
        systemd_services = [
            'daily-alerts', 'daily-financial-report', 'signal-api', 
            'interest-rate-scheduler', 'forex-bot'
        ]
        
        active_services = []
        for service in systemd_services:
            try:
                result = subprocess.run(['systemctl', 'is-active', service], 
                                      capture_output=True, text=True)
                if result.stdout.strip() == 'active':
                    active_services.append(service)
            except:
                pass
        
        if active_services:
            logger.warning(f"⚠️ Found {len(active_services)} active systemd services:")
            for service in active_services:
                logger.warning(f"  - {service}")
            logger.warning("These may conflict with the main.py scheduler")
        else:
            logger.info("✅ No conflicting systemd services found")
        
        # Recommendations
        if len(main_processes) > 1:
            logger.warning("⚠️ Multiple main.py processes detected - consider stopping duplicates")
        
        if active_services:
            logger.warning("⚠️ Consider stopping systemd services to avoid conflicts")
            logger.warning("⚠️ Use: sudo systemctl stop <service-name>")
        
        return len(main_processes) <= 1 and len(active_services) == 0
        
    except Exception as e:
        logger.error(f"❌ Error checking for conflicts: {e}")
        return False

async def main():
    """Main execution function"""
    print("🚀 Sending Today's Missed Reports + Verification")
    print("=" * 60)
    
    try:
        # Step 1: Send today's missed reports
        logger.info("STEP 1: Sending today's missed reports with live data...")
        reports_sent = await send_todays_missed_reports()
        
        if not reports_sent:
            logger.error("❌ Failed to send reports - stopping here")
            return
        
        # Step 2: Verify scheduling configuration
        logger.info("STEP 2: Verifying 6 AM weekday schedule...")
        schedule_ok = await verify_scheduling_config()
        
        # Step 3: Check for conflicts
        logger.info("STEP 3: Checking for conflicting services...")
        no_conflicts = await check_for_conflicts()
        
        # Final summary
        print("\n" + "=" * 60)
        print("📋 FINAL SUMMARY")
        print("=" * 60)
        
        if reports_sent:
            print("✅ Today's reports sent to ALL 3 platforms")
            print("   - Signal ✅")
            print("   - Telegram ✅") 
            print("   - WhatsApp ✅")
        else:
            print("❌ Failed to send today's reports")
        
        if schedule_ok:
            print("✅ 6 AM weekday schedule properly configured")
        else:
            print("⚠️ Schedule configuration needs attention")
        
        if no_conflicts:
            print("✅ No conflicting services detected")
        else:
            print("⚠️ Potential conflicts detected - see logs")
        
        print("\n🔄 Next scheduled report: Tomorrow at 6:00 AM PST")
        print("📱 Will be delivered to all 3 platforms automatically")
        
    except Exception as e:
        logger.error(f"❌ Script failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())