"""
Comprehensive Test Suite for Daily Financial Report Automation
"""

import unittest
import json
import tempfile
import os
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path
import asyncio

# Import modules to test
try:
    from utils import ForexParser, ReportFormatter, ValidationHelper
    from security_utils import DataSanitizer, RateLimiter, HeaderManager
    from config_manager import ConfigManager, ConfigValidator
    from error_handler import ErrorHandler, resilient_operation
except ImportError as e:
    print(f"Warning: Could not import some modules for testing: {e}")

class TestForexParser(unittest.TestCase):
    """Test ForexParser functionality"""
    
    def setUp(self):
        self.parser = ForexParser()
        self.sample_text = """
        EURUSD SELL at 1.0850
        GBPUSD strong BUY signal at 1.2650
        USDJPY neutral range trading
        """
        
    def test_extract_forex_signals_from_text(self):
        """Test extracting forex signals from text"""
        signals = self.parser.extract_forex_signals(self.sample_text)
        
        self.assertIsInstance(signals, dict)
        self.assertIn('EURUSD', signals)
        self.assertIn('GBPUSD', signals)
        
        # Check signal details
        if 'EURUSD' in signals:
            self.assertEqual(signals['EURUSD']['signal'], 'SELL')
            self.assertIn('price', signals['EURUSD'])
    
    def test_determine_signal(self):
        """Test signal determination from text"""
        self.assertEqual(self.parser._determine_signal("Strong BUY signal"), "BUY")
        self.assertEqual(self.parser._determine_signal("SELL immediately"), "SELL")
        self.assertEqual(self.parser._determine_signal("neutral outlook"), "NEUTRAL")
        self.assertIsNone(self.parser._determine_signal("no clear direction"))
    
    def test_extract_price(self):
        """Test price extraction from text"""
        self.assertEqual(self.parser._extract_price("EURUSD at 1.0850"), "1.0850")
        self.assertEqual(self.parser._extract_price("price: 148.25"), "148.25")
        self.assertIsNotNone(self.parser._extract_price("@ 0.6750"))
    
    def test_validate_price(self):
        """Test price validation"""
        self.assertTrue(self.parser._validate_price("1.0850", "EURUSD"))
        self.assertTrue(self.parser._validate_price("148.25", "USDJPY"))
        self.assertFalse(self.parser._validate_price("999.99", "EURUSD"))
        self.assertFalse(self.parser._validate_price("invalid", "EURUSD"))


class TestReportFormatter(unittest.TestCase):
    """Test ReportFormatter functionality"""
    
    def setUp(self):
        self.formatter = ReportFormatter()
        self.sample_data = {
            'forex_data': {
                'EURUSD': {'signal': 'BUY', 'price': '1.0850'},
                'GBPUSD': {'signal': 'SELL', 'price': '1.2650'}
            },
            'options_data': [
                {
                    'ticker': 'SPY',
                    'high_52week': '450.00',
                    'low_52week': '380.00',
                    'call_strike': '420.00',
                    'status': 'ACTIVE'
                }
            ]
        }
    
    def test_format_forex_section(self):
        """Test forex section formatting"""
        section = self.formatter._format_forex_section(self.sample_data['forex_data'])
        
        self.assertIsInstance(section, str)
        self.assertIn('EURUSD', section)
        self.assertIn('BUY', section)
        self.assertIn('GBPUSD', section)
        self.assertIn('SELL', section)
    
    def test_format_options_section(self):
        """Test options section formatting"""
        section = self.formatter._format_options_section(self.sample_data['options_data'])
        
        self.assertIsInstance(section, str)
        self.assertIn('SPY', section)
        self.assertIn('450.00', section)
    
    def test_fallback_format(self):
        """Test fallback formatting"""
        result = self.formatter._fallback_format(self.sample_data)
        
        self.assertIsInstance(result, str)
        self.assertIn('Daily Financial Report', result)
        self.assertIn('forex_data', result)


class TestDataSanitizer(unittest.TestCase):
    """Test DataSanitizer functionality"""
    
    def setUp(self):
        self.sanitizer = DataSanitizer()
    
    def test_remove_pii(self):
        """Test PII removal"""
        text = "Contact john.doe@example.com or call 555-123-4567"
        sanitized = self.sanitizer.remove_pii(text)
        
        self.assertNotIn("john.doe@example.com", sanitized)
        self.assertNotIn("555-123-4567", sanitized)
        self.assertIn("[EMAIL]", sanitized)
        self.assertIn("[PHONE]", sanitized)
    
    def test_anonymize_urls(self):
        """Test URL anonymization"""
        text = "Visit https://www.mymama.uk/alerts for more info"
        anonymized = self.sanitizer.anonymize_urls(text)
        
        self.assertIn("https://mymama.uk/[PATH]", anonymized)
        self.assertNotIn("/alerts", anonymized)


class TestRateLimiter(unittest.TestCase):
    """Test RateLimiter functionality"""
    
    def setUp(self):
        self.limiter = RateLimiter(min_delay=1.0, max_delay=5.0)
    
    def test_can_request(self):
        """Test request permission logic"""
        domain = "test.com"
        
        # First request should be allowed
        self.assertTrue(self.limiter.can_request(domain))
        
        # Immediate second request should be blocked
        self.assertFalse(self.limiter.can_request(domain))
    
    def test_wait_time(self):
        """Test wait time calculation"""
        domain = "test.com"
        
        # No previous request
        self.assertEqual(self.limiter.wait_time(domain), 0)
        
        # After request, should have wait time
        self.limiter.can_request(domain)
        wait_time = self.limiter.wait_time(domain)
        self.assertGreater(wait_time, 0)
    
    def test_adaptive_delays(self):
        """Test adaptive delay mechanism"""
        domain = "failing.com"
        
        # Record multiple failures
        for _ in range(5):
            self.limiter.record_failure(domain)
        
        # Should have increased delay
        self.assertIn(domain, self.limiter.adaptive_delays)
        self.assertGreater(self.limiter.adaptive_delays[domain], self.limiter.min_interval)


class TestConfigManager(unittest.TestCase):
    """Test ConfigManager functionality"""
    
    def setUp(self):
        # Create temporary config file
        self.temp_dir = tempfile.mkdtemp()
        self.config_file = os.path.join(self.temp_dir, 'test_config.json')
        
        self.test_config = {
            "mymama": {
                "base_url": "https://test.com",
                "selectors": {
                    "username": "input[name='username']"
                }
            },
            "telegram": {
                "bot_token": "test_token",
                "group_id": "test_group"
            }
        }
        
        with open(self.config_file, 'w') as f:
            json.dump(self.test_config, f)
        
        self.config_manager = ConfigManager(self.config_file)
    
    def tearDown(self):
        # Clean up temporary files
        import shutil
        shutil.rmtree(self.temp_dir)
    
    def test_load_config(self):
        """Test configuration loading"""
        self.assertTrue(self.config_manager.load_config())
        self.assertEqual(
            self.config_manager.get('mymama.base_url'), 
            "https://test.com"
        )
    
    def test_get_config_value(self):
        """Test getting configuration values"""
        value = self.config_manager.get('mymama.base_url')
        self.assertEqual(value, "https://test.com")
        
        # Test default value
        default_value = self.config_manager.get('nonexistent.key', 'default')
        self.assertEqual(default_value, 'default')
    
    def test_set_config_value(self):
        """Test setting configuration values"""
        success = self.config_manager.set('new.section.key', 'test_value')
        self.assertTrue(success)
        
        value = self.config_manager.get('new.section.key')
        self.assertEqual(value, 'test_value')


class TestConfigValidator(unittest.TestCase):
    """Test ConfigValidator functionality"""
    
    def test_valid_config(self):
        """Test validation of valid configuration"""
        valid_config = {
            "mymama": {
                "base_url": "https://test.com",
                "essentials_path": "/test",
                "selectors": {
                    "username": "input",
                    "password": "input",
                    "submit": "button",
                    "content": "div"
                }
            },
            "telegram": {
                "bot_token": "token",
                "group_id": "group"
            },
            "scraping": {},
            "monitoring": {},
            "security": {}
        }
        
        is_valid, errors = ConfigValidator.validate_config(valid_config)
        self.assertTrue(is_valid)
        self.assertEqual(len(errors), 0)
    
    def test_invalid_config(self):
        """Test validation of invalid configuration"""
        invalid_config = {
            "mymama": {
                "base_url": "https://test.com"
                # Missing required fields
            }
        }
        
        is_valid, errors = ConfigValidator.validate_config(invalid_config)
        self.assertFalse(is_valid)
        self.assertGreater(len(errors), 0)


class TestErrorHandler(unittest.TestCase):
    """Test ErrorHandler functionality"""
    
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.log_file = os.path.join(self.temp_dir, 'test_errors.log')
        self.error_handler = ErrorHandler(self.log_file)
    
    def tearDown(self):
        import shutil
        shutil.rmtree(self.temp_dir)
    
    def test_handle_error(self):
        """Test error handling"""
        test_error = ValueError("Test error")
        
        result = self.error_handler.handle_error(
            test_error, 
            "test_context", 
            "HIGH"
        )
        
        # Should log error
        self.assertIn("test_context:ValueError", self.error_handler.error_counts)
        self.assertEqual(self.error_handler.error_counts["test_context:ValueError"], 1)
    
    def test_recovery_strategy(self):
        """Test error recovery strategy"""
        def test_recovery(error, context, data):
            return "recovered"
        
        self.error_handler.register_recovery(ValueError, test_recovery)
        
        test_error = ValueError("Test error")
        result = self.error_handler.handle_error(test_error, "test_context")
        
        self.assertEqual(result, "recovered")
    
    def test_resilient_operation_decorator(self):
        """Test resilient operation decorator"""
        call_count = 0
        
        @resilient_operation("test_operation", max_retries=2, fallback_result="fallback")
        def failing_function():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ValueError("Test error")
            return "success"
        
        result = failing_function()
        self.assertEqual(result, "success")
        self.assertEqual(call_count, 3)


class TestIntegration(unittest.TestCase):
    """Integration tests for multiple components working together"""
    
    def test_forex_parsing_and_formatting(self):
        """Test complete forex parsing and formatting pipeline"""
        # Sample data
        raw_text = """
        EURUSD strong BUY signal at 1.0850
        GBPUSD SELL recommendation at 1.2650
        """
        
        # Parse signals
        parser = ForexParser()
        signals = parser.extract_forex_signals(raw_text)
        
        # Format report
        formatter = ReportFormatter()
        report_data = {'forex_data': signals}
        
        # Should not raise exception
        try:
            formatted_section = formatter._format_forex_section(signals)
            self.assertIsInstance(formatted_section, str)
        except Exception as e:
            self.fail(f"Integration test failed: {e}")
    
    def test_data_sanitization_pipeline(self):
        """Test data sanitization in processing pipeline"""
        # Data with PII
        raw_data = "Contact support at help@example.com or 555-123-4567"
        
        sanitizer = DataSanitizer()
        sanitized = sanitizer.remove_pii(raw_data)
        
        # Should not contain original PII
        self.assertNotIn("help@example.com", sanitized)
        self.assertNotIn("555-123-4567", sanitized)


def run_tests():
    """Run all tests"""
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add test classes
    test_classes = [
        TestForexParser,
        TestReportFormatter,
        TestDataSanitizer,
        TestRateLimiter,
        TestConfigManager,
        TestConfigValidator,
        TestErrorHandler,
        TestIntegration
    ]
    
    for test_class in test_classes:
        tests = loader.loadTestsFromTestCase(test_class)
        suite.addTests(tests)
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Print summary
    print(f"\n{'='*50}")
    print(f"Test Summary:")
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print(f"Success rate: {((result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100):.1f}%")
    
    return result.wasSuccessful()


if __name__ == '__main__':
    success = run_tests()
    exit(0 if success else 1)