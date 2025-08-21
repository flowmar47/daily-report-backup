"""
Retry logic utilities with exponential backoff
"""

import asyncio
import random
from typing import Callable, Any, Optional, Type, Union, Tuple
from functools import wraps

from ..core.logging import get_logger
from ..core.exceptions import ForexSignalsError

logger = get_logger(__name__)


class RetryManager:
    """
    Manages retry logic with exponential backoff and jitter
    """
    
    def __init__(
        self,
        max_attempts: int = 3,
        base_delay: float = 1.0,
        max_delay: float = 60.0,
        exponential_base: float = 2.0,
        jitter: bool = True,
        exceptions: Tuple[Type[Exception], ...] = (Exception,)
    ):
        """
        Initialize retry manager
        
        Args:
            max_attempts: Maximum number of retry attempts
            base_delay: Base delay in seconds
            max_delay: Maximum delay in seconds
            exponential_base: Base for exponential backoff
            jitter: Whether to add random jitter
            exceptions: Exception types that trigger retry
        """
        self.max_attempts = max_attempts
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.exponential_base = exponential_base
        self.jitter = jitter
        self.exceptions = exceptions
    
    def calculate_delay(self, attempt: int) -> float:
        """
        Calculate delay for given attempt number
        
        Args:
            attempt: Attempt number (0-based)
            
        Returns:
            Delay in seconds
        """
        # Exponential backoff
        delay = self.base_delay * (self.exponential_base ** attempt)
        
        # Cap at max delay
        delay = min(delay, self.max_delay)
        
        # Add jitter if enabled
        if self.jitter:
            # Add random jitter up to 25% of delay
            jitter_amount = delay * 0.25 * random.random()
            delay += jitter_amount
        
        return delay
    
    async def execute_async(
        self,
        func: Callable,
        *args,
        **kwargs
    ) -> Any:
        """
        Execute async function with retry logic
        
        Args:
            func: Async function to execute
            *args: Function arguments
            **kwargs: Function keyword arguments
            
        Returns:
            Function result
            
        Raises:
            Exception: Last exception if all retries fail
        """
        last_exception = None
        
        for attempt in range(self.max_attempts):
            try:
                result = await func(*args, **kwargs)
                
                if attempt > 0:
                    logger.info(f"✅ Retry successful on attempt {attempt + 1}")
                
                return result
                
            except self.exceptions as e:
                last_exception = e
                
                if attempt == self.max_attempts - 1:
                    # Last attempt failed
                    logger.error(f"❌ All {self.max_attempts} retry attempts failed")
                    break
                
                delay = self.calculate_delay(attempt)
                logger.warning(f"⚠️ Attempt {attempt + 1} failed: {str(e)[:100]}. Retrying in {delay:.2f}s...")
                
                await asyncio.sleep(delay)
            
            except Exception as e:
                # Non-retryable exception
                logger.error(f"❌ Non-retryable exception: {type(e).__name__}: {str(e)[:100]}")
                raise
        
        # All retries failed
        if last_exception:
            raise last_exception
        else:
            raise ForexSignalsError("Retry failed with unknown error")
    
    def execute_sync(
        self,
        func: Callable,
        *args,
        **kwargs
    ) -> Any:
        """
        Execute sync function with retry logic
        
        Args:
            func: Sync function to execute
            *args: Function arguments
            **kwargs: Function keyword arguments
            
        Returns:
            Function result
            
        Raises:
            Exception: Last exception if all retries fail
        """
        import time
        
        last_exception = None
        
        for attempt in range(self.max_attempts):
            try:
                result = func(*args, **kwargs)
                
                if attempt > 0:
                    logger.info(f"✅ Retry successful on attempt {attempt + 1}")
                
                return result
                
            except self.exceptions as e:
                last_exception = e
                
                if attempt == self.max_attempts - 1:
                    # Last attempt failed
                    logger.error(f"❌ All {self.max_attempts} retry attempts failed")
                    break
                
                delay = self.calculate_delay(attempt)
                logger.warning(f"⚠️ Attempt {attempt + 1} failed: {str(e)[:100]}. Retrying in {delay:.2f}s...")
                
                time.sleep(delay)
            
            except Exception as e:
                # Non-retryable exception
                logger.error(f"❌ Non-retryable exception: {type(e).__name__}: {str(e)[:100]}")
                raise
        
        # All retries failed
        if last_exception:
            raise last_exception
        else:
            raise ForexSignalsError("Retry failed with unknown error")


def retry_with_backoff(
    max_attempts: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    exponential_base: float = 2.0,
    jitter: bool = True,
    exceptions: Tuple[Type[Exception], ...] = (Exception,)
):
    """
    Decorator for automatic retry with exponential backoff
    
    Args:
        max_attempts: Maximum number of retry attempts
        base_delay: Base delay in seconds
        max_delay: Maximum delay in seconds
        exponential_base: Base for exponential backoff
        jitter: Whether to add random jitter
        exceptions: Exception types that trigger retry
    
    Returns:
        Decorated function
    """
    def decorator(func: Callable) -> Callable:
        retry_manager = RetryManager(
            max_attempts=max_attempts,
            base_delay=base_delay,
            max_delay=max_delay,
            exponential_base=exponential_base,
            jitter=jitter,
            exceptions=exceptions
        )
        
        if asyncio.iscoroutinefunction(func):
            @wraps(func)
            async def async_wrapper(*args, **kwargs):
                return await retry_manager.execute_async(func, *args, **kwargs)
            return async_wrapper
        else:
            @wraps(func)
            def sync_wrapper(*args, **kwargs):
                return retry_manager.execute_sync(func, *args, **kwargs)
            return sync_wrapper
    
    return decorator


# Predefined retry configurations
api_retry = retry_with_backoff(
    max_attempts=3,
    base_delay=1.0,
    max_delay=30.0,
    exceptions=(ConnectionError, TimeoutError)
)

network_retry = retry_with_backoff(
    max_attempts=5,
    base_delay=0.5,
    max_delay=10.0,
    exceptions=(ConnectionError, TimeoutError, OSError)
)

database_retry = retry_with_backoff(
    max_attempts=3,
    base_delay=0.1,
    max_delay=5.0,
    exceptions=(ConnectionError, TimeoutError)
)