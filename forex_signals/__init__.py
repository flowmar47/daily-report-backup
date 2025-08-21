"""
Forex Signals Package
Professional forex signal generation and messaging system
"""

__version__ = "2.0.0"
__author__ = "Forex Signal System"
__description__ = "Professional forex signal generation with multi-API integration"

# Package-level imports for easier access
from .core.config import Settings, get_settings
from .core.exceptions import (
    ForexSignalsError,
    ConfigurationError,
    APIError,
    ValidationError
)

__all__ = [
    "Settings",
    "get_settings", 
    "ForexSignalsError",
    "ConfigurationError",
    "APIError",
    "ValidationError"
]