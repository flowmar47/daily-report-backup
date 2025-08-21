"""Structured logging configuration for the forex signal system."""

import logging
import logging.config
import sys
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime
import json
import os


class JSONFormatter(logging.Formatter):
    """Custom JSON formatter for structured logging."""
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON."""
        log_entry = {
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno,
        }
        
        # Add exception info if present
        if record.exc_info:
            log_entry['exception'] = self.formatException(record.exc_info)
        
        # Add extra fields from record
        for key, value in record.__dict__.items():
            if key not in {
                'name', 'msg', 'args', 'levelname', 'levelno', 'pathname',
                'filename', 'module', 'lineno', 'funcName', 'created',
                'msecs', 'relativeCreated', 'thread', 'threadName',
                'processName', 'process', 'getMessage', 'exc_info',
                'exc_text', 'stack_info'
            }:
                log_entry[key] = value
        
        return json.dumps(log_entry, default=str)


class ColoredFormatter(logging.Formatter):
    """Colored formatter for console output."""
    
    # Color codes
    COLORS = {
        'DEBUG': '\033[36m',     # Cyan
        'INFO': '\033[32m',      # Green
        'WARNING': '\033[33m',   # Yellow
        'ERROR': '\033[31m',     # Red
        'CRITICAL': '\033[35m',  # Magenta
        'RESET': '\033[0m'       # Reset
    }
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record with colors."""
        # Add color to level name
        level_color = self.COLORS.get(record.levelname, '')
        reset_color = self.COLORS['RESET']
        
        # Create colored level name
        colored_level = f"{level_color}{record.levelname:8}{reset_color}"
        
        # Format timestamp
        timestamp = datetime.fromtimestamp(record.created).strftime('%Y-%m-%d %H:%M:%S')
        
        # Format message
        message = record.getMessage()
        
        # Add exception info if present
        if record.exc_info:
            message += '\n' + self.formatException(record.exc_info)
        
        return f"{timestamp} | {colored_level} | {record.name:20} | {message}"


class LoggingConfig:
    """Centralized logging configuration."""
    
    def __init__(self, 
                 log_level: str = 'INFO',
                 log_dir: str = 'logs',
                 app_name: str = 'forex_signals',
                 enable_json_logging: bool = True,
                 enable_console_logging: bool = True,
                 max_file_size: int = 10 * 1024 * 1024,  # 10MB
                 backup_count: int = 5):
        
        self.log_level = log_level.upper()
        self.log_dir = Path(log_dir)
        self.app_name = app_name
        self.enable_json_logging = enable_json_logging
        self.enable_console_logging = enable_console_logging
        self.max_file_size = max_file_size
        self.backup_count = backup_count
        
        # Create log directory if it doesn't exist
        self.log_dir.mkdir(exist_ok=True)
    
    def get_logging_config(self) -> Dict[str, Any]:
        """Get logging configuration dictionary."""
        config = {
            'version': 1,
            'disable_existing_loggers': False,
            'formatters': {
                'json': {
                    '()': JSONFormatter,
                },
                'colored': {
                    '()': ColoredFormatter,
                },
                'standard': {
                    'format': '%(asctime)s | %(levelname)-8s | %(name)-20s | %(message)s',
                    'datefmt': '%Y-%m-%d %H:%M:%S'
                }
            },
            'handlers': {},
            'loggers': {
                '': {  # Root logger
                    'level': self.log_level,
                    'handlers': [],
                    'propagate': False
                },
                'src': {  # Application logger
                    'level': self.log_level,
                    'handlers': [],
                    'propagate': False
                },
                'urllib3': {
                    'level': 'WARNING',
                    'handlers': [],
                    'propagate': True
                },
                'requests': {
                    'level': 'WARNING',
                    'handlers': [],
                    'propagate': True
                }
            }
        }
        
        handlers = []
        
        # Console handler
        if self.enable_console_logging:
            config['handlers']['console'] = {
                'class': 'logging.StreamHandler',
                'level': self.log_level,
                'formatter': 'colored' if sys.stdout.isatty() else 'standard',
                'stream': 'ext://sys.stdout'
            }
            handlers.append('console')
        
        # File handlers
        if self.enable_json_logging:
            # JSON log file for structured logging
            config['handlers']['json_file'] = {
                'class': 'logging.handlers.RotatingFileHandler',
                'level': self.log_level,
                'formatter': 'json',
                'filename': str(self.log_dir / f'{self.app_name}.json'),
                'maxBytes': self.max_file_size,
                'backupCount': self.backup_count,
                'encoding': 'utf-8'
            }
            handlers.append('json_file')
        
        # Standard text log file
        config['handlers']['text_file'] = {
            'class': 'logging.handlers.RotatingFileHandler',
            'level': self.log_level,
            'formatter': 'standard',
            'filename': str(self.log_dir / f'{self.app_name}.log'),
            'maxBytes': self.max_file_size,
            'backupCount': self.backup_count,
            'encoding': 'utf-8'
        }
        handlers.append('text_file')
        
        # Error-only log file
        config['handlers']['error_file'] = {
            'class': 'logging.handlers.RotatingFileHandler',
            'level': 'ERROR',
            'formatter': 'json' if self.enable_json_logging else 'standard',
            'filename': str(self.log_dir / f'{self.app_name}_errors.log'),
            'maxBytes': self.max_file_size,
            'backupCount': self.backup_count,
            'encoding': 'utf-8'
        }
        handlers.append('error_file')
        
        # Assign handlers to loggers
        config['loggers']['']['handlers'] = handlers
        config['loggers']['src']['handlers'] = handlers
        config['loggers']['urllib3']['handlers'] = ['error_file']
        config['loggers']['requests']['handlers'] = ['error_file']
        
        return config
    
    def setup_logging(self) -> None:
        """Setup logging configuration."""
        config = self.get_logging_config()
        logging.config.dictConfig(config)
        
        # Log startup message
        logger = logging.getLogger('src.core.logging')
        logger.info(f"Logging configured - Level: {self.log_level}, Dir: {self.log_dir}")


class StructuredLogger:
    """Wrapper for structured logging with additional context."""
    
    def __init__(self, name: str):
        self.logger = logging.getLogger(name)
        self.context = {}
    
    def add_context(self, **kwargs) -> 'StructuredLogger':
        """Add context to all log messages."""
        new_logger = StructuredLogger(self.logger.name)
        new_logger.context = {**self.context, **kwargs}
        new_logger.logger = self.logger
        return new_logger
    
    def _log(self, level: int, message: str, **kwargs):
        """Internal log method with context."""
        extra = {**self.context, **kwargs}
        self.logger.log(level, message, extra=extra)
    
    def debug(self, message: str, **kwargs):
        """Log debug message."""
        self._log(logging.DEBUG, message, **kwargs)
    
    def info(self, message: str, **kwargs):
        """Log info message."""
        self._log(logging.INFO, message, **kwargs)
    
    def warning(self, message: str, **kwargs):
        """Log warning message."""
        self._log(logging.WARNING, message, **kwargs)
    
    def error(self, message: str, **kwargs):
        """Log error message."""
        self._log(logging.ERROR, message, **kwargs)
    
    def critical(self, message: str, **kwargs):
        """Log critical message."""
        self._log(logging.CRITICAL, message, **kwargs)
    
    def exception(self, message: str, **kwargs):
        """Log exception with traceback."""
        kwargs['exc_info'] = True
        self._log(logging.ERROR, message, **kwargs)


# Performance logging decorator
def log_performance(logger: Optional[StructuredLogger] = None):
    """Decorator to log function performance."""
    def decorator(func):
        def wrapper(*args, **kwargs):
            import time
            
            perf_logger = logger or StructuredLogger(f'performance.{func.__module__}.{func.__name__}')
            
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                duration = time.time() - start_time
                
                perf_logger.info(
                    f"Function {func.__name__} completed",
                    function=func.__name__,
                    duration_ms=round(duration * 1000, 2),
                    status='success'
                )
                
                return result
                
            except Exception as e:
                duration = time.time() - start_time
                
                perf_logger.error(
                    f"Function {func.__name__} failed",
                    function=func.__name__,
                    duration_ms=round(duration * 1000, 2),
                    status='error',
                    error_type=type(e).__name__,
                    error_message=str(e)
                )
                
                raise
        
        return wrapper
    return decorator


# API call logging decorator
def log_api_call(api_name: str, logger: Optional[StructuredLogger] = None):
    """Decorator to log API calls."""
    def decorator(func):
        def wrapper(*args, **kwargs):
            import time
            
            api_logger = logger or StructuredLogger(f'api.{api_name}')
            
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                duration = time.time() - start_time
                
                api_logger.info(
                    f"API call to {api_name} successful",
                    api_name=api_name,
                    function=func.__name__,
                    duration_ms=round(duration * 1000, 2),
                    status='success'
                )
                
                return result
                
            except Exception as e:
                duration = time.time() - start_time
                
                api_logger.error(
                    f"API call to {api_name} failed",
                    api_name=api_name,
                    function=func.__name__,
                    duration_ms=round(duration * 1000, 2),
                    status='error',
                    error_type=type(e).__name__,
                    error_message=str(e)
                )
                
                raise
        
        return wrapper
    return decorator


# Initialize default logging configuration
def setup_default_logging(log_level: str = None) -> None:
    """Setup default logging configuration."""
    # Get log level from environment or use INFO as default
    if log_level is None:
        log_level = os.getenv('LOG_LEVEL', 'INFO')
    
    # Determine if we're in development mode
    is_development = os.getenv('ENVIRONMENT', 'production').lower() in ('development', 'dev', 'local')
    
    config = LoggingConfig(
        log_level=log_level,
        enable_json_logging=not is_development,  # Use JSON in production, text in development
        enable_console_logging=True
    )
    
    config.setup_logging()


# Convenience function to get a structured logger
def get_logger(name: str) -> StructuredLogger:
    """Get a structured logger instance."""
    return StructuredLogger(name)