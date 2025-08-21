#!/usr/bin/env python3
"""
Circuit Breaker Pattern Implementation for OhmsAlertsReports
Provides resilient error handling and automatic recovery for external service calls
"""

import asyncio
import functools
import logging
import time
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Union
from dataclasses import dataclass, field
import threading
from collections import deque, defaultdict
import json

logger = logging.getLogger(__name__)

class CircuitState(Enum):
    """Circuit breaker states"""
    CLOSED = "closed"       # Normal operation
    OPEN = "open"          # Failing, requests blocked
    HALF_OPEN = "half_open" # Testing if service recovered

@dataclass
class CircuitBreakerConfig:
    """Configuration for circuit breaker"""
    failure_threshold: int = 5          # Failures before opening
    recovery_timeout: int = 60          # Seconds before trying half-open
    success_threshold: int = 3          # Successes needed to close from half-open
    timeout: float = 30.0               # Request timeout in seconds
    excluded_exceptions: List[type] = field(default_factory=list)  # Exceptions to ignore
    
    # Advanced settings
    max_failures_window: int = 300      # Time window for failure counting (seconds)
    exponential_backoff: bool = True    # Use exponential backoff for recovery
    max_recovery_timeout: int = 1800    # Maximum recovery timeout (30 minutes)

@dataclass
class CircuitStats:
    """Circuit breaker statistics"""
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    timeouts: int = 0
    circuit_opened_count: int = 0
    circuit_closed_count: int = 0
    current_failure_streak: int = 0
    last_failure_time: Optional[float] = None
    last_success_time: Optional[float] = None
    state_changed_at: Optional[float] = None
    
    def success_rate(self) -> float:
        """Calculate success rate percentage"""
        return (self.successful_requests / max(1, self.total_requests)) * 100

class CircuitBreaker:
    """Circuit breaker implementation with advanced features"""
    
    def __init__(self, name: str, config: CircuitBreakerConfig = None):
        self.name = name
        self.config = config or CircuitBreakerConfig()
        
        # State management
        self._state = CircuitState.CLOSED
        self._stats = CircuitStats()
        self._lock = threading.RLock()
        
        # Failure tracking
        self._failure_times = deque()  # Track failure timestamps
        self._recovery_attempt_count = 0
        
        # Monitoring
        self._state_listeners: List[Callable] = []
        
        logger.info(f"🔌 Circuit breaker '{name}' initialized in {self._state.value} state")
    
    @property
    def state(self) -> CircuitState:
        """Get current circuit state"""
        return self._state
    
    @property
    def stats(self) -> CircuitStats:
        """Get circuit statistics"""
        return self._stats
    
    def add_state_listener(self, listener: Callable[[str, CircuitState, CircuitState], None]):
        """Add a listener for state changes"""
        self._state_listeners.append(listener)
    
    def _change_state(self, new_state: CircuitState):
        """Change circuit state and notify listeners"""
        with self._lock:
            old_state = self._state
            self._state = new_state
            self._stats.state_changed_at = time.time()
            
            # Update state-specific counters
            if new_state == CircuitState.OPEN:
                self._stats.circuit_opened_count += 1
            elif new_state == CircuitState.CLOSED:
                self._stats.circuit_closed_count += 1
                self._recovery_attempt_count = 0
            
            logger.info(f"🔄 Circuit '{self.name}': {old_state.value} → {new_state.value}")
            
            # Notify listeners
            for listener in self._state_listeners:
                try:
                    listener(self.name, old_state, new_state)
                except Exception as e:
                    logger.warning(f"State listener error: {e}")
    
    def _should_open(self) -> bool:
        """Check if circuit should open due to failures"""
        with self._lock:
            # Clean old failures outside the time window
            current_time = time.time()
            cutoff_time = current_time - self.config.max_failures_window
            
            while self._failure_times and self._failure_times[0] < cutoff_time:
                self._failure_times.popleft()
            
            # Check if failure threshold exceeded
            return len(self._failure_times) >= self.config.failure_threshold
    
    def _should_attempt_reset(self) -> bool:
        """Check if circuit should attempt to reset (closed → half-open)"""
        if self._state != CircuitState.OPEN:
            return False
        
        if not self._stats.last_failure_time:
            return True
        
        # Calculate recovery timeout with exponential backoff
        base_timeout = self.config.recovery_timeout
        if self.config.exponential_backoff:
            backoff_multiplier = min(2 ** self._recovery_attempt_count, 8)  # Max 8x
            actual_timeout = min(base_timeout * backoff_multiplier, self.config.max_recovery_timeout)
        else:
            actual_timeout = base_timeout
        
        elapsed = time.time() - self._stats.last_failure_time
        return elapsed >= actual_timeout
    
    def _record_success(self):
        """Record a successful operation"""
        with self._lock:
            self._stats.total_requests += 1
            self._stats.successful_requests += 1
            self._stats.current_failure_streak = 0
            self._stats.last_success_time = time.time()
            
            if self._state == CircuitState.HALF_OPEN:
                # Count successes in half-open state
                consecutive_successes = (self._stats.successful_requests - 
                                       (self._stats.total_requests - self.config.success_threshold))
                
                if consecutive_successes >= self.config.success_threshold:
                    self._change_state(CircuitState.CLOSED)
    
    def _record_failure(self, exception: Exception):
        """Record a failed operation"""
        with self._lock:
            # Check if this exception should be ignored
            if any(isinstance(exception, exc_type) for exc_type in self.config.excluded_exceptions):
                logger.debug(f"Ignoring excluded exception: {type(exception).__name__}")
                return
            
            self._stats.total_requests += 1
            self._stats.failed_requests += 1
            self._stats.current_failure_streak += 1
            self._stats.last_failure_time = time.time()
            
            # Record failure timestamp
            self._failure_times.append(time.time())
            
            # Check if circuit should open
            if self._state == CircuitState.CLOSED and self._should_open():
                self._change_state(CircuitState.OPEN)
            elif self._state == CircuitState.HALF_OPEN:
                # Any failure in half-open state reopens the circuit
                self._change_state(CircuitState.OPEN)
                self._recovery_attempt_count += 1
    
    def _record_timeout(self):
        """Record a timeout"""
        with self._lock:
            self._stats.timeouts += 1
    
    def call(self, func: Callable, *args, **kwargs) -> Any:
        """Execute function with circuit breaker protection"""
        # Check if circuit allows request
        with self._lock:
            if self._state == CircuitState.OPEN:
                if self._should_attempt_reset():
                    self._change_state(CircuitState.HALF_OPEN)
                    logger.info(f"🔄 Circuit '{self.name}' attempting reset (half-open)")
                else:
                    raise CircuitBreakerOpenError(f"Circuit '{self.name}' is open")
        
        # Execute the function
        start_time = time.time()
        try:
            # Apply timeout if configured
            if hasattr(func, '__call__'):
                if asyncio.iscoroutinefunction(func):
                    # Async function
                    result = asyncio.wait_for(
                        func(*args, **kwargs), 
                        timeout=self.config.timeout
                    )
                else:
                    # Sync function - use threading for timeout
                    import concurrent.futures
                    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
                        future = executor.submit(func, *args, **kwargs)
                        result = future.result(timeout=self.config.timeout)
            else:
                result = func(*args, **kwargs)
            
            self._record_success()
            execution_time = time.time() - start_time
            logger.debug(f"✅ Circuit '{self.name}' call succeeded in {execution_time:.3f}s")
            return result
            
        except asyncio.TimeoutError:
            self._record_timeout()
            self._record_failure(TimeoutError("Function call timed out"))
            raise CircuitBreakerTimeoutError(f"Circuit '{self.name}' call timed out after {self.config.timeout}s")
        
        except Exception as e:
            self._record_failure(e)
            execution_time = time.time() - start_time
            logger.warning(f"❌ Circuit '{self.name}' call failed in {execution_time:.3f}s: {e}")
            raise
    
    async def call_async(self, func: Callable, *args, **kwargs) -> Any:
        """Execute async function with circuit breaker protection"""
        # Check if circuit allows request
        with self._lock:
            if self._state == CircuitState.OPEN:
                if self._should_attempt_reset():
                    self._change_state(CircuitState.HALF_OPEN)
                    logger.info(f"🔄 Circuit '{self.name}' attempting reset (half-open)")
                else:
                    raise CircuitBreakerOpenError(f"Circuit '{self.name}' is open")
        
        # Execute the async function
        start_time = time.time()
        try:
            result = await asyncio.wait_for(
                func(*args, **kwargs), 
                timeout=self.config.timeout
            )
            
            self._record_success()
            execution_time = time.time() - start_time
            logger.debug(f"✅ Circuit '{self.name}' async call succeeded in {execution_time:.3f}s")
            return result
            
        except asyncio.TimeoutError:
            self._record_timeout()
            self._record_failure(TimeoutError("Async function call timed out"))
            raise CircuitBreakerTimeoutError(f"Circuit '{self.name}' async call timed out after {self.config.timeout}s")
        
        except Exception as e:
            self._record_failure(e)
            execution_time = time.time() - start_time
            logger.warning(f"❌ Circuit '{self.name}' async call failed in {execution_time:.3f}s: {e}")
            raise
    
    def get_health_status(self) -> Dict[str, Any]:
        """Get detailed health status"""
        with self._lock:
            return {
                'name': self.name,
                'state': self._state.value,
                'healthy': self._state in [CircuitState.CLOSED, CircuitState.HALF_OPEN],
                'stats': {
                    'total_requests': self._stats.total_requests,
                    'success_rate': round(self._stats.success_rate(), 2),
                    'failure_streak': self._stats.current_failure_streak,
                    'circuit_opens': self._stats.circuit_opened_count,
                    'timeouts': self._stats.timeouts
                },
                'config': {
                    'failure_threshold': self.config.failure_threshold,
                    'recovery_timeout': self.config.recovery_timeout,
                    'timeout': self.config.timeout
                },
                'last_state_change': self._stats.state_changed_at,
                'recovery_attempts': self._recovery_attempt_count
            }

class CircuitBreakerOpenError(Exception):
    """Raised when circuit breaker is open"""
    pass

class CircuitBreakerTimeoutError(Exception):
    """Raised when circuit breaker call times out"""
    pass

# Decorator implementations
def circuit_breaker(name: str, config: CircuitBreakerConfig = None):
    """Decorator to apply circuit breaker to a function"""
    def decorator(func: Callable) -> Callable:
        cb = CircuitBreaker(name, config)
        
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            return cb.call(func, *args, **kwargs)
        
        # Attach circuit breaker to function for monitoring
        wrapper._circuit_breaker = cb
        return wrapper
    
    return decorator

def async_circuit_breaker(name: str, config: CircuitBreakerConfig = None):
    """Decorator to apply circuit breaker to an async function"""
    def decorator(func: Callable) -> Callable:
        cb = CircuitBreaker(name, config)
        
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            return await cb.call_async(func, *args, **kwargs)
        
        # Attach circuit breaker to function for monitoring
        wrapper._circuit_breaker = cb
        return wrapper
    
    return decorator

# Circuit breaker registry
class CircuitBreakerRegistry:
    """Registry to manage multiple circuit breakers"""
    
    def __init__(self):
        self._breakers: Dict[str, CircuitBreaker] = {}
        self._lock = threading.RLock()
    
    def register(self, name: str, config: CircuitBreakerConfig = None) -> CircuitBreaker:
        """Register a new circuit breaker"""
        with self._lock:
            if name in self._breakers:
                logger.warning(f"Circuit breaker '{name}' already exists")
                return self._breakers[name]
            
            breaker = CircuitBreaker(name, config)
            self._breakers[name] = breaker
            logger.info(f"🔌 Registered circuit breaker: {name}")
            return breaker
    
    def get(self, name: str) -> Optional[CircuitBreaker]:
        """Get circuit breaker by name"""
        return self._breakers.get(name)
    
    def get_all_status(self) -> Dict[str, Dict[str, Any]]:
        """Get status of all circuit breakers"""
        with self._lock:
            return {name: cb.get_health_status() for name, cb in self._breakers.items()}
    
    def reset_all(self):
        """Reset all circuit breakers to closed state"""
        with self._lock:
            for cb in self._breakers.values():
                cb._change_state(CircuitState.CLOSED)
                cb._stats = CircuitStats()
                cb._failure_times.clear()
            logger.info("🔄 All circuit breakers reset")
    
    def export_metrics(self) -> Dict[str, Any]:
        """Export metrics for monitoring systems"""
        metrics = {
            'timestamp': time.time(),
            'circuit_breakers': {},
            'summary': {
                'total_breakers': len(self._breakers),
                'open_breakers': 0,
                'healthy_breakers': 0,
                'total_requests': 0,
                'total_failures': 0
            }
        }
        
        for name, cb in self._breakers.items():
            status = cb.get_health_status()
            metrics['circuit_breakers'][name] = status
            
            # Update summary
            if status['state'] == 'open':
                metrics['summary']['open_breakers'] += 1
            if status['healthy']:
                metrics['summary']['healthy_breakers'] += 1
            
            metrics['summary']['total_requests'] += status['stats']['total_requests']
            metrics['summary']['total_failures'] += cb._stats.failed_requests
        
        return metrics

# Global registry
_global_registry = CircuitBreakerRegistry()

def get_circuit_breaker(name: str, config: CircuitBreakerConfig = None) -> CircuitBreaker:
    """Get or create a circuit breaker from global registry"""
    breaker = _global_registry.get(name)
    if breaker is None:
        breaker = _global_registry.register(name, config)
    return breaker

def get_all_circuit_breakers() -> Dict[str, Dict[str, Any]]:
    """Get status of all circuit breakers"""
    return _global_registry.get_all_status()

def reset_all_circuit_breakers():
    """Reset all circuit breakers"""
    _global_registry.reset_all()

# Example usage and testing
async def test_circuit_breaker():
    """Test circuit breaker functionality"""
    logger.info("🧪 Testing circuit breaker functionality...")
    
    # Create test circuit breaker
    config = CircuitBreakerConfig(
        failure_threshold=3,
        recovery_timeout=5,
        success_threshold=2,
        timeout=2.0
    )
    
    cb = CircuitBreaker("test_service", config)
    
    # Test function that sometimes fails
    async def flaky_service(should_fail: bool = False):
        await asyncio.sleep(0.1)  # Simulate work
        if should_fail:
            raise Exception("Service unavailable")
        return "Success"
    
    # Test successful calls
    print("Testing successful calls...")
    for i in range(3):
        try:
            result = await cb.call_async(flaky_service, should_fail=False)
            print(f"  ✅ Call {i+1}: {result}")
        except Exception as e:
            print(f"  ❌ Call {i+1}: {e}")
    
    # Test failing calls (should open circuit)
    print("\nTesting failing calls...")
    for i in range(5):
        try:
            result = await cb.call_async(flaky_service, should_fail=True)
            print(f"  ✅ Call {i+1}: {result}")
        except CircuitBreakerOpenError as e:
            print(f"  🔌 Call {i+1}: Circuit open - {e}")
        except Exception as e:
            print(f"  ❌ Call {i+1}: {e}")
    
    # Show circuit status
    status = cb.get_health_status()
    print(f"\n📊 Circuit Status: {status['state']}")
    print(f"   Success rate: {status['stats']['success_rate']}%")
    print(f"   Failure streak: {status['stats']['failure_streak']}")
    
    # Wait for recovery and test
    print(f"\n⏰ Waiting {config.recovery_timeout}s for recovery...")
    await asyncio.sleep(config.recovery_timeout + 1)
    
    print("Testing recovery...")
    try:
        result = await cb.call_async(flaky_service, should_fail=False)
        print(f"  ✅ Recovery call: {result}")
    except Exception as e:
        print(f"  ❌ Recovery call: {e}")
    
    final_status = cb.get_health_status()
    print(f"\n📊 Final Status: {final_status['state']}")
    
    return cb

def main():
    """Main test function"""
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    
    print("🔌 CIRCUIT BREAKER PATTERN IMPLEMENTATION")
    print("=" * 50)
    
    # Run async test
    asyncio.run(test_circuit_breaker())
    
    # Show all circuit breakers
    all_status = get_all_circuit_breakers()
    print(f"\n📊 All Circuit Breakers ({len(all_status)}):")
    for name, status in all_status.items():
        print(f"   {name}: {status['state']} (success: {status['stats']['success_rate']}%)")

if __name__ == "__main__":
    main()