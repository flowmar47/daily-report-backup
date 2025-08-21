#!/usr/bin/env python3
"""
Unified Messaging Test Suite
Comprehensive testing for all messaging platforms without sending production messages
"""

import asyncio
import logging
import sys
import json
import os
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List, Optional

# Add paths for imports
sys.path.append(str(Path(__file__).parent / 'src'))
sys.path.append(str(Path(__file__).parent / 'src' / 'messengers'))

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class UnifiedMessagingTestSuite:
    """Comprehensive test suite for all messaging platforms"""
    
    def __init__(self):
        self.test_results = []
        self.test_start_time = datetime.now()
        
    async def run_all_tests(self):
        """Run all messaging tests"""
        logger.info("🧪 Starting Unified Messaging Test Suite")
        logger.info("🚨 DRY RUN MODE - No messages will be sent to production platforms")
        
        # Test 1: Environment and Configuration
        await self.test_environment_setup()
        
        # Test 2: Import and Module Tests
        await self.test_imports_and_modules()
        
        # Test 3: Signal Infrastructure Tests
        await self.test_signal_infrastructure()
        
        # Test 4: Telegram Infrastructure Tests  
        await self.test_telegram_infrastructure()
        
        # Test 5: WhatsApp Infrastructure Tests
        await self.test_whatsapp_infrastructure()
        
        # Test 6: Unified Messenger Tests
        await self.test_unified_messenger()
        
        # Test 7: Error Handling Tests
        await self.test_error_handling()
        
        # Test 8: Message Formatting Tests
        await self.test_message_formatting()
        
        # Test 9: Platform Health Checks
        await self.test_platform_health_checks()
        
        # Print summary
        self.print_test_summary()
    
    async def test_environment_setup(self):
        """Test 1: Environment and configuration setup"""
        logger.info("\n=== Test 1: Environment Setup ===")
        
        try:
            from utils.env_config import EnvironmentConfig
            
            # Test environment loading
            env_config = EnvironmentConfig('daily_report')
            credentials = env_config.get_all_vars()
            
            # Check Signal credentials
            signal_phone = credentials.get('SIGNAL_PHONE_NUMBER')
            signal_group = credentials.get('SIGNAL_GROUP_ID')
            signal_api = credentials.get('SIGNAL_API_URL', 'http://localhost:8080')
            
            # Check Telegram credentials
            telegram_token = credentials.get('TELEGRAM_BOT_TOKEN')
            telegram_group = credentials.get('TELEGRAM_GROUP_ID')
            
            # Check WhatsApp credentials (optional)
            whatsapp_phone = credentials.get('WHATSAPP_PHONE_NUMBER')
            whatsapp_groups = credentials.get('WHATSAPP_GROUP_NAMES')
            
            # Validate required credentials
            signal_ok = signal_phone and signal_group
            telegram_ok = telegram_token and telegram_group
            whatsapp_ok = whatsapp_phone and whatsapp_groups
            
            logger.info(f"Signal credentials: {'✅' if signal_ok else '❌'}")
            logger.info(f"Telegram credentials: {'✅' if telegram_ok else '❌'}")
            logger.info(f"WhatsApp credentials: {'✅' if whatsapp_ok else '⚠️ Optional'}")
            
            self.record_test("Environment Setup", signal_ok and telegram_ok)
            
        except Exception as e:
            logger.error(f"❌ Environment setup failed: {e}")
            self.record_test("Environment Setup", False)
    
    async def test_imports_and_modules(self):
        """Test 2: Import and module availability"""
        logger.info("\n=== Test 2: Import and Module Tests ===")
        
        # Test core imports
        try:
            from messengers.unified_messenger import UnifiedMultiMessenger, UnifiedSignalMessenger, UnifiedTelegramMessenger
            logger.info("✅ Core messenger imports successful")
            core_imports_ok = True
        except Exception as e:
            logger.error(f"❌ Core messenger imports failed: {e}")
            core_imports_ok = False
        
        # Test httpx availability (for Signal/Telegram)
        try:
            import httpx
            logger.info("✅ httpx available for HTTP messaging")
            httpx_ok = True
        except ImportError:
            logger.error("❌ httpx not available")
            httpx_ok = False
        
        # Test Playwright availability (for WhatsApp)
        try:
            from playwright.async_api import async_playwright
            logger.info("✅ Playwright available for WhatsApp")
            playwright_ok = True
        except ImportError:
            logger.warning("⚠️ Playwright not available - WhatsApp will use Selenium fallback")
            playwright_ok = False
        
        # Test Selenium availability (WhatsApp fallback)
        try:
            from selenium import webdriver
            logger.info("✅ Selenium available as WhatsApp fallback")
            selenium_ok = True
        except ImportError:
            logger.warning("⚠️ Selenium not available")
            selenium_ok = False
        
        self.record_test("Core Imports", core_imports_ok)
        self.record_test("HTTP Client", httpx_ok)
        self.record_test("Browser Automation", playwright_ok or selenium_ok)
    
    async def test_signal_infrastructure(self):
        """Test 3: Signal infrastructure tests"""
        logger.info("\n=== Test 3: Signal Infrastructure ===")
        
        try:
            import httpx
            
            # Test Signal API connectivity (read-only)
            async with httpx.AsyncClient(timeout=10.0) as client:
                try:
                    response = await client.get('http://localhost:8080/v1/about')
                    if response.status_code == 200:
                        api_info = response.json()
                        logger.info(f"✅ Signal API responding: version {api_info.get('version')}")
                        signal_api_ok = True
                    else:
                        logger.error(f"❌ Signal API returned status {response.status_code}")
                        signal_api_ok = False
                except Exception as e:
                    logger.error(f"❌ Signal API not reachable: {e}")
                    signal_api_ok = False
                
                # Test accounts endpoint (read-only)
                try:
                    response = await client.get('http://localhost:8080/v1/accounts')
                    if response.status_code == 200:
                        accounts = response.json()
                        logger.info(f"✅ Signal accounts endpoint working: {len(accounts)} accounts")
                        accounts_ok = True
                    else:
                        logger.error(f"❌ Signal accounts endpoint failed: {response.status_code}")
                        accounts_ok = False
                except Exception as e:
                    logger.error(f"❌ Signal accounts check failed: {e}")
                    accounts_ok = False
            
            self.record_test("Signal API Connectivity", signal_api_ok)
            self.record_test("Signal Accounts", accounts_ok)
            
        except Exception as e:
            logger.error(f"❌ Signal infrastructure test failed: {e}")
            self.record_test("Signal Infrastructure", False)
    
    async def test_telegram_infrastructure(self):
        """Test 4: Telegram infrastructure tests"""
        logger.info("\n=== Test 4: Telegram Infrastructure ===")
        
        try:
            from utils.env_config import EnvironmentConfig
            import httpx
            
            env_config = EnvironmentConfig('daily_report')
            credentials = env_config.get_all_vars()
            
            bot_token = credentials.get('TELEGRAM_BOT_TOKEN')
            if not bot_token:
                logger.error("❌ Telegram bot token not configured")
                self.record_test("Telegram Infrastructure", False)
                return
            
            # Test Telegram API connectivity (read-only)
            api_url = f"https://api.telegram.org/bot{bot_token}"
            
            async with httpx.AsyncClient(timeout=10.0) as client:
                try:
                    response = await client.get(f"{api_url}/getMe")
                    if response.status_code == 200:
                        bot_info = response.json()
                        if bot_info.get('ok'):
                            bot_data = bot_info['result']
                            logger.info(f"✅ Telegram bot responding: @{bot_data.get('username')}")
                            telegram_ok = True
                        else:
                            logger.error(f"❌ Telegram API error: {bot_info.get('description')}")
                            telegram_ok = False
                    else:
                        logger.error(f"❌ Telegram API returned status {response.status_code}")
                        telegram_ok = False
                except Exception as e:
                    logger.error(f"❌ Telegram API not reachable: {e}")
                    telegram_ok = False
            
            self.record_test("Telegram API Connectivity", telegram_ok)
            
        except Exception as e:
            logger.error(f"❌ Telegram infrastructure test failed: {e}")
            self.record_test("Telegram Infrastructure", False)
    
    async def test_whatsapp_infrastructure(self):
        """Test 5: WhatsApp infrastructure tests"""
        logger.info("\n=== Test 5: WhatsApp Infrastructure ===")
        
        # Test browser automation availability
        playwright_available = False
        selenium_available = False
        
        try:
            from playwright.async_api import async_playwright
            playwright_available = True
            logger.info("✅ Playwright available for WhatsApp")
        except ImportError:
            logger.info("ℹ️ Playwright not available")
        
        try:
            from selenium import webdriver
            selenium_available = True
            logger.info("✅ Selenium available for WhatsApp")
        except ImportError:
            logger.info("ℹ️ Selenium not available")
        
        # Test session directory creation
        try:
            session_path = Path(__file__).parent / 'browser_sessions' / 'whatsapp_test'
            session_path.mkdir(parents=True, exist_ok=True)
            
            # Test write permissions
            test_file = session_path / 'test.txt'
            test_file.write_text('test')
            test_file.unlink()
            
            logger.info("✅ WhatsApp session directory writable")
            session_ok = True
        except Exception as e:
            logger.error(f"❌ WhatsApp session directory test failed: {e}")
            session_ok = False
        
        self.record_test("WhatsApp Browser Automation", playwright_available or selenium_available)
        self.record_test("WhatsApp Session Management", session_ok)
    
    async def test_unified_messenger(self):
        """Test 6: Unified messenger initialization"""
        logger.info("\n=== Test 6: Unified Messenger Tests ===")
        
        try:
            from messengers.unified_messenger import UnifiedMultiMessenger
            
            # Test initialization without actually sending messages
            logger.info("Testing Telegram + Signal initialization...")
            multi_messenger = UnifiedMultiMessenger(['telegram', 'signal'])
            
            if 'telegram' in multi_messenger.messengers:
                logger.info("✅ Telegram messenger initialized")
                telegram_init_ok = True
            else:
                logger.error("❌ Telegram messenger failed to initialize")
                telegram_init_ok = False
            
            if 'signal' in multi_messenger.messengers:
                logger.info("✅ Signal messenger initialized")
                signal_init_ok = True
            else:
                logger.error("❌ Signal messenger failed to initialize")
                signal_init_ok = False
            
            # Test WhatsApp initialization (if configured)
            logger.info("Testing WhatsApp initialization...")
            try:
                whatsapp_messenger = UnifiedMultiMessenger(['whatsapp'])
                if 'whatsapp' in whatsapp_messenger.messengers:
                    logger.info("✅ WhatsApp messenger initialized")
                    whatsapp_init_ok = True
                else:
                    logger.info("ℹ️ WhatsApp messenger not configured")
                    whatsapp_init_ok = True  # Not required
                await whatsapp_messenger.cleanup()
            except Exception as e:
                logger.info(f"ℹ️ WhatsApp initialization skipped: {e}")
                whatsapp_init_ok = True  # Not required
            
            await multi_messenger.cleanup()
            
            self.record_test("Unified Messenger Init", telegram_init_ok and signal_init_ok)
            
        except Exception as e:
            logger.error(f"❌ Unified messenger test failed: {e}")
            self.record_test("Unified Messenger", False)
    
    async def test_error_handling(self):
        """Test 7: Error handling and resilience"""
        logger.info("\n=== Test 7: Error Handling Tests ===")
        
        try:
            from enhanced_error_handler import EnhancedErrorHandler, ErrorContext, ErrorSeverity, ErrorCategory
            
            # Test error handler initialization
            error_handler = EnhancedErrorHandler({})
            logger.info("✅ Error handler initializes correctly")
            
            # Test error context creation
            error_context = ErrorContext(
                operation="test_operation",
                component="test_component",
                severity=ErrorSeverity.LOW,
                category=ErrorCategory.UNKNOWN
            )
            logger.info("✅ Error context creation works")
            
            # Test error recording (without actual error)
            test_error = Exception("Test error - this is intentional")
            await error_handler.handle_error(test_error, error_context)
            logger.info("✅ Error handling mechanism works")
            
            self.record_test("Error Handling", True)
            
        except Exception as e:
            logger.error(f"❌ Error handling test failed: {e}")
            self.record_test("Error Handling", False)
    
    async def test_message_formatting(self):
        """Test 8: Message formatting and validation"""
        logger.info("\n=== Test 8: Message Formatting Tests ===")
        
        try:
            # Test structured financial data format
            test_data = """FOREX PAIRS

Pair: EURUSD
High: 1.1158
Average: 1.0742
Low: 1.0238
MT4 Action: MT4 SELL
Exit: 1.0850

EQUITIES AND OPTIONS

Symbol: QQQ
52 Week High: 480.92
52 Week Low: 478.13
Strike Price:

CALL > 521.68

PUT < N/A
Status: TRADE IN PROFIT"""
            
            # Test message length constraints
            if len(test_data) < 4096:  # Telegram limit
                logger.info("✅ Message within Telegram length limits")
                telegram_format_ok = True
            else:
                logger.warning("⚠️ Message exceeds Telegram length limits")
                telegram_format_ok = False
            
            if len(test_data) < 2000:  # Conservative Signal limit
                logger.info("✅ Message within Signal length limits")
                signal_format_ok = True
            else:
                logger.warning("⚠️ Message exceeds Signal length limits")
                signal_format_ok = False
            
            # Test line breaks and formatting
            lines = test_data.split('\n')
            if len(lines) > 1:
                logger.info(f"✅ Multi-line formatting: {len(lines)} lines")
                formatting_ok = True
            else:
                logger.error("❌ Multi-line formatting failed")
                formatting_ok = False
            
            # Test no emojis requirement
            emoji_found = any(ord(char) > 127 for char in test_data if ord(char) > 255)
            if not emoji_found:
                logger.info("✅ No emojis found - complies with plaintext requirement")
                emoji_ok = True
            else:
                logger.warning("⚠️ Emojis detected - should use plaintext only")
                emoji_ok = False
            
            self.record_test("Message Formatting", telegram_format_ok and signal_format_ok and formatting_ok and emoji_ok)
            
        except Exception as e:
            logger.error(f"❌ Message formatting test failed: {e}")
            self.record_test("Message Formatting", False)
    
    async def test_platform_health_checks(self):
        """Test 9: Platform health check capabilities"""
        logger.info("\n=== Test 9: Platform Health Checks ===")
        
        try:
            # Test health check methods exist and are callable
            from messengers.unified_messenger import UnifiedMultiMessenger
            
            multi_messenger = UnifiedMultiMessenger(['telegram', 'signal'])
            
            # Check if messengers have health check capabilities
            health_checks_available = 0
            total_messengers = len(multi_messenger.messengers)
            
            for platform, messenger in multi_messenger.messengers.items():
                if hasattr(messenger, 'health_check'):
                    logger.info(f"✅ {platform} has health check capability")
                    health_checks_available += 1
                else:
                    logger.info(f"ℹ️ {platform} no health check method")
            
            await multi_messenger.cleanup()
            
            health_check_ok = health_checks_available > 0
            logger.info(f"Health checks available: {health_checks_available}/{total_messengers}")
            
            self.record_test("Platform Health Checks", health_check_ok)
            
        except Exception as e:
            logger.error(f"❌ Platform health check test failed: {e}")
            self.record_test("Platform Health Checks", False)
    
    def record_test(self, test_name: str, passed: bool):
        """Record test result"""
        self.test_results.append((test_name, passed))
    
    def print_test_summary(self):
        """Print comprehensive test summary"""
        logger.info("\n" + "="*60)
        logger.info("🧪 UNIFIED MESSAGING TEST SUITE SUMMARY")
        logger.info("="*60)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for _, passed in self.test_results if passed)
        
        for test_name, passed in self.test_results:
            status = "✅ PASS" if passed else "❌ FAIL"
            logger.info(f"{test_name:.<40} {status}")
        
        logger.info("-" * 60)
        logger.info(f"Total Tests: {total_tests}")
        logger.info(f"Passed: {passed_tests}")
        logger.info(f"Failed: {total_tests - passed_tests}")
        logger.info(f"Success Rate: {(passed_tests/total_tests*100):.1f}%")
        
        test_duration = datetime.now() - self.test_start_time
        logger.info(f"Test Duration: {test_duration.total_seconds():.2f} seconds")
        
        if passed_tests == total_tests:
            logger.info("\n🎉 ALL TESTS PASSED - Messaging system is ready!")
        elif passed_tests >= total_tests * 0.8:
            logger.info("\n✅ Most tests passed - System mostly functional")
        else:
            logger.info("\n⚠️ Multiple test failures - Review configuration")
        
        logger.info("\n📋 NEXT STEPS:")
        if passed_tests < total_tests:
            logger.info("1. Review failed tests and fix configuration issues")
            logger.info("2. Install missing dependencies (Playwright, etc.)")
            logger.info("3. Verify API credentials and connectivity")
        logger.info("4. Test with dry-run before enabling production messaging")
        logger.info("5. Monitor logs during first production runs")

async def main():
    """Run the unified messaging test suite"""
    test_suite = UnifiedMessagingTestSuite()
    await test_suite.run_all_tests()

if __name__ == "__main__":
    asyncio.run(main())