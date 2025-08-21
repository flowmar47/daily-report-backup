#!/usr/bin/env python3
"""
Test Suite for Enhanced Error Handling System
Comprehensive testing of all enhanced components and error handling patterns
"""

import asyncio
import logging
import json
import time
from datetime import datetime
from pathlib import Path
import traceback

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Import enhanced components
from enhanced_error_handler import (
    EnhancedErrorHandler, ErrorContext, ErrorCategory, ErrorSeverity,
    DataValidator, resilient_operation, global_error_handler
)
from enhanced_messaging import EnhancedMessagingSystem, MessagePriority
from network_resilience import NetworkHealthMonitor, network_monitor


class EnhancedSystemTester:
    """Comprehensive test suite for enhanced error handling system"""
    
    def __init__(self):
        self.test_results = {}
        self.start_time = time.time()
        
        # Test components
        self.error_handler = global_error_handler
        self.messaging_system = EnhancedMessagingSystem()
        self.data_validator = DataValidator()
        self.network_monitor = network_monitor
        
        logger.info("Enhanced system tester initialized")
    
    def log_test_result(self, test_name: str, success: bool, details: str = ""):
        """Log test result"""
        status = "✅ PASS" if success else "❌ FAIL"
        logger.info(f"{status} {test_name}: {details}")
        
        self.test_results[test_name] = {
            'success': success,
            'details': details,
            'timestamp': datetime.now().isoformat()
        }
    
    async def test_error_handler(self):
        """Test enhanced error handler functionality"""
        logger.info("🧪 Testing Enhanced Error Handler...")
        
        try:
            # Test 1: Basic error handling
            test_error = ValueError("Test error for enhanced handler")
            context = ErrorContext(
                component="test_suite",
                operation="test_error_handler",
                financial_data_involved=True
            )
            
            result = await self.error_handler.handle_error(
                test_error, context, ErrorCategory.DATA_VALIDATION, ErrorSeverity.MEDIUM
            )
            
            self.log_test_result(
                "error_handler_basic",
                result is not None,
                f"Recovery strategy: {result.strategy_used.value if result else 'None'}"
            )
            
            # Test 2: Error statistics
            stats = self.error_handler.get_error_statistics()
            self.log_test_result(
                "error_handler_statistics",
                isinstance(stats, dict) and 'error_counts' in stats,
                f"Stats keys: {list(stats.keys())}"
            )
            
            # Test 3: Recovery strategies
            for category in [ErrorCategory.AUTHENTICATION, ErrorCategory.NETWORK, ErrorCategory.MESSAGING]:
                try:
                    test_error = Exception(f"Test {category.value} error")
                    context = ErrorContext(component="test", operation="recovery_test")
                    result = await self.error_handler.handle_error(test_error, context, category)
                    
                    self.log_test_result(
                        f"error_handler_recovery_{category.value.lower()}",
                        result is not None,
                        f"Success: {result.success if result else False}"
                    )
                except Exception as e:
                    self.log_test_result(
                        f"error_handler_recovery_{category.value.lower()}",
                        False,
                        f"Exception: {str(e)}"
                    )
            
        except Exception as e:
            self.log_test_result("error_handler", False, f"Exception: {str(e)}")
    
    async def test_data_validator(self):
        """Test data validation functionality"""
        logger.info("🧪 Testing Data Validator...")
        
        try:
            # Test 1: Valid forex data
            valid_forex_data = {
                'EURUSD': {
                    'signal': 'BUY',
                    'entry': '1.0850',
                    'exit': '1.0900',
                    'high': '1.0875',
                    'low': '1.0825'
                },
                'GBPUSD': {
                    'signal': 'SELL',
                    'entry': '1.2650',
                    'exit': '1.2600',
                    'high': '1.2675',
                    'low': '1.2625'
                }
            }
            
            forex_validation = self.data_validator.validate_forex_data(valid_forex_data)
            self.log_test_result(
                "data_validator_forex_valid",
                forex_validation['is_valid'],
                f"Quality score: {forex_validation['data_quality_score']}"
            )
            
            # Test 2: Invalid forex data (test patterns)
            invalid_forex_data = {
                'EURUSD': {
                    'signal': 'TEST',
                    'entry': 'sample',
                    'exit': 'demo',
                    'high': 'fake',
                    'low': 'mock'
                }
            }
            
            invalid_validation = self.data_validator.validate_forex_data(invalid_forex_data)
            self.log_test_result(
                "data_validator_forex_invalid",
                not invalid_validation['is_valid'],
                f"Errors detected: {len(invalid_validation['errors'])}"
            )
            
            # Test 3: Valid options data
            valid_options_data = [
                {
                    'ticker': 'TSLA',
                    'high_52week': '479.70',
                    'low_52week': '258.35',
                    'call_strike': '352.42',
                    'put_strike': '345.45',
                    'status': 'ACTIVE'
                }
            ]
            
            options_validation = self.data_validator.validate_options_data(valid_options_data)
            self.log_test_result(
                "data_validator_options_valid",
                options_validation['is_valid'],
                f"Quality score: {options_validation['data_quality_score']}"
            )
            
        except Exception as e:
            self.log_test_result("data_validator", False, f"Exception: {str(e)}")
    
    async def test_resilient_operation_decorator(self):
        """Test resilient operation decorator"""
        logger.info("🧪 Testing Resilient Operation Decorator...")
        
        try:
            # Test successful operation
            @resilient_operation(
                category=ErrorCategory.NETWORK,
                severity=ErrorSeverity.MEDIUM,
                component="test_decorator"
            )
            async def successful_operation():
                return "success"
            
            result = await successful_operation()
            self.log_test_result(
                "resilient_decorator_success",
                result == "success",
                f"Result: {result}"
            )
            
            # Test failing operation with recovery
            failure_count = 0
            
            @resilient_operation(
                category=ErrorCategory.DATA_VALIDATION,
                severity=ErrorSeverity.LOW,
                component="test_decorator",
                financial_data=True
            )
            async def failing_operation():
                nonlocal failure_count
                failure_count += 1
                if failure_count < 2:
                    raise ValueError("Test failure")
                return "recovered"
            
            result = await failing_operation()
            self.log_test_result(
                "resilient_decorator_recovery",
                result == "recovered",
                f"Failures before recovery: {failure_count}"
            )
            
        except Exception as e:
            self.log_test_result("resilient_decorator", False, f"Exception: {str(e)}")
    
    async def test_messaging_system(self):
        """Test enhanced messaging system"""
        logger.info("🧪 Testing Enhanced Messaging System...")
        
        try:
            # Start queue processor
            await self.messaging_system.start_queue_processor()
            
            # Test 1: Send financial alert
            message_id = await self.messaging_system.send_financial_alert(
                "🧪 TEST: Enhanced messaging system test alert",
                priority=MessagePriority.LOW,
                immediate=False  # Queue it
            )
            
            self.log_test_result(
                "messaging_financial_alert",
                bool(message_id),
                f"Message ID: {message_id}"
            )
            
            # Test 2: Get system status
            status = self.messaging_system.get_system_status()
            self.log_test_result(
                "messaging_system_status",
                isinstance(status, dict) and 'messengers' in status,
                f"Queued messages: {status['queue']['queued_messages']}"
            )
            
            # Test 3: Queue statistics
            queue_stats = self.messaging_system.message_queue.get_statistics()
            self.log_test_result(
                "messaging_queue_stats",
                isinstance(queue_stats, dict),
                f"Stats: {queue_stats}"
            )
            
            # Wait for processing
            await asyncio.sleep(2)
            
            # Stop queue processor
            await self.messaging_system.stop_queue_processor()
            
        except Exception as e:
            self.log_test_result("messaging_system", False, f"Exception: {str(e)}")
    
    async def test_network_resilience(self):
        """Test network resilience functionality"""
        logger.info("🧪 Testing Network Resilience...")
        
        try:
            # Test 1: Connectivity tests
            tests = await self.network_monitor.run_comprehensive_connectivity_test()
            self.log_test_result(
                "network_connectivity_tests",
                len(tests) > 0,
                f"Tests completed: {len(tests)}"
            )
            
            # Test 2: Network health assessment
            health = self.network_monitor.assess_network_health(tests)
            self.log_test_result(
                "network_health_assessment",
                health.status is not None,
                f"Status: {health.status.value}, Loss: {health.packet_loss_rate:.1%}"
            )
            
            # Test 3: Circuit breaker
            breaker = self.network_monitor.get_circuit_breaker("test_endpoint")
            initial_state = breaker.state
            
            # Trigger failures
            for _ in range(6):
                breaker.record_failure()
            
            # Check if breaker opened
            opened_state = breaker.state
            
            self.log_test_result(
                "network_circuit_breaker",
                initial_state != opened_state,
                f"State changed: {initial_state.value} -> {opened_state.value}"
            )
            
            # Test 4: Network statistics
            stats = self.network_monitor.get_network_statistics()
            self.log_test_result(
                "network_statistics",
                isinstance(stats, dict) and 'overall_health' in stats,
                f"Stats available: {list(stats.keys())}"
            )
            
        except Exception as e:
            self.log_test_result("network_resilience", False, f"Exception: {str(e)}")
    
    async def test_integration_scenarios(self):
        """Test integration scenarios"""
        logger.info("🧪 Testing Integration Scenarios...")
        
        try:
            # Scenario 1: Simulated authentication failure with recovery
            context = ErrorContext(
                component="integration_test",
                operation="simulated_auth_failure",
                financial_data_involved=True
            )
            
            auth_error = Exception("Simulated authentication failure")
            recovery_result = await self.error_handler.handle_error(
                auth_error, context, ErrorCategory.AUTHENTICATION, ErrorSeverity.HIGH
            )
            
            self.log_test_result(
                "integration_auth_recovery",
                recovery_result is not None,
                f"Recovery attempted: {recovery_result.strategy_used.value if recovery_result else 'None'}"
            )
            
            # Scenario 2: Data validation failure with fallback
            invalid_data = {'invalid': 'test data'}
            validation_error = ValueError("Invalid financial data")
            
            context = ErrorContext(
                component="integration_test",
                operation="data_validation_failure",
                financial_data_involved=True
            )
            
            validation_recovery = await self.error_handler.handle_error(
                validation_error, context, ErrorCategory.DATA_VALIDATION, ErrorSeverity.MEDIUM
            )
            
            self.log_test_result(
                "integration_validation_fallback",
                validation_recovery is not None and validation_recovery.fallback_data is not None,
                f"Fallback data provided: {bool(validation_recovery.fallback_data if validation_recovery else False)}"
            )
            
            # Scenario 3: Messaging failure with retry
            messaging_error = Exception("Simulated messaging failure")
            context = ErrorContext(
                component="integration_test",
                operation="messaging_failure",
                financial_data_involved=True
            )
            
            messaging_recovery = await self.error_handler.handle_error(
                messaging_error, context, ErrorCategory.MESSAGING, ErrorSeverity.HIGH
            )
            
            self.log_test_result(
                "integration_messaging_retry",
                messaging_recovery is not None,
                f"Recovery success: {messaging_recovery.success if messaging_recovery else False}"
            )
            
        except Exception as e:
            self.log_test_result("integration_scenarios", False, f"Exception: {str(e)}")
    
    async def test_performance_and_stress(self):
        """Test performance under stress conditions"""
        logger.info("🧪 Testing Performance and Stress...")
        
        try:
            # Test 1: Multiple concurrent error handling
            async def generate_test_error(error_id: int):
                error = Exception(f"Concurrent test error {error_id}")
                context = ErrorContext(
                    component="stress_test",
                    operation=f"concurrent_error_{error_id}",
                    metadata={"error_id": error_id}
                )
                return await self.error_handler.handle_error(
                    error, context, ErrorCategory.SYSTEM, ErrorSeverity.LOW
                )
            
            start_time = time.time()
            concurrent_tasks = [generate_test_error(i) for i in range(10)]
            results = await asyncio.gather(*concurrent_tasks, return_exceptions=True)
            concurrent_time = time.time() - start_time
            
            successful_results = [r for r in results if not isinstance(r, Exception)]
            
            self.log_test_result(
                "performance_concurrent_errors",
                len(successful_results) == 10,
                f"Processed 10 errors in {concurrent_time:.2f}s"
            )
            
            # Test 2: Data validation performance
            large_forex_data = {}
            for i in range(50):
                large_forex_data[f'PAIR{i:02d}'] = {
                    'signal': 'BUY' if i % 2 == 0 else 'SELL',
                    'entry': f'1.{i:04d}',
                    'exit': f'1.{i+1:04d}',
                    'high': f'1.{i+2:04d}',
                    'low': f'1.{i-1:04d}'
                }
            
            start_time = time.time()
            validation_result = self.data_validator.validate_forex_data(large_forex_data)
            validation_time = time.time() - start_time
            
            self.log_test_result(
                "performance_data_validation",
                validation_result['is_valid'],
                f"Validated 50 forex pairs in {validation_time:.3f}s"
            )
            
        except Exception as e:
            self.log_test_result("performance_stress", False, f"Exception: {str(e)}")
    
    def generate_test_report(self):
        """Generate comprehensive test report"""
        total_time = time.time() - self.start_time
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results.values() if result['success'])
        failed_tests = total_tests - passed_tests
        
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        report = {
            'test_summary': {
                'total_tests': total_tests,
                'passed_tests': passed_tests,
                'failed_tests': failed_tests,
                'success_rate': f"{success_rate:.1f}%",
                'total_time': f"{total_time:.2f}s",
                'timestamp': datetime.now().isoformat()
            },
            'test_results': self.test_results,
            'system_status': {
                'error_handler_stats': self.error_handler.get_error_statistics(),
                'messaging_status': self.messaging_system.get_system_status(),
                'network_stats': self.network_monitor.get_network_statistics()
            }
        }
        
        # Save report
        report_file = Path('logs/enhanced_system_test_report.json')
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2, default=str)
        
        # Print summary
        print("\n" + "=" * 80)
        print("🧪 ENHANCED SYSTEM TEST REPORT")
        print("=" * 80)
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests} ✅")
        print(f"Failed: {failed_tests} ❌")
        print(f"Success Rate: {success_rate:.1f}%")
        print(f"Total Time: {total_time:.2f}s")
        print("\n📋 Test Results:")
        
        for test_name, result in self.test_results.items():
            status = "✅" if result['success'] else "❌"
            print(f"  {status} {test_name}: {result['details']}")
        
        print(f"\n📄 Full report saved to: {report_file}")
        print("=" * 80)
        
        return report
    
    async def run_all_tests(self):
        """Run all test suites"""
        logger.info("🚀 Starting Enhanced System Test Suite...")
        
        test_suites = [
            ("Error Handler", self.test_error_handler),
            ("Data Validator", self.test_data_validator),
            ("Resilient Operations", self.test_resilient_operation_decorator),
            ("Messaging System", self.test_messaging_system),
            ("Network Resilience", self.test_network_resilience),
            ("Integration Scenarios", self.test_integration_scenarios),
            ("Performance & Stress", self.test_performance_and_stress)
        ]
        
        for suite_name, suite_function in test_suites:
            try:
                logger.info(f"\n🧪 Running {suite_name} tests...")
                await suite_function()
            except Exception as e:
                logger.error(f"❌ Test suite {suite_name} failed with exception: {e}")
                logger.error(traceback.format_exc())
                self.log_test_result(f"{suite_name}_suite", False, f"Suite exception: {str(e)}")
        
        # Generate final report
        return self.generate_test_report()


async def main():
    """Main test execution"""
    tester = EnhancedSystemTester()
    report = await tester.run_all_tests()
    
    # Return exit code based on success rate
    success_rate = float(report['test_summary']['success_rate'].rstrip('%'))
    exit_code = 0 if success_rate >= 80 else 1
    
    logger.info(f"Test suite completed with {success_rate:.1f}% success rate")
    return exit_code


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)