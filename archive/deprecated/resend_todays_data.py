#!/usr/bin/env python3
"""
Resend Today's Financial Data
Emergency script to resend the financial data that failed to reach Telegram due to Unicode issues
"""

import asyncio
import json
import logging
from datetime import datetime
from pathlib import Path

# Import from the existing structure
try:
    from messengers.multi_messenger import send_to_both_messengers
    MESSENGER_AVAILABLE = True
except ImportError:
    try:
        # Try the unified messenger approach
        import sys
        sys.path.append('/home/ohms/OhmsAlertsReports/src/daily_report/messengers')
        from unified_messenger import send_structured_financial_data
        MESSENGER_AVAILABLE = True
    except ImportError:
        MESSENGER_AVAILABLE = False

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/resend_data.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class DataResender:
    """Emergency data resender for failed Telegram delivery"""
    
    def __init__(self):
        self.data_file = Path('real_alerts_only/real_alerts_20250702_060141.json')
        
    async def load_todays_data(self):
        """Load the extracted financial data from today's 6 AM run"""
        try:
            if not self.data_file.exists():
                logger.error(f"❌ Data file not found: {self.data_file}")
                return None
                
            with open(self.data_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            logger.info(f"✅ Loaded data with {len(data.get('forex_alerts', {}))} forex alerts, {len(data.get('options_data', []))} options")
            return data
            
        except Exception as e:
            logger.error(f"❌ Failed to load data: {e}")
            return None
    
    def format_structured_report(self, data):
        """Format the data into the required structured plaintext format"""
        try:
            template_generator = StructuredTemplateGenerator()
            
            # Format forex section
            forex_section = template_generator._format_forex_section(data.get('forex_alerts', {}))
            
            # Format options section
            options_section = template_generator._format_options_section(data.get('options_data', []))
            
            # Format swing trades section
            swing_section = template_generator._format_swing_trades_section(data.get('swing_trades', []))
            
            # Format day trades section
            day_section = template_generator._format_day_trades_section(data.get('day_trades', []))
            
            # Combine all sections
            report_parts = []
            
            if forex_section:
                report_parts.append(forex_section)
                
            if options_section:
                report_parts.append(options_section)
                
            if swing_section:
                report_parts.append(swing_section)
                
            if day_section:
                report_parts.append(day_section)
            
            # Add header and footer
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M PST")
            header = f"DAILY FINANCIAL ALERTS - {timestamp}"
            footer = "=" * 50
            
            full_report = f"{header}\n\n" + "\n\n".join(report_parts) + f"\n\n{footer}"
            
            logger.info(f"✅ Formatted report: {len(full_report)} characters")
            return full_report
            
        except Exception as e:
            logger.error(f"❌ Failed to format report: {e}")
            return None
    
    async def resend_data(self):
        """Resend the financial data with fixed Unicode encoding"""
        try:
            logger.info("🚀 Starting emergency data resend...")
            
            # Load the data
            data = await self.load_todays_data()
            if not data:
                return False
            
            # Format the report
            report = self.format_structured_report(data)
            if not report:
                return False
            
            # Initialize messenger (only Telegram and Signal)
            multi_messenger = UnifiedMultiMessenger(['telegram', 'signal'])
            
            logger.info("📤 Sending formatted report via unified messenger...")
            
            # Send to all platforms
            results = await multi_messenger.send_to_all(report)
            
            # Log results
            success_count = 0
            for platform, result in results.items():
                if result.success:
                    logger.info(f"✅ {platform.upper()}: Message sent successfully (ID: {result.message_id})")
                    success_count += 1
                else:
                    logger.error(f"❌ {platform.upper()}: Failed - {result.error}")
            
            logger.info(f"📊 DELIVERY SUMMARY: {success_count}/{len(results)} platforms successful")
            
            # Cleanup
            await multi_messenger.cleanup()
            
            return success_count == len(results)
            
        except Exception as e:
            logger.error(f"❌ Emergency resend failed: {e}")
            return False

async def main():
    """Main execution function"""
    logger.info("=" * 60)
    logger.info("EMERGENCY DATA RESEND - Fixing Telegram Unicode Issues")
    logger.info("=" * 60)
    
    resender = DataResender()
    success = await resender.resend_data()
    
    if success:
        logger.info("✅ Emergency resend completed successfully!")
    else:
        logger.error("❌ Emergency resend failed - check logs for details")
    
    logger.info("=" * 60)

if __name__ == "__main__":
    asyncio.run(main())