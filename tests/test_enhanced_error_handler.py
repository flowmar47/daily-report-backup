#!/usr/bin/env python3
"""
Unit tests for EnhancedErrorHandler
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
import asyncio
import time
from pathlib import Path
import sys

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from enhanced_error_handler import (
    EnhancedErrorHandler, ErrorCategory, resilient_operation,
    validate_financial_data, CircuitBreaker, CircuitState
)


class TestEnhancedErrorHandler(unittest.TestCase):
    """Test EnhancedErrorHandler functionality"""
    
    def setUp(self):
        """Set up test environment"""
        self.config = {
            'retry_attempts': 3,
            'retry_delay': 0.1,
            'circuit_breaker_threshold': 5,
            'circuit_breaker_timeout': 60
        }
        self.handler = EnhancedErrorHandler(self.config)
        
    def test_initialization(self):
        """Test EnhancedErrorHandler initialization"""
        self.assertEqual(self.handler.config, self.config)
        self.assertEqual(len(self.handler.error_history), 0)
        self.assertIsInstance(self.handler.circuit_breakers, dict)
        
    def test_categorize_error(self):
        """Test error categorization"""
        # Network errors
        network_errors = [
            ConnectionError("Connection failed"),
            TimeoutError("Request timed out"),
            Exception("Network is unreachable"),
            Exception("Connection reset by peer")
        ]
        for error in network_errors:
            category = self.handler.categorize_error(error)
            self.assertEqual(category, ErrorCategory.NETWORK)
            
        # Authentication errors
        auth_errors = [
            Exception("Invalid credentials"),
            Exception("Authentication failed"),
            Exception("401 Unauthorized"),
            Exception("Access denied")
        ]
        for error in auth_errors:
            category = self.handler.categorize_error(error)
            self.assertEqual(category, ErrorCategory.AUTHENTICATION)
            
        # Data quality errors
        data_errors = [
            ValueError("Invalid data format"),
            KeyError("Missing required field"),
            Exception("No data found"),
            Exception("Empty response")
        ]
        for error in data_errors:
            category = self.handler.categorize_error(error)
            self.assertEqual(category, ErrorCategory.DATA_QUALITY)
            
    def test_should_retry(self):
        """Test retry decision logic"""
        # Retryable errors
        retryable = [
            ConnectionError("Temporary failure"),
            TimeoutError("Request timeout"),
            Exception("503 Service Unavailable")
        ]
        for error in retryable:
            self.assertTrue(self.handler.should_retry(error))
            
        # Non-retryable errors
        non_retryable = [
            ValueError("Invalid input"),
            KeyError("Missing field"),
            Exception("Invalid credentials")
        ]
        for error in non_retryable:
            self.assertFalse(self.handler.should_retry(error))
            
    @patch('enhanced_error_handler.logger')
    def test_log_error(self, mock_logger):
        """Test error logging"""
        error = ValueError("Test error")
        context = {"operation": "test", "attempt": 1}
        
        self.handler.log_error(error, context)
        
        # Verify logging
        mock_logger.error.assert_called()
        
        # Verify error history
        self.assertEqual(len(self.handler.error_history), 1)
        recorded_error = self.handler.error_history[0]
        self.assertEqual(recorded_error['error_type'], 'ValueError')
        self.assertEqual(recorded_error['message'], 'Test error')
        self.assertEqual(recorded_error['context'], context)
        
    def test_get_retry_delay(self):
        """Test retry delay calculation"""
        # Exponential backoff
        delays = []
        for attempt in range(1, 5):
            delay = self.handler.get_retry_delay(attempt)
            delays.append(delay)
            
        # Verify exponential increase
        for i in range(1, len(delays)):
            self.assertGreater(delays[i], delays[i-1])
            
    def test_get_error_summary(self):
        """Test error summary generation"""
        # Add some errors
        errors = [
            (ConnectionError("Network error"), {"operation": "fetch"}),
            (ValueError("Data error"), {"operation": "parse"}),
            (ConnectionError("Timeout"), {"operation": "fetch"})
        ]
        
        for error, context in errors:
            self.handler.log_error(error, context)
            
        # Get summary
        summary = self.handler.get_error_summary()
        
        # Verify summary structure
        self.assertIn('total_errors', summary)
        self.assertIn('errors_by_category', summary)
        self.assertIn('recent_errors', summary)
        self.assertEqual(summary['total_errors'], 3)
        
    def test_circuit_breaker_basic(self):
        """Test circuit breaker basic functionality"""
        operation = "test_operation"
        breaker = self.handler.get_circuit_breaker(operation)
        
        # Initially closed
        self.assertEqual(breaker.state, CircuitState.CLOSED)
        self.assertTrue(breaker.is_closed())
        
        # Record failures
        for i in range(5):  # threshold is 5
            breaker.record_failure()
            
        # Should be open now
        self.assertEqual(breaker.state, CircuitState.OPEN)
        self.assertTrue(breaker.is_open())
        
    def test_circuit_breaker_recovery(self):
        """Test circuit breaker recovery"""
        breaker = CircuitBreaker(threshold=2, timeout=0.1)
        
        # Trip the breaker
        breaker.record_failure()
        breaker.record_failure()
        self.assertTrue(breaker.is_open())
        
        # Wait for timeout
        time.sleep(0.2)
        
        # Should be half-open
        self.assertTrue(breaker.is_half_open())
        
        # Successful call should close it
        breaker.record_success()
        self.assertTrue(breaker.is_closed())
        
    @patch('enhanced_error_handler.asyncio.sleep')
    async def test_resilient_operation_decorator(self, mock_sleep):
        """Test resilient_operation decorator"""
        mock_sleep.return_value = None
        attempt_count = 0
        
        @resilient_operation(max_retries=3, base_delay=0.1)
        async def flaky_operation():
            nonlocal attempt_count
            attempt_count += 1
            if attempt_count < 3:
                raise ConnectionError("Temporary failure")
            return "Success"
            
        # Should succeed after retries
        result = await flaky_operation()
        self.assertEqual(result, "Success")
        self.assertEqual(attempt_count, 3)
        
    @patch('enhanced_error_handler.asyncio.sleep')
    async def test_resilient_operation_failure(self, mock_sleep):
        """Test resilient_operation decorator failure"""
        mock_sleep.return_value = None
        
        @resilient_operation(max_retries=2, base_delay=0.1)
        async def always_fails():
            raise ConnectionError("Permanent failure")
            
        # Should raise after max retries
        with self.assertRaises(ConnectionError):
            await always_fails()
            
    def test_validate_financial_data(self):
        """Test financial data validation"""
        # Valid data
        valid_data = {
            'forex_signals': [
                {'pair': 'EURUSD', 'signal': 'BUY', 'entry_price': 1.1234}
            ],
            'options_plays': [
                {'ticker': 'AAPL', 'strategy': 'CALL', 'strike': 150}
            ]
        }
        self.assertTrue(validate_financial_data(valid_data))
        
        # Invalid data - missing required fields
        invalid_data = {
            'forex_signals': [
                {'pair': 'EURUSD'}  # missing signal and entry_price
            ]
        }
        self.assertFalse(validate_financial_data(invalid_data))
        
        # Invalid data - wrong types
        invalid_types = {
            'forex_signals': "not a list"
        }
        self.assertFalse(validate_financial_data(invalid_types))
        
        # Empty data
        self.assertFalse(validate_financial_data({}))
        self.assertFalse(validate_financial_data(None))
        
    def test_clear_old_errors(self):
        """Test clearing old errors"""
        # Add errors with different timestamps
        import datetime
        
        # Add old error (manually set timestamp)
        old_error = {
            'timestamp': (datetime.datetime.now() - datetime.timedelta(days=8)).isoformat(),
            'error_type': 'OldError',
            'message': 'Old error',
            'category': ErrorCategory.UNKNOWN,
            'context': {}
        }
        self.handler.error_history.append(old_error)
        
        # Add recent error
        self.handler.log_error(ValueError("Recent error"), {})
        
        # Clear old errors
        initial_count = len(self.handler.error_history)
        self.handler.clear_old_errors(days=7)
        
        # Verify old error removed
        self.assertEqual(len(self.handler.error_history), initial_count - 1)
        self.assertFalse(any(e['error_type'] == 'OldError' for e in self.handler.error_history))
        
    def test_get_circuit_breaker_states(self):
        """Test getting all circuit breaker states"""
        # Create multiple circuit breakers
        operations = ['op1', 'op2', 'op3']
        for op in operations:
            breaker = self.handler.get_circuit_breaker(op)
            if op == 'op2':
                # Trip this one
                for _ in range(5):
                    breaker.record_failure()
                    
        # Get states
        states = self.handler.get_circuit_breaker_states()
        
        # Verify states
        self.assertEqual(len(states), 3)
        self.assertEqual(states['op1'], 'closed')
        self.assertEqual(states['op2'], 'open')
        self.assertEqual(states['op3'], 'closed')


class TestCircuitBreaker(unittest.TestCase):
    """Test CircuitBreaker functionality"""
    
    def test_state_transitions(self):
        """Test circuit breaker state transitions"""
        breaker = CircuitBreaker(threshold=3, timeout=0.1)
        
        # Start closed
        self.assertEqual(breaker.state, CircuitState.CLOSED)
        
        # Record some failures
        breaker.record_failure()
        breaker.record_failure()
        self.assertEqual(breaker.state, CircuitState.CLOSED)
        
        # Hit threshold - should open
        breaker.record_failure()
        self.assertEqual(breaker.state, CircuitState.OPEN)
        
        # Wait for timeout
        time.sleep(0.15)
        
        # Check state - should be half-open
        _ = breaker.state  # This triggers the state check
        self.assertEqual(breaker.state, CircuitState.HALF_OPEN)
        
        # Success in half-open state - should close
        breaker.record_success()
        self.assertEqual(breaker.state, CircuitState.CLOSED)
        
    def test_call_protection(self):
        """Test circuit breaker call protection"""
        breaker = CircuitBreaker(threshold=2, timeout=1)
        call_count = 0
        
        def protected_call():
            nonlocal call_count
            call_count += 1
            if call_count <= 2:
                raise Exception("Failure")
            return "Success"
            
        # First two calls should fail and trip breaker
        for _ in range(2):
            try:
                result = breaker.call(protected_call)
            except Exception:
                pass
                
        # Breaker should be open
        self.assertTrue(breaker.is_open())
        
        # Next call should be rejected without calling function
        with self.assertRaises(Exception) as cm:
            breaker.call(protected_call)
        self.assertIn("Circuit breaker is open", str(cm.exception))
        self.assertEqual(call_count, 2)  # Function not called
        
    def test_half_open_recovery(self):
        """Test recovery from half-open state"""
        breaker = CircuitBreaker(threshold=2, timeout=0.1)
        
        # Trip the breaker
        breaker.record_failure()
        breaker.record_failure()
        
        # Wait for half-open
        time.sleep(0.15)
        
        # Failure in half-open should re-open
        def failing_call():
            raise Exception("Still failing")
            
        try:
            breaker.call(failing_call)
        except Exception:
            pass
            
        self.assertTrue(breaker.is_open())
        self.assertEqual(breaker.failure_count, 3)


if __name__ == '__main__':
    unittest.main()