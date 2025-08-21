"""
Circuit breaker pattern implementation for API resilience
"""

import asyncio
import time
from enum import Enum
from typing import Callable, Any, Optional, Dict
from dataclasses import dataclass, field

from ..core.logging import get_logger
from ..core.exceptions import ForexSignalsError

logger = get_logger(__name__)


class CircuitBreakerState(Enum):
    """Circuit breaker states"""
    CLOSED = "closed"      # Normal operation
    OPEN = "open"          # Failing, calls rejected
    HALF_OPEN = "half_open"  # Testing if service recovered


@dataclass
class CircuitBreakerStats:
    """Circuit breaker statistics"""
    total_calls: int = 0
    successful_calls: int = 0
    failed_calls: int = 0
    consecutive_failures: int = 0
    last_failure_time: float = 0.0
    last_success_time: float = 0.0
    
    @property
    def failure_rate(self) -> float:
        """Calculate failure rate"""
        if self.total_calls == 0:
            return 0.0
        return self.failed_calls / self.total_calls
    
    @property
    def success_rate(self) -> float:
        """Calculate success rate"""
        return 1.0 - self.failure_rate


class CircuitBreaker:
    """
    Circuit breaker implementation for API resilience
    Prevents cascading failures by failing fast when service is down
    """
    
    def __init__(
        self,
        name: str,
        failure_threshold: int = 5,
        recovery_timeout: float = 60.0,
        expected_exception: type = Exception,
        failure_rate_threshold: float = 0.5,
        minimum_calls: int = 10
    ):
        """
        Initialize circuit breaker
        
        Args:
            name: Circuit breaker name
            failure_threshold: Number of consecutive failures to open circuit
            recovery_timeout: Time to wait before attempting recovery (seconds)
            expected_exception: Exception type that counts as failure
            failure_rate_threshold: Failure rate threshold (0.0 to 1.0)
            minimum_calls: Minimum calls before checking failure rate
        """
        self.name = name
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.expected_exception = expected_exception
        self.failure_rate_threshold = failure_rate_threshold
        self.minimum_calls = minimum_calls
        
        self.state = CircuitBreakerState.CLOSED
        self.stats = CircuitBreakerStats()
        self._state_change_time = time.time()
        
        logger.info(f"🔧 Circuit breaker '{name}' initialized")
    
    def _can_attempt_call(self) -> bool:
        """Check if call can be attempted based on current state"""
        now = time.time()
        
        if self.state == CircuitBreakerState.CLOSED:
            return True
        elif self.state == CircuitBreakerState.OPEN:
            # Check if recovery timeout has elapsed
            if now - self._state_change_time >= self.recovery_timeout:
                self._change_state(CircuitBreakerState.HALF_OPEN)
                logger.info(f"🔄 Circuit breaker '{self.name}' moved to HALF_OPEN")
                return True
            return False
        elif self.state == CircuitBreakerState.HALF_OPEN:
            return True
        
        return False
    
    def _on_success(self):
        """Handle successful call"""
        self.stats.successful_calls += 1
        self.stats.total_calls += 1
        self.stats.consecutive_failures = 0
        self.stats.last_success_time = time.time()
        
        if self.state == CircuitBreakerState.HALF_OPEN:
            self._change_state(CircuitBreakerState.CLOSED)
            logger.info(f"✅ Circuit breaker '{self.name}' recovered, moved to CLOSED")
    
    def _on_failure(self, exception: Exception):
        """Handle failed call"""
        self.stats.failed_calls += 1
        self.stats.total_calls += 1
        self.stats.consecutive_failures += 1
        self.stats.last_failure_time = time.time()
        
        logger.warning(f"⚠️ Circuit breaker '{self.name}' failure: {type(exception).__name__}")
        
        should_open = False
        
        # Check consecutive failures threshold
        if self.stats.consecutive_failures >= self.failure_threshold:
            should_open = True
            logger.warning(f"❌ Consecutive failure threshold ({self.failure_threshold}) reached")
        
        # Check failure rate threshold (if we have enough data)
        if (self.stats.total_calls >= self.minimum_calls and 
            self.stats.failure_rate >= self.failure_rate_threshold):
            should_open = True
            logger.warning(f"❌ Failure rate threshold ({self.failure_rate_threshold:.1%}) exceeded: {self.stats.failure_rate:.1%}")
        
        if should_open and self.state != CircuitBreakerState.OPEN:
            self._change_state(CircuitBreakerState.OPEN)
            logger.error(f"🚨 Circuit breaker '{self.name}' OPENED due to failures")
        elif self.state == CircuitBreakerState.HALF_OPEN:
            # Failed during recovery test, go back to OPEN
            self._change_state(CircuitBreakerState.OPEN)
            logger.warning(f"🔄 Circuit breaker '{self.name}' failed recovery test, back to OPEN")
    
    def _change_state(self, new_state: CircuitBreakerState):
        """Change circuit breaker state"""
        old_state = self.state
        self.state = new_state
        self._state_change_time = time.time()
        
        if old_state != new_state:
            logger.info(f"🔄 Circuit breaker '{self.name}': {old_state.value} → {new_state.value}")
    
    async def call_async(self, func: Callable, *args, **kwargs) -> Any:
        """
        Execute async function through circuit breaker
        
        Args:
            func: Async function to execute
            *args: Function arguments
            **kwargs: Function keyword arguments
            
        Returns:
            Function result
            
        Raises:
            ForexSignalsError: If circuit is open
            Exception: Original exception from function
        """
        if not self._can_attempt_call():
            raise ForexSignalsError(
                f"Circuit breaker '{self.name}' is OPEN. Service temporarily unavailable.",
                error_code="CIRCUIT_BREAKER_OPEN",
                details={"circuit_breaker": self.name, "state": self.state.value}
            )
        
        try:
            result = await func(*args, **kwargs)
            self._on_success()
            return result
            
        except self.expected_exception as e:
            self._on_failure(e)
            raise
        except Exception as e:
            # Unexpected exception - don't count as failure for circuit breaker
            logger.warning(f"⚠️ Unexpected exception in circuit breaker '{self.name}': {type(e).__name__}")
            raise
    
    def call_sync(self, func: Callable, *args, **kwargs) -> Any:
        """
        Execute sync function through circuit breaker
        
        Args:
            func: Sync function to execute
            *args: Function arguments
            **kwargs: Function keyword arguments
            
        Returns:
            Function result
            
        Raises:
            ForexSignalsError: If circuit is open
            Exception: Original exception from function
        """
        if not self._can_attempt_call():
            raise ForexSignalsError(
                f"Circuit breaker '{self.name}' is OPEN. Service temporarily unavailable.",
                error_code="CIRCUIT_BREAKER_OPEN",
                details={"circuit_breaker": self.name, "state": self.state.value}
            )
        
        try:
            result = func(*args, **kwargs)
            self._on_success()
            return result
            
        except self.expected_exception as e:
            self._on_failure(e)
            raise
        except Exception as e:
            # Unexpected exception - don't count as failure for circuit breaker
            logger.warning(f"⚠️ Unexpected exception in circuit breaker '{self.name}': {type(e).__name__}")
            raise
    
    def get_stats(self) -> Dict[str, Any]:
        """Get circuit breaker statistics"""
        return {
            "name": self.name,
            "state": self.state.value,
            "total_calls": self.stats.total_calls,
            "successful_calls": self.stats.successful_calls,
            "failed_calls": self.stats.failed_calls,
            "consecutive_failures": self.stats.consecutive_failures,
            "failure_rate": self.stats.failure_rate,
            "success_rate": self.stats.success_rate,
            "last_failure_time": self.stats.last_failure_time,
            "last_success_time": self.stats.last_success_time,
            "state_change_time": self._state_change_time,
            "time_in_current_state": time.time() - self._state_change_time
        }
    
    def reset(self):
        """Reset circuit breaker to initial state"""
        logger.info(f"🔄 Resetting circuit breaker '{self.name}'")
        self.state = CircuitBreakerState.CLOSED
        self.stats = CircuitBreakerStats()
        self._state_change_time = time.time()
    
    def force_open(self):
        """Force circuit breaker to OPEN state"""
        logger.warning(f"🚨 Forcing circuit breaker '{self.name}' to OPEN state")
        self._change_state(CircuitBreakerState.OPEN)
    
    def force_close(self):
        """Force circuit breaker to CLOSED state"""
        logger.info(f"✅ Forcing circuit breaker '{self.name}' to CLOSED state")
        self._change_state(CircuitBreakerState.CLOSED)
    
    def __str__(self) -> str:
        return f"CircuitBreaker(name='{self.name}', state={self.state.value})"
    
    def __repr__(self) -> str:
        return (f"CircuitBreaker(name='{self.name}', state={self.state.value}, "
                f"failures={self.stats.consecutive_failures}/{self.failure_threshold})")


# Global circuit breaker registry
_circuit_breakers: Dict[str, CircuitBreaker] = {}


def get_circuit_breaker(
    name: str,
    failure_threshold: int = 5,
    recovery_timeout: float = 60.0,
    expected_exception: type = Exception,
    failure_rate_threshold: float = 0.5,
    minimum_calls: int = 10
) -> CircuitBreaker:
    """
    Get or create a circuit breaker by name
    
    Args:
        name: Circuit breaker name
        failure_threshold: Number of consecutive failures to open circuit
        recovery_timeout: Time to wait before attempting recovery (seconds)
        expected_exception: Exception type that counts as failure
        failure_rate_threshold: Failure rate threshold (0.0 to 1.0)
        minimum_calls: Minimum calls before checking failure rate
        
    Returns:
        CircuitBreaker instance
    """
    if name not in _circuit_breakers:
        _circuit_breakers[name] = CircuitBreaker(
            name=name,
            failure_threshold=failure_threshold,
            recovery_timeout=recovery_timeout,
            expected_exception=expected_exception,
            failure_rate_threshold=failure_rate_threshold,
            minimum_calls=minimum_calls
        )
    
    return _circuit_breakers[name]


def get_all_circuit_breaker_stats() -> Dict[str, Dict[str, Any]]:
    """Get statistics for all circuit breakers"""
    return {name: cb.get_stats() for name, cb in _circuit_breakers.items()}


def reset_all_circuit_breakers():
    """Reset all circuit breakers"""
    logger.info("🔄 Resetting all circuit breakers")
    for cb in _circuit_breakers.values():
        cb.reset()