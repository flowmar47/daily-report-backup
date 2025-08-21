#!/usr/bin/env python3
"""
Test authentication with the correct email address
"""
import asyncio
import logging
import os
from enhanced_browserbase_scraper import EnhancedBrowserBaseScraper
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_correct_email():
    """Test with verified correct email"""
    try:
        # Verify the credentials first
        username = os.getenv('MYMAMA_USERNAME')
        password = os.getenv('MYMAMA_PASSWORD')
        
        logger.info("🔍 Verifying credentials...")
        logger.info(f"📧 Email: {username}")
        logger.info(f"🔒 Password: {'*' * len(password) if password else 'NOT SET'}")
        
        if username != 'comfort.uncounted44@mailer.me':
            logger.error(f"❌ Email mismatch! Expected: comfort.uncounted44@mailer.me, Got: {username}")
            return
        
        logger.info("✅ Email verified as correct: comfort.uncounted44@mailer.me")
        
        # Now test the scraper
        logger.info("🚀 Testing enhanced scraper with correct email...")
        scraper = EnhancedBrowserBaseScraper()
        
        # Run a quick test
        result = await scraper.scrape_data()
        
        if result.get('success'):
            logger.info("✅ Scraping completed successfully!")
            
            # Check data
            forex_count = len(result.get('forex_alerts', []))
            options_count = len(result.get('options_alerts', []))
            swing_count = len(result.get('swing_trades', []))
            day_count = len(result.get('day_trades', []))
            
            logger.info(f"📊 Data extracted:")
            logger.info(f"  - Forex alerts: {forex_count}")
            logger.info(f"  - Options alerts: {options_count}")
            logger.info(f"  - Swing trades: {swing_count}")
            logger.info(f"  - Day trades: {day_count}")
            
            total_alerts = forex_count + options_count + swing_count + day_count
            
            if total_alerts > 0:
                logger.info("🎉 SUCCESS! Real trading data extracted!")
                
                # Send a quick success report
                from main import DailyReportAutomation
                automation = DailyReportAutomation()
                
                success_message = f"""✅ AUTHENTICATION SUCCESS!

Email correction resolved the login issue.

Real MyMama Data Extracted:
• Forex alerts: {forex_count}
• Options alerts: {options_count}  
• Swing trades: {swing_count}
• Day trades: {day_count}
• Total alerts: {total_alerts}

Enhanced BrowserBase scraper now fully operational with live data!"""

                await automation.send_telegram_report(success_message)
                await automation.send_signal_report(success_message)
                logger.info("📱 Success message sent to both platforms!")
                
            else:
                logger.info("📊 Authentication successful but no current trading data")
                
        else:
            logger.error(f"❌ Scraping failed: {result.get('error')}")
            
    except Exception as e:
        logger.error(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_correct_email())