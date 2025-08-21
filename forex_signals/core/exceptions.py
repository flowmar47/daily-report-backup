"""
Custom exception hierarchy for forex signals system
Provides specific error types for better error handling and debugging
"""

from typing import Optional, Dict, Any


class ForexSignalsError(Exception):
    """Base exception for all forex signals errors"""
    
    def __init__(
        self, 
        message: str,
        error_code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        self.message = message
        self.error_code = error_code
        self.details = details or {}
        super().__init__(self.message)
    
    def __str__(self) -> str:
        parts = [self.message]
        if self.error_code:
            parts.append(f"Error Code: {self.error_code}")
        if self.details:
            parts.append(f"Details: {self.details}")
        return " | ".join(parts)


class ConfigurationError(ForexSignalsError):
    """Raised when configuration is invalid or missing"""
    pass


class APIError(ForexSignalsError):
    """Raised when external API calls fail"""
    
    def __init__(
        self, 
        message: str,
        api_name: str,
        status_code: Optional[int] = None,
        response_text: Optional[str] = None,
        **kwargs
    ):
        self.api_name = api_name
        self.status_code = status_code
        self.response_text = response_text
        
        details = {
            "api_name": api_name,
            "status_code": status_code,
            "response_text": response_text
        }
        details.update(kwargs)
        
        super().__init__(message, details=details)


class DataFetchError(ForexSignalsError):
    """Raised when data fetching operations fail"""
    
    def __init__(
        self,
        message: str,
        pair: Optional[str] = None,
        source: Optional[str] = None,
        **kwargs
    ):
        self.pair = pair
        self.source = source
        
        details = {
            "pair": pair,
            "source": source
        }
        details.update(kwargs)
        
        super().__init__(message, details=details)


class ValidationError(ForexSignalsError):
    """Raised when data validation fails"""
    
    def __init__(
        self,
        message: str,
        field: Optional[str] = None,
        value: Optional[Any] = None,
        expected: Optional[str] = None,
        **kwargs
    ):
        self.field = field
        self.value = value
        self.expected = expected
        
        details = {
            "field": field,
            "value": value,
            "expected": expected
        }
        details.update(kwargs)
        
        super().__init__(message, details=details)


class MessagingError(ForexSignalsError):
    """Raised when messaging operations fail"""
    
    def __init__(
        self,
        message: str,
        platform: Optional[str] = None,
        recipient: Optional[str] = None,
        **kwargs
    ):
        self.platform = platform
        self.recipient = recipient
        
        details = {
            "platform": platform,
            "recipient": recipient
        }
        details.update(kwargs)
        
        super().__init__(message, details=details)


class RateLimitError(APIError):
    """Raised when API rate limits are exceeded"""
    
    def __init__(
        self,
        message: str,
        api_name: str,
        retry_after: Optional[int] = None,
        **kwargs
    ):
        self.retry_after = retry_after
        super().__init__(
            message, 
            api_name, 
            status_code=429,
            retry_after=retry_after,
            **kwargs
        )


class AuthenticationError(APIError):
    """Raised when API authentication fails"""
    
    def __init__(self, message: str, api_name: str, **kwargs):
        super().__init__(
            message,
            api_name,
            status_code=401,
            **kwargs
        )


class NetworkError(ForexSignalsError):
    """Raised when network operations fail"""
    
    def __init__(
        self,
        message: str,
        url: Optional[str] = None,
        timeout: Optional[int] = None,
        **kwargs
    ):
        self.url = url
        self.timeout = timeout
        
        details = {
            "url": url,
            "timeout": timeout
        }
        details.update(kwargs)
        
        super().__init__(message, details=details)


class DataQualityError(ValidationError):
    """Raised when data quality checks fail (e.g., fake prices detected)"""
    
    def __init__(
        self,
        message: str,
        pair: str,
        price: float,
        reason: str,
        **kwargs
    ):
        self.pair = pair
        self.price = price
        self.reason = reason
        
        details = {
            "pair": pair,
            "price": price,
            "reason": reason
        }
        details.update(kwargs)
        
        super().__init__(message, field="price", value=price, **details)