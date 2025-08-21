"""
Centralized logging configuration for forex signals system
Provides structured logging with correlation IDs and proper formatting
"""

import logging
import logging.config
import sys
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any
import json

from .config import get_settings


class CorrelationFilter(logging.Filter):
    """Add correlation ID to log records"""
    
    def filter(self, record):
        if not hasattr(record, 'correlation_id'):
            record.correlation_id = getattr(
                CorrelationFilter._local,
                'correlation_id',
                'N/A'
            )
        return True
    
    _local = None  # Thread-local storage for correlation IDs


class JsonFormatter(logging.Formatter):
    """JSON formatter for structured logging"""
    
    def format(self, record):
        log_data = {
            'timestamp': datetime.utcnow().isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno,
        }
        
        # Add correlation ID if available
        if hasattr(record, 'correlation_id'):
            log_data['correlation_id'] = record.correlation_id
        
        # Add exception info if present
        if record.exc_info:
            log_data['exception'] = self.formatException(record.exc_info)
        
        # Add extra fields from record
        for key, value in record.__dict__.items():
            if key not in [
                'name', 'msg', 'args', 'levelname', 'levelno', 'pathname',
                'filename', 'module', 'exc_info', 'exc_text', 'stack_info',
                'lineno', 'funcName', 'created', 'msecs', 'relativeCreated',
                'thread', 'threadName', 'processName', 'process', 'getMessage',
                'correlation_id', 'message'
            ]:
                log_data[key] = value
        
        return json.dumps(log_data, default=str)


def setup_logging(
    log_level: Optional[str] = None,
    log_dir: Optional[str] = None,
    enable_json: Optional[bool] = None
) -> None:
    """
    Setup centralized logging configuration
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR)
        log_dir: Directory for log files
        enable_json: Whether to use JSON formatting
    """
    settings = get_settings()
    
    # Use provided values or fall back to settings
    log_level = log_level or settings.log_level
    log_dir = Path(log_dir or settings.log_dir)
    enable_json = enable_json if enable_json is not None else settings.enable_json_logging
    
    # Create log directory
    log_dir.mkdir(exist_ok=True)
    
    # Define formatters
    json_formatter = JsonFormatter()
    console_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - [%(correlation_id)s] - %(message)s'
    )
    
    # Logging configuration
    config = {
        'version': 1,
        'disable_existing_loggers': False,
        'filters': {
            'correlation': {
                '()': CorrelationFilter,
            }
        },
        'formatters': {
            'json': {
                '()': JsonFormatter,
            },
            'console': {
                'format': '%(asctime)s - %(name)s - %(levelname)s - [%(correlation_id)s] - %(message)s'
            }
        },
        'handlers': {
            'console': {
                'class': 'logging.StreamHandler',
                'level': log_level,
                'formatter': 'console',
                'filters': ['correlation'],
                'stream': sys.stdout
            },
            'file': {
                'class': 'logging.handlers.RotatingFileHandler',
                'level': log_level,
                'formatter': 'json' if enable_json else 'console',
                'filters': ['correlation'],
                'filename': str(log_dir / 'forex_signals.log'),
                'maxBytes': 10485760,  # 10MB
                'backupCount': 5
            },
            'error_file': {
                'class': 'logging.handlers.RotatingFileHandler',
                'level': 'ERROR',
                'formatter': 'json' if enable_json else 'console',
                'filters': ['correlation'],
                'filename': str(log_dir / 'forex_signals_error.log'),
                'maxBytes': 10485760,  # 10MB
                'backupCount': 5
            }
        },
        'root': {
            'level': log_level,
            'handlers': ['console', 'file', 'error_file']
        },
        'loggers': {
            'forex_signals': {
                'level': log_level,
                'handlers': ['console', 'file', 'error_file'],
                'propagate': False
            },
            # Suppress noisy third-party loggers
            'urllib3': {'level': 'WARNING'},
            'requests': {'level': 'WARNING'},
            'asyncio': {'level': 'WARNING'},
        }
    }
    
    logging.config.dictConfig(config)


def get_logger(name: str = None) -> logging.Logger:
    """
    Get a logger instance with correlation support
    
    Args:
        name: Logger name, defaults to calling module
    
    Returns:
        Configured logger instance
    """
    if name is None:
        # Get the calling module's name
        import inspect
        frame = inspect.currentframe().f_back
        name = frame.f_globals.get('__name__', 'forex_signals')
    
    return logging.getLogger(name)


def set_correlation_id(correlation_id: Optional[str] = None) -> str:
    """
    Set correlation ID for current thread
    
    Args:
        correlation_id: Custom correlation ID, generates UUID if None
    
    Returns:
        The correlation ID that was set
    """
    if correlation_id is None:
        correlation_id = str(uuid.uuid4())
    
    # Store in thread-local storage
    import threading
    if not hasattr(CorrelationFilter, '_local') or CorrelationFilter._local is None:
        CorrelationFilter._local = threading.local()
    
    CorrelationFilter._local.correlation_id = correlation_id
    return correlation_id


def get_correlation_id() -> Optional[str]:
    """Get current correlation ID"""
    if hasattr(CorrelationFilter, '_local') and CorrelationFilter._local:
        return getattr(CorrelationFilter._local, 'correlation_id', None)
    return None


def clear_correlation_id() -> None:
    """Clear current correlation ID"""
    if hasattr(CorrelationFilter, '_local') and CorrelationFilter._local:
        if hasattr(CorrelationFilter._local, 'correlation_id'):
            delattr(CorrelationFilter._local, 'correlation_id')