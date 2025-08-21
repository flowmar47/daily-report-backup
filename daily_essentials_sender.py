#!/usr/bin/env python3
"""
Daily Essentials Sender
Scrapes MyMama essentials page and sends to Signal & Telegram at 8 AM PST on weekdays
"""

import asyncio
import json
import logging
import schedule
import time
from datetime import datetime
from pathlib import Path
import pytz
from dotenv import load_dotenv
import os
from messenger_compatibility import SignalMessenger, TelegramMessenger

# Load environment variables
script_dir = Path(__file__).parent
load_dotenv(script_dir / '.env')

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(script_dir / 'logs' / 'daily_essentials.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Timezone
PST = pytz.timezone('America/Los_Angeles')


class DailyEssentialsSender:
    """Main class for scraping and sending daily essentials"""
    
    def __init__(self):
        """Initialize with configuration and components"""
        # Load configuration
        config_path = script_dir / 'config.json'
        with open(config_path, 'r') as f:
            self.config = json.load(f)
        
        # Initialize components
        self.scraper = None
        self.messengers = []
        self.setup_components()
    
    def setup_components(self):
        """Setup scraper and messengers"""
        try:
            # Initialize MyMama scraper
            from real_only_mymama_scraper import RealOnlyMyMamaScraper
            self.scraper = RealOnlyMyMamaScraper()
            logger.info("✅ MyMama scraper initialized")
            
            # Initialize messengers
            from messengers.multi_messenger import MultiMessenger
            
            messengers = []
            
            # Setup Signal messenger
            signal_config = {
                'signal_cli_path': os.getenv('SIGNAL_CLI_PATH', 'signal-cli'),
                'phone_number': os.getenv('SIGNAL_PHONE_NUMBER'),
                'group_id': os.getenv('SIGNAL_GROUP_ID'),
                'config_dir': str(Path.home() / '.local/share/signal-cli')
            }
            
            if signal_config['phone_number'] and signal_config['group_id']:
                signal_messenger = SignalMessenger(signal_config)
                messengers.append(signal_messenger)
                logger.info("✅ Signal messenger configured")
            else:
                logger.warning("⚠️ Signal messenger not configured (missing credentials)")
            
            # Setup Telegram messenger
            telegram_config = {
                'bot_token': os.getenv('TELEGRAM_BOT_TOKEN'),
                'chat_id': os.getenv('TELEGRAM_GROUP_ID')
            }
            
            if telegram_config['bot_token'] and telegram_config['chat_id']:
                telegram_messenger = TelegramMessenger(telegram_config)
                messengers.append(telegram_messenger)
                logger.info("✅ Telegram messenger configured")
            else:
                logger.warning("⚠️ Telegram messenger not configured (missing credentials)")
            
            # Create multi-messenger
            if messengers:
                self.multi_messenger = MultiMessenger(messengers, {'concurrent_sends': True})
                logger.info(f"✅ Multi-messenger initialized with {len(messengers)} platforms")
            else:
                logger.error("❌ No messengers configured!")
                self.multi_messenger = None
                
        except Exception as e:
            logger.error(f"❌ Error setting up components: {e}")
            raise
    
    async def collect_essentials_data(self):
        """Collect data from MyMama essentials page"""
        logger.info("🔍 Collecting essentials data from MyMama...")
        
        try:
            # Use the existing scraper to get real alerts
            result = await self.scraper.get_real_alerts_only()
            
            if result.get('has_real_data'):
                logger.info("✅ Successfully collected essentials data")
                return result
            else:
                logger.warning("⚠️ No real data available from MyMama")
                return None
                
        except Exception as e:
            logger.error(f"❌ Error collecting data: {e}")
            return None
    
    def format_essentials_report(self, data):
        """Format the essentials data into a readable report"""
        if not data or not data.get('has_real_data'):
            return None
        
        # Current timestamp
        now = datetime.now(PST)
        date_str = now.strftime("%A, %B %d, %Y")
        time_str = now.strftime("%I:%M %p PST")
        
        # Start building report
        report_lines = [
            f"🔔 **MyMama Essentials Alert**",
            f"📅 {date_str}",
            f"⏰ {time_str}",
            "",
            "---",
            ""
        ]
        
        # Add Forex Signals
        forex_alerts = data.get('forex_alerts', {})
        if forex_alerts:
            report_lines.append("💱 **FOREX SIGNALS**")
            report_lines.append("")
            
            for pair, alert in forex_alerts.items():
                signal = alert.get('signal', 'N/A')
                entry = alert.get('entry', 'N/A')
                exit_price = alert.get('exit', 'N/A')
                
                if signal == 'BUY':
                    emoji = '🟢'
                elif signal == 'SELL':
                    emoji = '🔴'
                else:
                    emoji = '⚪'
                
                report_lines.append(f"{emoji} **{pair}**: {signal}")
                report_lines.append(f"   Entry: {entry} | Exit: {exit_price}")
                report_lines.append("")
        
        # Add Options Data
        options_data = data.get('options_data', [])
        if options_data:
            report_lines.append("📊 **OPTIONS DATA**")
            report_lines.append("")
            
            for option in options_data:
                ticker = option.get('ticker', 'N/A')
                high_52w = option.get('high_52week', 'N/A')
                low_52w = option.get('low_52week', 'N/A')
                call_strike = option.get('call_strike', 'N/A')
                put_strike = option.get('put_strike', 'N/A')
                
                report_lines.append(f"**{ticker}**")
                report_lines.append(f"52W Range: {low_52w} - {high_52w}")
                report_lines.append(f"CALL > {call_strike} | PUT < {put_strike}")
                report_lines.append("")
        
        # Add Earnings Releases
        earnings_data = data.get('earnings_releases', [])
        if earnings_data:
            report_lines.append("📈 **EARNINGS RELEASES**")
            report_lines.append("")
            
            for earning in earnings_data[:5]:  # Limit to top 5
                ticker = earning.get('ticker', 'N/A')
                company = earning.get('company', 'N/A')
                date = earning.get('earnings_date', 'N/A')
                price = earning.get('current_price', 'N/A')
                
                report_lines.append(f"**{ticker}** ({company})")
                report_lines.append(f"Price: {price} | Date: {date}")
                report_lines.append("")
        
        # Add Premium Trades
        swing_trades = data.get('swing_trades', [])
        day_trades = data.get('day_trades', [])
        
        if swing_trades or day_trades:
            report_lines.append("🎯 **PREMIUM TRADES**")
            report_lines.append("")
            
            if swing_trades:
                report_lines.append("📊 *Swing Trades:*")
                for trade in swing_trades[:3]:  # Limit to top 3
                    ticker = trade.get('ticker', 'N/A')
                    company = trade.get('company', 'N/A')
                    price = trade.get('current_price', 'N/A')
                    report_lines.append(f"• {ticker} ({company}) - {price}")
                report_lines.append("")
            
            if day_trades:
                report_lines.append("⚡ *Day Trades:*")
                for trade in day_trades[:3]:  # Limit to top 3
                    ticker = trade.get('ticker', 'N/A')
                    company = trade.get('company', 'N/A')
                    price = trade.get('current_price', 'N/A')
                    report_lines.append(f"• {ticker} ({company}) - {price}")
                report_lines.append("")
        
        # Add footer
        report_lines.extend([
            "---",
            "",
            "⚠️ *Risk Warning: Trading involves risk. Always do your own research.*",
            "",
            "📊 *Data sourced from market analysis*"
        ])
        
        return "\n".join(report_lines)
    
    async def send_essentials_alert(self):
        """Main job function to scrape and send essentials"""
        logger.info("🚀 Starting essentials alert job...")
        
        try:
            # Collect data
            data = await self.collect_essentials_data()
            
            if not data or not data.get('has_real_data'):
                logger.warning("⚠️ No real data available - skipping send")
                return
            
            # Format report
            report = self.format_essentials_report(data)
            
            if not report:
                logger.warning("⚠️ Failed to format report")
                return
            
            # Send via multi-messenger
            if self.multi_messenger:
                result = await self.multi_messenger.send_message(report)
                
                if result.status.value == 'success':
                    logger.info("✅ Successfully sent essentials alert to all platforms")
                elif result.status.value == 'partial':
                    logger.warning("⚠️ Partially sent essentials alert")
                    metadata = result.metadata
                    logger.info(f"Successful platforms: {metadata.get('successful_platforms', [])}")
                    logger.info(f"Failed platforms: {metadata.get('failed_platforms', [])}")
                else:
                    logger.error("❌ Failed to send essentials alert")
                    if result.error:
                        logger.error(f"Error: {result.error}")
            else:
                logger.error("❌ No messengers configured")
            
        except Exception as e:
            logger.error(f"❌ Error in essentials alert job: {e}", exc_info=True)
    
    def run_scheduler(self):
        """Setup and run the scheduler"""
        # Schedule for 6 AM PST on weekdays
        schedule_time = "06:00"
        
        logger.info(f"🕒 Scheduling essentials alerts for weekdays at {schedule_time} PST")
        
        # Create async wrapper
        def job_wrapper():
            asyncio.run(self.send_essentials_alert())
        
        # Schedule for each weekday
        schedule.every().monday.at(schedule_time, PST).do(job_wrapper)
        schedule.every().tuesday.at(schedule_time, PST).do(job_wrapper)
        schedule.every().wednesday.at(schedule_time, PST).do(job_wrapper)
        schedule.every().thursday.at(schedule_time, PST).do(job_wrapper)
        schedule.every().friday.at(schedule_time, PST).do(job_wrapper)
        
        logger.info("✅ Scheduler configured successfully")
        logger.info("Waiting for scheduled jobs...")
        
        # Keep running
        while True:
            schedule.run_pending()
            time.sleep(60)  # Check every minute


async def test_run():
    """Test run the essentials alert immediately"""
    logger.info("🧪 Running test alert...")
    sender = DailyEssentialsSender()
    await sender.send_essentials_alert()
    logger.info("✅ Test run complete")


def main():
    """Main entry point"""
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == 'test':
        # Run test immediately
        asyncio.run(test_run())
    else:
        # Run scheduler
        logger.info("Starting Daily Essentials Sender...")
        sender = DailyEssentialsSender()
        
        try:
            sender.run_scheduler()
        except KeyboardInterrupt:
            logger.info("\n👋 Scheduler stopped by user")
        except Exception as e:
            logger.error(f"❌ Scheduler error: {e}", exc_info=True)


if __name__ == "__main__":
    main()