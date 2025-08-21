#!/usr/bin/env python3
"""
Send Real MyMama Alerts to Telegram Group
Only sends if real data can be successfully parsed
"""
import asyncio
import os
import sys
import logging
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

async def send_real_alerts():
    """Get real MyMama alerts and send to Telegram if parsing successful"""
    
    logger.info("🚀 Starting Real MyMama Alerts to Telegram process...")
    
    try:
        # Import real-only scraper
        from real_only_mymama_scraper import RealOnlyMyMamaScraper
        
        # Get real alerts data
        scraper = RealOnlyMyMamaScraper()
        alerts_data = await scraper.get_real_alerts_only()
        
        if not alerts_data['has_real_data']:
            logger.warning("⚠️ No real alerts data available - NOT sending to Telegram")
            logger.info(f"📋 Reason: {alerts_data.get('message', 'Unknown')}")
            return False
        
        # Format for Telegram
        message = format_telegram_message(alerts_data)
        
        # Send to Telegram
        success = await send_to_telegram(message)
        
        if success:
            logger.info("✅ Real MyMama alerts sent to Telegram successfully!")
            
            # Log summary
            forex_count = len(alerts_data.get('forex_alerts', {}))
            options_count = len(alerts_data.get('options_data', []))
            earnings_count = len(alerts_data.get('earnings_releases', []))
            swing_count = len(alerts_data.get('swing_trades', []))
            day_count = len(alerts_data.get('day_trades', []))
            logger.info(f"📊 Sent: {forex_count} forex, {options_count} options, {earnings_count} earnings, {swing_count} swing trades, {day_count} day trades")
            
            return True
        else:
            logger.error("❌ Failed to send alerts to Telegram")
            return False
            
    except Exception as e:
        logger.error(f"❌ Error in send_real_alerts: {e}")
        import traceback
        traceback.print_exc()
        return False

def format_telegram_message(alerts_data):
    """Format alerts data for Telegram"""
    
    from datetime import datetime
    
    message_parts = []
    
    # Header
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')
    message_parts.append("🚨 **FINANCIAL ALERTS** 🚨")
    message_parts.append(f"📅 {timestamp}")
    message_parts.append("")
    
    # Forex alerts
    forex_alerts = alerts_data.get('forex_alerts', {})
    if forex_alerts:
        message_parts.append("💱 **FOREX SIGNALS:**")
        message_parts.append("```")
        
        for pair, data in forex_alerts.items():
            signal = data.get('signal', 'N/A')
            entry = data.get('entry', 'N/A')
            exit_price = data.get('exit', 'N/A')
            high = data.get('high', 'N/A')
            low = data.get('low', 'N/A')
            
            message_parts.append(f"{pair}: {signal}")
            message_parts.append(f"  Entry:  {entry}")
            message_parts.append(f"  Exit:   {exit_price}")
            message_parts.append(f"  High:   {high}")
            message_parts.append(f"  Low:    {low}")
            message_parts.append("")
        
        message_parts.append("```")
    
    # Options data
    options_data = alerts_data.get('options_data', [])
    if options_data:
        message_parts.append("📊 **OPTIONS DATA:**")
        message_parts.append("```")
        
        for option in options_data:
            ticker = option.get('ticker', 'N/A')
            high_52week = option.get('high_52week', 'N/A')
            low_52week = option.get('low_52week', 'N/A')
            call_strike = option.get('call_strike', 'N/A')
            put_strike = option.get('put_strike', 'N/A')
            status = option.get('status', 'N/A')
            
            message_parts.append(f"{ticker}:")
            message_parts.append(f"  52W High: {high_52week}")
            message_parts.append(f"  52W Low:  {low_52week}")
            message_parts.append(f"  CALL >:   {call_strike}")
            message_parts.append(f"  PUT <:    {put_strike}")
            message_parts.append(f"  Status:   {status}")
            message_parts.append("")
        
        message_parts.append("```")
    
    # Earnings releases
    earnings_data = alerts_data.get('earnings_releases', [])
    if earnings_data:
        message_parts.append("📈 **EARNINGS RELEASES:**")
        message_parts.append("```")
        
        for earning in earnings_data:
            company = earning.get('company', 'N/A')
            ticker = earning.get('ticker', 'N/A')
            price = earning.get('current_price', 'N/A')
            date = earning.get('earnings_date', 'N/A')
            rationale = earning.get('rationale', 'N/A')
            
            message_parts.append(f"{ticker} ({company}):")
            message_parts.append(f"  Price:     {price}")
            message_parts.append(f"  Date:      {date}")
            message_parts.append(f"  Rationale: {rationale}")
            message_parts.append("")
        
        message_parts.append("```")
    
    # Swing trades
    swing_trades = alerts_data.get('swing_trades', [])
    if swing_trades:
        message_parts.append("📊 **SWING TRADES:**")
        message_parts.append("```")
        
        for trade in swing_trades:
            company = trade.get('company', 'N/A')
            ticker = trade.get('ticker', 'N/A')
            price = trade.get('current_price', 'N/A')
            date = trade.get('earnings_date', 'N/A')
            rationale = trade.get('rationale', 'N/A')
            
            message_parts.append(f"{ticker} ({company}):")
            message_parts.append(f"  Price:     {price}")
            message_parts.append(f"  Date:      {date}")
            message_parts.append(f"  Rationale: {rationale}")
            message_parts.append("")
        
        message_parts.append("```")
    
    # Day trades
    day_trades = alerts_data.get('day_trades', [])
    if day_trades:
        message_parts.append("⚡ **DAY TRADES:**")
        message_parts.append("```")
        
        for trade in day_trades:
            company = trade.get('company', 'N/A')
            ticker = trade.get('ticker', 'N/A')
            price = trade.get('current_price', 'N/A')
            date = trade.get('earnings_date', 'N/A')
            rationale = trade.get('rationale', 'N/A')
            
            message_parts.append(f"{ticker} ({company}):")
            message_parts.append(f"  Price:     {price}")
            message_parts.append(f"  Date:      {date}")
            message_parts.append(f"  Rationale: {rationale}")
            message_parts.append("")
        
        message_parts.append("```")
    
    # Footer
    # Removed "Real data only" line as requested
    
    return "\n".join(message_parts)

async def send_to_telegram(message):
    """Send message to Telegram group"""
    
    try:
        bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
        group_id = os.getenv('TELEGRAM_GROUP_ID')
        
        if not bot_token or not group_id:
            logger.error("❌ Missing Telegram credentials")
            return False
        
        import aiohttp
        
        url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        
        payload = {
            'chat_id': group_id,
            'text': message,
            'parse_mode': 'Markdown',
            'disable_web_page_preview': True
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload) as response:
                if response.status == 200:
                    logger.info("✅ Message sent to Telegram successfully")
                    return True
                else:
                    error_text = await response.text()
                    logger.error(f"❌ Telegram API error: {response.status} - {error_text}")
                    return False
                    
    except Exception as e:
        logger.error(f"❌ Error sending to Telegram: {e}")
        return False

async def main():
    """Main function"""
    print("🎯 Real MyMama Alerts to Telegram")
    print("=" * 50)
    
    success = await send_real_alerts()
    
    if success:
        print("✅ SUCCESS: Real alerts sent to Telegram group")
    else:
        print("❌ FAILED: No real alerts sent")
        print("💡 Possible reasons:")
        print("   - No real MyMama data available")
        print("   - Parsing failed")
        print("   - Telegram sending failed")
        print("   - Authentication issues")
    
    print("=" * 50)
    return success

if __name__ == "__main__":
    result = asyncio.run(main())