#!/usr/bin/env python3
"""
Send immediate MyMama forex report to Telegram group
"""

import asyncio
import os
import sys
import logging
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

# Load environment variables
script_dir = Path(__file__).parent
env_path = script_dir / '.env'
load_dotenv(env_path)

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def send_immediate_mymama_report():
    """Send current MyMama forex data to Telegram group immediately"""
    
    try:
        # Get Telegram credentials
        bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
        group_id = os.getenv('TELEGRAM_GROUP_ID')
        
        if not bot_token or not group_id:
            logger.error("❌ Missing Telegram credentials")
            return False
        
        logger.info(f"📱 Sending immediate MyMama report to group: {group_id}")
        
        # Collect current MyMama forex data
        from scraper_compatibility import RealOnlyMyMamaScraper
        scraper = RealOnlyMyMamaScraper()
        result = await scraper.scrape_real_alerts()
        
        forex_data = result.get('forex_forecasts', [])
        options_data = result.get('options_trades', [])
        earnings_data = result.get('earnings_reports', [])
        
        if not forex_data and not options_data and not earnings_data:
            logger.warning("⚠️ No financial data available to send")
            return False
        
        # Format the message for Telegram
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S PST')
        
        message = f"""📊 **MyMama Financial Alerts** - {timestamp}

🎯 **Current MyMama.uk Signals**

"""
        
        # Add forex forecasts
        if forex_data:
            message += "**FOREX PAIRS**\n\n"
            for forecast in forex_data:
                pair = forecast.get('pair', 'Unknown')
                high = forecast.get('high', 'N/A')
                low = forecast.get('low', 'N/A')
                action = forecast.get('mt4_action', 'N/A')
                
                if action == "BUY":
                    emoji = "🟢"
                elif action == "SELL":
                    emoji = "🔴"
                else:
                    emoji = "🟡"
                
                message += f"{emoji} **{pair}**: {action}\n"
                if high != 'N/A':
                    message += f"   High: {high}\n"
                if low != 'N/A':
                    message += f"   Low: {low}\n"
                message += "\n"
        
        # Add options data
        if options_data:
            message += "**OPTIONS**\n\n"
            for option in options_data:
                symbol = option.get('symbol', 'Unknown')
                call_strike = option.get('call_strike', 'N/A')
                put_strike = option.get('put_strike', 'N/A')
                message += f"📈 **{symbol}**\n"
                if call_strike != 'N/A':
                    message += f"   CALL > {call_strike}\n"
                if put_strike != 'N/A':
                    message += f"   PUT < {put_strike}\n"
                message += "\n"
        
        # Add earnings data
        if earnings_data:
            message += "**EARNINGS**\n\n"
            for earning in earnings_data:
                company = earning.get('company', 'Unknown')
                date = earning.get('date', 'N/A')
                message += f"📅 **{company}**: {date}\n"
        
        total_signals = len(forex_data) + len(options_data) + len(earnings_data)
        message += f"""
📊 *Live analysis from MyMama.uk*
🤖 Automated Alert System
📈 **{total_signals} active signals**
"""
        
        # Send to Telegram
        from telegram import Bot
        
        bot = Bot(token=bot_token)
        
        await bot.send_message(
            chat_id=group_id,
            text=message,
            parse_mode='Markdown'
        )
        
        logger.info("MyMama financial report sent to Telegram group successfully!")
        logger.info(f"Sent {total_signals} signals to the group (Forex: {len(forex_data)}, Options: {len(options_data)}, Earnings: {len(earnings_data)})")
        
        return True
        
    except Exception as e:
        logger.error(f"Error sending immediate report: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """Main function"""
    print("Sending immediate MyMama forex report to Telegram group...")
    
    success = await send_immediate_mymama_report()
    
    if success:
        print("Report sent successfully!")
    else:
        print("Failed to send report")
    
    return success

if __name__ == "__main__":
    asyncio.run(main())