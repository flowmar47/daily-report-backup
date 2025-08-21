#!/usr/bin/env python3
"""
Enhanced Error Handling System
Provides comprehensive error handling, retry mechanisms, and circuit breaker patterns
for all components of the financial alerts system
"""

import asyncio
import logging
import json
import time
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Callable, Union
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from functools import wraps
from tenacity import (
    retry, stop_after_attempt, wait_exponential, wait_fixed,
    retry_if_exception_type, retry_if_result, before_sleep_log
)

logger = logging.getLogger(__name__)

class ErrorSeverity(str, Enum):
    """Error severity levels"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"

class ErrorCategory(str, Enum):
    """Error categories for classification"""
    AUTHENTICATION = "authentication"
    NETWORK = "network"
    DATA_EXTRACTION = "data_extraction"
    DATA_VALIDATION = "data_validation"
    RATE_LIMITING = "rate_limiting"
    CONFIGURATION = "configuration"
    EXTERNAL_API = "external_api"
    BROWSER_AUTOMATION = "browser_automation"
    FILE_SYSTEM = "file_system"
    MESSAGING = "messaging"
    UNKNOWN = "unknown"

class RetryStrategy(str, Enum):
    """Retry strategy types"""
    EXPONENTIAL_BACKOFF = "exponential_backoff"
    FIXED_DELAY = "fixed_delay"
    NO_RETRY = "no_retry"
    CIRCUIT_BREAKER = "circuit_breaker"

@dataclass
class ErrorContext:
    """Context information for error handling"""
    operation: str
    component: str
    severity: ErrorSeverity
    category: ErrorCategory
    retry_strategy: RetryStrategy = RetryStrategy.EXPONENTIAL_BACKOFF
    max_retries: int = 3
    base_delay: float = 1.0
    max_delay: float = 60.0
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)

@dataclass
class ErrorRecord:
    """Record of an error occurrence"""
    error: Exception
    context: ErrorContext
    retry_count: int = 0
    resolved: bool = False
    resolution_time: Optional[datetime] = None
    stack_trace: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.now)

class CircuitBreakerState(str, Enum):
    """Circuit breaker states"""
    CLOSED = "closed"     # Normal operation
    OPEN = "open"         # Failing, reject calls
    HALF_OPEN = "half_open"  # Testing if service recovered

@dataclass
class CircuitBreaker:
    """Circuit breaker for external service calls"""
    name: str
    failure_threshold: int = 5
    recovery_timeout: int = 60
    state: CircuitBreakerState = CircuitBreakerState.CLOSED
    failure_count: int = 0
    last_failure_time: Optional[datetime] = None
    
    def can_execute(self) -> bool:
        """Check if operation can be executed"""
        if self.state == CircuitBreakerState.CLOSED:
            return True
        elif self.state == CircuitBreakerState.OPEN:
            if self._should_attempt_reset():
                self.state = CircuitBreakerState.HALF_OPEN
                return True
            return False
        else:  # HALF_OPEN
            return True
    
    def record_success(self):
        """Record successful operation"""
        self.failure_count = 0
        self.state = CircuitBreakerState.CLOSED
        self.last_failure_time = None
    
    def record_failure(self):
        """Record failed operation"""
        self.failure_count += 1
        self.last_failure_time = datetime.now()
        
        if self.state == CircuitBreakerState.HALF_OPEN:
            self.state = CircuitBreakerState.OPEN
        elif self.failure_count >= self.failure_threshold:
            self.state = CircuitBreakerState.OPEN
    
    def _should_attempt_reset(self) -> bool:
        """Check if enough time has passed to attempt reset"""
        if not self.last_failure_time:
            return True
        return datetime.now() - self.last_failure_time > timedelta(seconds=self.recovery_timeout)

class EnhancedErrorHandler:
    """
    Enhanced error handler with comprehensive error management
    Provides retry mechanisms, circuit breakers, and error analytics
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        """
        Initialize enhanced error handler
        
        Args:
            log_dir: Directory for error logs
        """
        config = config or {}
        self.log_dir = Path(config.get('log_dir', 'logs'))
        self.log_dir.mkdir(exist_ok=True)
        
        # Error tracking
        self.error_records: List[ErrorRecord] = []
        self.circuit_breakers: Dict[str, CircuitBreaker] = {}
        
        # Rate limiting for error notifications
        self.notification_cooldown = {}
        self.cooldown_period = 300  # 5 minutes
        
        logger.info("Enhanced error handler initialized")
    
    def get_or_create_circuit_breaker(self, name: str, **kwargs) -> CircuitBreaker:
        """Get or create circuit breaker for service"""
        if name not in self.circuit_breakers:
            self.circuit_breakers[name] = CircuitBreaker(name=name, **kwargs)
        return self.circuit_breakers[name]
    
    async def handle_error(self, error: Exception, context: ErrorContext) -> bool:
        """
        Handle error with appropriate strategy
        
        Args:
            error: Exception that occurred
            context: Error context information
            
        Returns:
            True if error was handled and operation should continue
        """
        # Record error
        error_record = ErrorRecord(
            error=error,
            context=context,
            stack_trace=str(error.__traceback__) if error.__traceback__ else None
        )
        self.error_records.append(error_record)
        
        # Log error
        await self._log_error(error_record)
        
        # Determine if should retry
        if context.retry_strategy == RetryStrategy.NO_RETRY:
            return False
        
        # Check circuit breaker
        if context.retry_strategy == RetryStrategy.CIRCUIT_BREAKER:
            circuit_breaker = self.get_or_create_circuit_breaker(
                f"{context.component}_{context.operation}"
            )
            if not circuit_breaker.can_execute():
                logger.warning(f"Circuit breaker OPEN for {context.operation}")
                return False
        
        # Apply rate limiting for notifications
        await self._apply_notification_cooldown(context)
        
        return True
    
    async def _log_error(self, error_record: ErrorRecord):
        """Log error to file and console"""
        context = error_record.context
        
        # Console logging
        log_level = self._get_log_level(context.severity)
        logger.log(log_level, 
                  f"Error in {context.component}.{context.operation}: "
                  f"{type(error_record.error).__name__}: {error_record.error}")
        
        # File logging
        log_data = {
            'timestamp': error_record.timestamp.isoformat(),
            'component': context.component,
            'operation': context.operation,
            'severity': context.severity,
            'category': context.category,
            'error_type': type(error_record.error).__name__,
            'error_message': str(error_record.error),
            'retry_count': error_record.retry_count,
            'metadata': context.metadata
        }
        
        log_file = self.log_dir / f"errors_{datetime.now().strftime('%Y%m%d')}.jsonl"
        with open(log_file, 'a') as f:
            f.write(json.dumps(log_data) + '\n')
    
    def _get_log_level(self, severity: ErrorSeverity) -> int:
        """Get logging level for severity"""
        mapping = {
            ErrorSeverity.CRITICAL: logging.CRITICAL,
            ErrorSeverity.HIGH: logging.ERROR,
            ErrorSeverity.MEDIUM: logging.WARNING,
            ErrorSeverity.LOW: logging.INFO,
            ErrorSeverity.INFO: logging.INFO
        }
        return mapping.get(severity, logging.ERROR)
    
    async def _apply_notification_cooldown(self, context: ErrorContext):
        """Apply cooldown to prevent notification spam"""
        cooldown_key = f"{context.component}_{context.operation}"
        last_notification = self.notification_cooldown.get(cooldown_key, 0)
        current_time = time.time()
        
        if current_time - last_notification < self.cooldown_period:
            return  # Still in cooldown
        
        self.notification_cooldown[cooldown_key] = current_time
        
        # Send notification for critical/high severity errors
        if context.severity in [ErrorSeverity.CRITICAL, ErrorSeverity.HIGH]:
            await self._send_error_notification(context)
    
    async def _send_error_notification(self, context: ErrorContext):
        """Send error notification (placeholder for future implementation)"""
        logger.warning(f"🚨 Critical error notification: {context.component}.{context.operation}")
    
    def get_circuit_breaker(self, service_name: str):
        """Get or create a circuit breaker for a service"""
        if service_name not in self.circuit_breakers:
            # Create a simple mock circuit breaker
            class MockCircuitBreaker:
                def is_open(self):
                    return False
                def can_execute(self):
                    return True
                def record_failure(self):
                    pass
                def record_success(self):
                    pass
            self.circuit_breakers[service_name] = MockCircuitBreaker()
        return self.circuit_breakers[service_name]
    
    def get_error_statistics(self) -> Dict[str, Any]:
        """Get error statistics for monitoring"""
        if not self.error_records:
            return {'total_errors': 0}
        
        # Group by component and category
        by_component = {}
        by_category = {}
        by_severity = {}
        
        for record in self.error_records:
            context = record.context
            
            # By component
            if context.component not in by_component:
                by_component[context.component] = 0
            by_component[context.component] += 1
            
            # By category
            if context.category not in by_category:
                by_category[context.category] = 0
            by_category[context.category] += 1
            
            # By severity
            if context.severity not in by_severity:
                by_severity[context.severity] = 0
            by_severity[context.severity] += 1
        
        return {
            'total_errors': len(self.error_records),
            'by_component': by_component,
            'by_category': by_category,
            'by_severity': by_severity,
            'circuit_breakers': {
                name: {
                    'state': cb.state,
                    'failure_count': cb.failure_count
                }
                for name, cb in self.circuit_breakers.items()
            }
        }

# Global error handler instance
_global_error_handler = None

def get_error_handler() -> EnhancedErrorHandler:
    """Get global error handler instance"""
    global _global_error_handler
    if _global_error_handler is None:
        _global_error_handler = EnhancedErrorHandler()
    return _global_error_handler

# Decorator for resilient operations
def resilient_operation(
    operation_name: str,
    component: str,
    category: ErrorCategory = ErrorCategory.UNKNOWN,
    severity: ErrorSeverity = ErrorSeverity.MEDIUM,
    retry_strategy: RetryStrategy = RetryStrategy.EXPONENTIAL_BACKOFF,
    max_retries: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 60.0
):
    """
    Decorator for resilient operations with enhanced error handling
    
    Args:
        operation_name: Name of the operation
        component: Component performing the operation
        category: Error category
        severity: Error severity
        retry_strategy: Retry strategy to use
        max_retries: Maximum number of retries
        base_delay: Base delay for retries
        max_delay: Maximum delay for retries
    """
    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            error_handler = get_error_handler()
            context = ErrorContext(
                operation=operation_name,
                component=component,
                category=category,
                severity=severity,
                retry_strategy=retry_strategy,
                max_retries=max_retries,
                base_delay=base_delay,
                max_delay=max_delay
            )
            
            # Check circuit breaker
            if retry_strategy == RetryStrategy.CIRCUIT_BREAKER:
                circuit_breaker = error_handler.get_or_create_circuit_breaker(
                    f"{component}_{operation_name}"
                )
                if not circuit_breaker.can_execute():
                    raise Exception(f"Circuit breaker open for {operation_name}")
            
            # Configure retry based on strategy
            if retry_strategy == RetryStrategy.NO_RETRY:
                try:
                    result = await func(*args, **kwargs)
                    if retry_strategy == RetryStrategy.CIRCUIT_BREAKER:
                        circuit_breaker.record_success()
                    return result
                except Exception as e:
                    await error_handler.handle_error(e, context)
                    if retry_strategy == RetryStrategy.CIRCUIT_BREAKER:
                        circuit_breaker.record_failure()
                    raise
            
            elif retry_strategy == RetryStrategy.FIXED_DELAY:
                retry_decorator = retry(
                    stop=stop_after_attempt(max_retries),
                    wait=wait_fixed(base_delay),
                    before_sleep=before_sleep_log(logger, logging.WARNING)
                )
            else:  # EXPONENTIAL_BACKOFF or CIRCUIT_BREAKER
                retry_decorator = retry(
                    stop=stop_after_attempt(max_retries),
                    wait=wait_exponential(multiplier=base_delay, max=max_delay),
                    before_sleep=before_sleep_log(logger, logging.WARNING)
                )
            
            @retry_decorator
            async def retryable_func():
                try:
                    result = await func(*args, **kwargs)
                    if retry_strategy == RetryStrategy.CIRCUIT_BREAKER:
                        circuit_breaker.record_success()
                    return result
                except Exception as e:
                    context.retry_count = getattr(retryable_func.retry, 'statistics', {}).get('attempt_number', 1) - 1
                    should_continue = await error_handler.handle_error(e, context)
                    if retry_strategy == RetryStrategy.CIRCUIT_BREAKER:
                        circuit_breaker.record_failure()
                    if not should_continue:
                        raise
                    raise  # Re-raise for retry mechanism
            
            return await retryable_func()
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            # For synchronous functions, convert to async
            async def async_func():
                return func(*args, **kwargs)
            
            return asyncio.run(async_wrapper(*args, **kwargs))
        
        # Return appropriate wrapper based on function type
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator

# Specific retry decorators for common scenarios
def retry_on_network_error(max_retries: int = 3):
    """Decorator for network-related operations"""
    return resilient_operation(
        operation_name="network_operation",
        component="network",
        category=ErrorCategory.NETWORK,
        severity=ErrorSeverity.MEDIUM,
        retry_strategy=RetryStrategy.EXPONENTIAL_BACKOFF,
        max_retries=max_retries
    )

def retry_on_authentication_error(max_retries: int = 2):
    """Decorator for authentication operations"""
    return resilient_operation(
        operation_name="authentication",
        component="auth",
        category=ErrorCategory.AUTHENTICATION,
        severity=ErrorSeverity.HIGH,
        retry_strategy=RetryStrategy.FIXED_DELAY,
        max_retries=max_retries,
        base_delay=2.0
    )

def circuit_breaker_protection(service_name: str):
    """Decorator for external service calls with circuit breaker"""
    return resilient_operation(
        operation_name=f"{service_name}_call",
        component="external_service",
        category=ErrorCategory.EXTERNAL_API,
        severity=ErrorSeverity.MEDIUM,
        retry_strategy=RetryStrategy.CIRCUIT_BREAKER,
        max_retries=3
    )

# Data validation helpers
class DataValidator:
    """Helper class for data validation"""
    
    @staticmethod
    def validate_financial_data(data: Dict[str, Any]) -> bool:
        """Validate financial data structure"""
        required_fields = ['timestamp', 'source']
        return all(field in data for field in required_fields)
    
    @staticmethod
    def validate_credentials(credentials: Dict[str, str]) -> bool:
        """Validate credential completeness"""
        return all(
            value and not value.startswith('your_') and value != 'placeholder'
            for value in credentials.values()
        )

if __name__ == "__main__":
    # Example usage and testing
    async def test_error_handling():
        """Test the enhanced error handling system"""
        
        @resilient_operation(
            "test_operation",
            "test_component",
            ErrorCategory.DATA_EXTRACTION,
            ErrorSeverity.MEDIUM,
            max_retries=3
        )
        async def failing_operation():
            """Test operation that fails"""
            raise Exception("Test error")
        
        try:
            await failing_operation()
        except Exception as e:
            print(f"Operation failed after retries: {e}")
        
        # Get statistics
        error_handler = get_error_handler()
        stats = error_handler.get_error_statistics()
        print(f"Error statistics: {stats}")
    
    logging.basicConfig(level=logging.INFO)
    asyncio.run(test_error_handling())