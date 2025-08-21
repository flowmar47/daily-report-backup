#!/usr/bin/env python3
"""
Enhanced Daily Sender with Heatmap Integration
Sends regular MyMama alerts + interest rate heatmaps to both Signal and Telegram
"""

import asyncio
import os
import sys
import subprocess
import logging
from datetime import datetime
from pathlib import Path

# Add src directory to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from messengers.multi_messenger import MultiMessenger
from messenger_compatibility import SignalMessenger, TelegramMessenger
from src.config.settings import settings
from real_only_mymama_scraper import RealOnlyMyMamaScraper
from src.data_processors.template_generator import StructuredTemplateGenerator

logger = logging.getLogger(__name__)


class EnhancedDailySender:
    """Enhanced daily sender with heatmap integration"""
    
    def __init__(self):
        """Initialize the enhanced daily sender"""
        self.config = settings.config
        self.heatmap_path = os.path.join(os.path.dirname(__file__), 'heatmaps')
        self.multi_messenger = self._setup_messengers()
        self.scraper = RealOnlyMyMamaScraper()
        self.template_generator = StructuredTemplateGenerator()
        
    def _setup_messengers(self) -> MultiMessenger:
        """Setup multi-messenger with both platforms"""
        messengers = []
        
        # Setup Telegram messenger
        if self.config.get('telegram', {}).get('enabled', True):
            telegram_config = {
                'bot_token': os.getenv('TELEGRAM_BOT_TOKEN'),
                'chat_id': os.getenv('TELEGRAM_GROUP_ID'),
                'thread_id': os.getenv('TELEGRAM_THREAD_ID'),
                'enabled': True
            }
            messengers.append(TelegramMessenger(telegram_config))
        
        # Setup Signal messenger
        if self.config.get('signal', {}).get('enabled', True):
            signal_config = {
                'phone_number': os.getenv('SIGNAL_PHONE_NUMBER'),
                'group_id': os.getenv('SIGNAL_GROUP_ID'),
                'api_url': 'http://localhost:8080',
                'signal_cli_path': 'signal-cli',
                'enabled': True
            }
            messengers.append(SignalMessenger(signal_config))
        
        return MultiMessenger(messengers, {'concurrent_sends': True})
    
    def generate_heatmaps(self) -> dict:
        """Generate interest rate heatmaps"""
        logger.info("Generating interest rate heatmaps...")
        
        try:
            # Run the silent bloomberg system
            result = subprocess.run([
                sys.executable, 
                os.path.join(self.heatmap_path, 'silent_bloomberg_system.py')
            ], capture_output=True, text=True, cwd=self.heatmap_path)
            
            if result.returncode != 0:
                logger.error(f"Error generating heatmaps: {result.stderr}")
                return None
                
            # Parse the output
            output_lines = result.stdout.strip().split('\n')
            if len(output_lines) < 2:
                logger.error("Unexpected heatmap output format")
                return None
                
            # Extract paths from output
            categorical_path = None
            forex_path = None
            
            for line in output_lines:
                if 'categorical_heatmap.png' in line:
                    categorical_path = line.strip()
                elif 'forex_pairs_heatmap.png' in line:
                    forex_path = line.strip()
            
            return {
                'categorical_heatmap': categorical_path,
                'forex_heatmap': forex_path,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Exception during heatmap generation: {e}")
            return None
    
    async def scrape_mymama_data(self) -> dict:
        """Scrape MyMama data"""
        logger.info("Scraping MyMama data...")
        
        try:
            # Use the existing scraper
            data = await self.scraper.scrape_data()
            return data
        except Exception as e:
            logger.error(f"Error scraping MyMama data: {e}")
            return None
    
    async def send_daily_report(self):
        """Send complete daily report with heatmaps"""
        logger.info("Starting enhanced daily report...")
        
        # Test connections first
        connection_test = await self.multi_messenger.test_connection()
        if not connection_test:
            logger.error("No messaging platforms available")
            return False
        
        # Generate heatmaps
        heatmap_data = self.generate_heatmaps()
        if not heatmap_data:
            logger.warning("Failed to generate heatmaps, continuing without them")
        
        # Scrape MyMama data
        mymama_data = await self.scrape_mymama_data()
        if not mymama_data:
            logger.error("Failed to scrape MyMama data")
            if not heatmap_data:
                logger.error("Both MyMama and heatmap data failed - aborting")
                return False
        
        # Send MyMama alerts if available
        if mymama_data:
            try:
                # Generate structured template
                report_text = self.template_generator.generate_template(mymama_data)
                
                # Send main report
                result = await self.multi_messenger.send_message(
                    f"🏦 DAILY FINANCIAL ALERTS\n\n{report_text}"
                )
                
                if result.status.value == 'success':
                    logger.info("MyMama alerts sent successfully")
                else:
                    logger.warning(f"MyMama alerts partially sent: {result.error}")
                    
            except Exception as e:
                logger.error(f"Error sending MyMama alerts: {e}")
        
        # Send heatmaps if available
        if heatmap_data:
            try:
                # Send categorical heatmap
                if heatmap_data.get('categorical_heatmap') and os.path.exists(heatmap_data['categorical_heatmap']):
                    result = await self.multi_messenger.send_attachment(
                        heatmap_data['categorical_heatmap'],
                        "📊 Global Interest Rates - Categorical Analysis"
                    )
                    
                    if result.status.value == 'success':
                        logger.info("Categorical heatmap sent successfully")
                    else:
                        logger.warning(f"Categorical heatmap partially sent: {result.error}")
                
                # Send forex pairs heatmap
                if heatmap_data.get('forex_heatmap') and os.path.exists(heatmap_data['forex_heatmap']):
                    result = await self.multi_messenger.send_attachment(
                        heatmap_data['forex_heatmap'],
                        "🌍 Forex Pairs Differential Matrix"
                    )
                    
                    if result.status.value == 'success':
                        logger.info("Forex heatmap sent successfully")
                    else:
                        logger.warning(f"Forex heatmap partially sent: {result.error}")
                        
            except Exception as e:
                logger.error(f"Error sending heatmaps: {e}")
        
        logger.info("Enhanced daily report completed")
        return True
    
    async def test_heatmap_generation(self):
        """Test heatmap generation only"""
        logger.info("Testing heatmap generation...")
        
        heatmap_data = self.generate_heatmaps()
        if heatmap_data:
            logger.info("Heatmap generation successful:")
            logger.info(f"  Categorical: {heatmap_data.get('categorical_heatmap')}")
            logger.info(f"  Forex: {heatmap_data.get('forex_heatmap')}")
            return True
        else:
            logger.error("Heatmap generation failed")
            return False
    
    async def test_messaging(self):
        """Test messaging system"""
        logger.info("Testing messaging system...")
        
        connection_test = await self.multi_messenger.test_connection()
        if connection_test:
            logger.info("Messaging system operational")
            
            # Send test message
            result = await self.multi_messenger.send_message(
                "🧪 Enhanced Daily Sender Test \\- Messaging System Operational"
            )
            
            if result.status.value == 'success':
                logger.info("Test message sent successfully")
                return True
            else:
                logger.warning(f"Test message partially sent: {result.error}")
                return True  # Partial success is still success
        else:
            logger.error("Messaging system not available")
            return False


async def main():
    """Main function"""
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    sender = EnhancedDailySender()
    
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
        
        if command == 'test-heatmaps':
            success = await sender.test_heatmap_generation()
            sys.exit(0 if success else 1)
        elif command == 'test-messaging':
            success = await sender.test_messaging()
            sys.exit(0 if success else 1)
        elif command == 'test-all':
            heatmap_test = await sender.test_heatmap_generation()
            messaging_test = await sender.test_messaging()
            success = heatmap_test and messaging_test
            sys.exit(0 if success else 1)
    
    # Default: send daily report
    success = await sender.send_daily_report()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    asyncio.run(main())