"""
Enhanced Error Handling Framework
"""

import logging
import functools
import traceback
from typing import Any, Callable, Optional, Dict
from datetime import datetime
import json

logger = logging.getLogger(__name__)

class ErrorSeverity:
    CRITICAL = "CRITICAL"  # System cannot continue
    HIGH = "HIGH"         # Major functionality affected
    MEDIUM = "MEDIUM"     # Some functionality affected
    LOW = "LOW"          # Minor issues, system continues

class ErrorHandler:
    """Centralized error handling with logging and recovery"""
    
    def __init__(self, log_file: str = "logs/error_details.log"):
        self.log_file = log_file
        self.error_counts = {}
        self.recovery_strategies = {}
        
    def register_recovery(self, error_type: type, strategy: Callable):
        """Register recovery strategy for specific error type"""
        self.recovery_strategies[error_type] = strategy
    
    def handle_error(self, error: Exception, context: str, 
                    severity: str = ErrorSeverity.MEDIUM,
                    recovery_data: Optional[Dict] = None) -> Optional[Any]:
        """
        Handle error with logging and optional recovery
        
        Args:
            error: The exception that occurred
            context: Context where error occurred
            severity: Error severity level
            recovery_data: Data needed for recovery
            
        Returns:
            Recovery result if successful, None otherwise
        """
        error_type = type(error).__name__
        error_key = f"{context}:{error_type}"
        
        # Track error frequency
        self.error_counts[error_key] = self.error_counts.get(error_key, 0) + 1
        
        # Log error details
        error_details = {
            'timestamp': datetime.now().isoformat(),
            'context': context,
            'error_type': error_type,
            'error_message': str(error),
            'severity': severity,
            'count': self.error_counts[error_key],
            'traceback': traceback.format_exc()
        }
        
        # Log to file
        try:
            with open(self.log_file, 'a') as f:
                f.write(json.dumps(error_details, indent=2) + '\n')
        except Exception as log_error:
            logger.error(f"Failed to log error details: {log_error}")
        
        # Log to standard logger
        log_method = {
            ErrorSeverity.CRITICAL: logger.critical,
            ErrorSeverity.HIGH: logger.error,
            ErrorSeverity.MEDIUM: logger.warning,
            ErrorSeverity.LOW: logger.info
        }.get(severity, logger.warning)
        
        log_method(f"[{severity}] {context}: {error_type} - {str(error)}")
        
        # Attempt recovery
        if type(error) in self.recovery_strategies:
            try:
                recovery_result = self.recovery_strategies[type(error)](
                    error, context, recovery_data
                )
                logger.info(f"Recovery successful for {error_type} in {context}")
                return recovery_result
            except Exception as recovery_error:
                logger.error(f"Recovery failed for {error_type}: {recovery_error}")
        
        return None
    
    def should_continue(self, error_key: str, max_errors: int = 5) -> bool:
        """Check if system should continue after repeated errors"""
        return self.error_counts.get(error_key, 0) < max_errors

def resilient_operation(context: str, severity: str = ErrorSeverity.MEDIUM,
                       max_retries: int = 3, fallback_result: Any = None):
    """
    Decorator for resilient operations with retry logic
    
    Args:
        context: Context description for logging
        severity: Error severity level
        max_retries: Maximum retry attempts
        fallback_result: Value to return if all retries fail
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            last_error = None
            
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_error = e
                    if attempt < max_retries:
                        wait_time = 2 ** attempt  # Exponential backoff
                        logger.warning(f"Attempt {attempt + 1} failed for {context}: {e}. "
                                     f"Retrying in {wait_time}s...")
                        import time
                        time.sleep(wait_time)
                    else:
                        error_handler.handle_error(e, context, severity)
            
            logger.error(f"All {max_retries + 1} attempts failed for {context}")
            return fallback_result
            
        return wrapper
    return decorator

# Global error handler instance
error_handler = ErrorHandler()

# Register common recovery strategies
def network_error_recovery(error, context, recovery_data):
    """Recovery strategy for network-related errors"""
    logger.info(f"Attempting network error recovery for {context}")
    import time
    time.sleep(5)  # Wait before retry
    return None

def import_error_recovery(error, context, recovery_data):
    """Recovery strategy for import errors"""
    logger.info(f"Using fallback implementation for {context}")
    return recovery_data.get('fallback_class') if recovery_data else None

error_handler.register_recovery(ConnectionError, network_error_recovery)
error_handler.register_recovery(ImportError, import_error_recovery)