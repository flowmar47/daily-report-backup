#!/usr/bin/env python3
"""
Comprehensive System Test
Tests all major components of the OhmsAlertsReports system
"""

import asyncio
import logging
import sys
from pathlib import Path
from datetime import datetime

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class SystemTester:
    """Comprehensive system testing class"""
    
    def __init__(self):
        self.test_results = {}
        self.start_time = datetime.now()
    
    async def test_imports(self):
        """Test all critical imports"""
        logger.info("🧪 Testing critical imports...")
        
        try:
            # Test scraper imports
            from real_only_mymama_scraper import RealOnlyMyMamaScraper
            logger.info("✅ RealOnlyMyMamaScraper import successful")
            self.test_results['scraper_import'] = True
            
            # Test messenger imports
            from messenger_compatibility import TelegramMessenger, SignalMessenger
            logger.info("✅ Messenger imports successful")
            self.test_results['messenger_import'] = True
            
            # Test main automation
            from main import DailyReportAutomation
            logger.info("✅ Main automation import successful")
            self.test_results['automation_import'] = True
            
        except Exception as e:
            logger.error(f"❌ Import test failed: {e}")
            self.test_results['imports'] = False
            return False
        
        return True
    
    async def test_scraper_initialization(self):
        """Test scraper initialization"""
        logger.info("🧪 Testing scraper initialization...")
        
        try:
            from real_only_mymama_scraper import RealOnlyMyMamaScraper
            scraper = RealOnlyMyMamaScraper()
            logger.info("✅ Scraper initialization successful")
            self.test_results['scraper_init'] = True
            return True
        except Exception as e:
            logger.error(f"❌ Scraper initialization failed: {e}")
            self.test_results['scraper_init'] = False
            return False
    
    async def test_messenger_initialization(self):
        """Test messenger initialization"""
        logger.info("🧪 Testing messenger initialization...")
        
        try:
            from messenger_compatibility import TelegramMessenger, SignalMessenger
            
            # Test Telegram
            telegram = TelegramMessenger()
            logger.info("✅ Telegram messenger initialization successful")
            self.test_results['telegram_init'] = True
            
            # Test Signal
            signal = SignalMessenger()
            logger.info("✅ Signal messenger initialization successful")
            self.test_results['signal_init'] = True
            
            return True
        except Exception as e:
            logger.error(f"❌ Messenger initialization failed: {e}")
            self.test_results['messenger_init'] = False
            return False
    
    async def test_configuration(self):
        """Test configuration loading"""
        logger.info("🧪 Testing configuration...")
        
        try:
            import json
            with open('config.json', 'r') as f:
                config = json.load(f)
            
            required_keys = ['app_settings', 'scraping', 'telegram', 'data_retention']
            for key in required_keys:
                if key not in config:
                    raise ValueError(f"Missing required config key: {key}")
            
            logger.info("✅ Configuration loading successful")
            self.test_results['config'] = True
            return True
        except Exception as e:
            logger.error(f"❌ Configuration test failed: {e}")
            self.test_results['config'] = False
            return False
    
    async def test_environment_variables(self):
        """Test environment variables"""
        logger.info("🧪 Testing environment variables...")
        
        try:
            import os
            from dotenv import load_dotenv
            load_dotenv()
            
            required_vars = [
                'MYMAMA_USERNAME',
                'MYMAMA_PASSWORD',
                'TELEGRAM_BOT_TOKEN',
                'TELEGRAM_GROUP_ID',
                'SIGNAL_PHONE_NUMBER',
                'SIGNAL_GROUP_ID'
            ]
            
            missing_vars = []
            for var in required_vars:
                if not os.getenv(var):
                    missing_vars.append(var)
            
            if missing_vars:
                raise ValueError(f"Missing environment variables: {missing_vars}")
            
            logger.info("✅ Environment variables check successful")
            self.test_results['env_vars'] = True
            return True
        except Exception as e:
            logger.error(f"❌ Environment variables test failed: {e}")
            self.test_results['env_vars'] = False
            return False
    
    async def test_service_status(self):
        """Test systemd service status"""
        logger.info("🧪 Testing systemd service status...")
        
        try:
            import subprocess
            result = subprocess.run(
                ['systemctl', 'is-active', 'daily-financial-report.service'],
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0 and result.stdout.strip() == 'active':
                logger.info("✅ Systemd service is active")
                self.test_results['service_status'] = True
                return True
            else:
                logger.warning("⚠️ Systemd service is not active")
                self.test_results['service_status'] = False
                return False
        except Exception as e:
            logger.error(f"❌ Service status test failed: {e}")
            self.test_results['service_status'] = False
            return False
    
    async def test_scheduled_time(self):
        """Test if current time matches scheduled time"""
        logger.info("🧪 Testing scheduled time configuration...")
        
        try:
            import json
            with open('config.json', 'r') as f:
                config = json.load(f)
            
            report_time = config['app_settings']['report_time']
            report_days = config['app_settings']['report_days']
            
            current_time = datetime.now()
            current_day = current_time.strftime('%A').lower()
            
            logger.info(f"📅 Scheduled time: {report_time} on {', '.join(report_days)}")
            logger.info(f"📅 Current time: {current_time.strftime('%H:%M')} on {current_day}")
            
            if current_day in report_days:
                logger.info("✅ Current day is in scheduled days")
                self.test_results['scheduled_time'] = True
                return True
            else:
                logger.info("ℹ️ Current day is not in scheduled days (normal)")
                self.test_results['scheduled_time'] = True
                return True
        except Exception as e:
            logger.error(f"❌ Scheduled time test failed: {e}")
            self.test_results['scheduled_time'] = False
            return False
    
    async def run_all_tests(self):
        """Run all system tests"""
        logger.info("🚀 Starting comprehensive system test...")
        logger.info("=" * 60)
        
        tests = [
            ('imports', self.test_imports),
            ('scraper_init', self.test_scraper_initialization),
            ('messenger_init', self.test_messenger_initialization),
            ('config', self.test_configuration),
            ('env_vars', self.test_environment_variables),
            ('service_status', self.test_service_status),
            ('scheduled_time', self.test_scheduled_time),
        ]
        
        for test_name, test_func in tests:
            try:
                await test_func()
            except Exception as e:
                logger.error(f"❌ Test {test_name} failed with exception: {e}")
                self.test_results[test_name] = False
        
        # Generate summary
        self.generate_summary()
    
    def generate_summary(self):
        """Generate test summary"""
        logger.info("=" * 60)
        logger.info("📊 SYSTEM TEST SUMMARY")
        logger.info("=" * 60)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results.values() if result)
        failed_tests = total_tests - passed_tests
        
        logger.info(f"Total tests: {total_tests}")
        logger.info(f"Passed: {passed_tests}")
        logger.info(f"Failed: {failed_tests}")
        logger.info(f"Success rate: {(passed_tests/total_tests)*100:.1f}%")
        
        if failed_tests > 0:
            logger.info("\n❌ Failed tests:")
            for test_name, result in self.test_results.items():
                if not result:
                    logger.info(f"  - {test_name}")
        else:
            logger.info("\n✅ All tests passed!")
        
        logger.info(f"\n⏱️ Test duration: {datetime.now() - self.start_time}")
        
        if failed_tests == 0:
            logger.info("\n🎉 System is ready for production!")
        else:
            logger.info("\n⚠️ System needs attention before production use")

async def main():
    """Main test function"""
    tester = SystemTester()
    await tester.run_all_tests()

if __name__ == "__main__":
    asyncio.run(main()) 