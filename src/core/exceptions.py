class ForexSignalException(Exception):
    """Base exception for the forex signal generation system."""
    def __init__(self, message: str, error_code: str = None, details: dict = None):
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.details = details or {}


# API Related Exceptions
class APIException(ForexSignalException):
    """Base exception for API-related errors."""
    pass


class APIKeyNotFound(APIException):
    """Raised when an API key is not found."""
    def __init__(self, api_name: str):
        super().__init__(
            f"API key not found for {api_name}",
            error_code="API_KEY_MISSING",
            details={"api_name": api_name}
        )


class InvalidAPICredentials(APIException):
    """Raised when API credentials are invalid."""
    def __init__(self, api_name: str, status_code: int = None):
        super().__init__(
            f"Invalid API credentials for {api_name}",
            error_code="API_CREDENTIALS_INVALID",
            details={"api_name": api_name, "status_code": status_code}
        )


class APIRateLimitExceeded(APIException):
    """Raised when API rate limit is exceeded."""
    def __init__(self, api_name: str, retry_after: int = None):
        super().__init__(
            f"Rate limit exceeded for {api_name}",
            error_code="API_RATE_LIMIT_EXCEEDED",
            details={"api_name": api_name, "retry_after": retry_after}
        )


class APITimeoutError(APIException):
    """Raised when API request times out."""
    def __init__(self, api_name: str, timeout_duration: float):
        super().__init__(
            f"API request timeout for {api_name} after {timeout_duration}s",
            error_code="API_TIMEOUT",
            details={"api_name": api_name, "timeout_duration": timeout_duration}
        )


class APIResponseError(APIException):
    """Raised when API returns an error response."""
    def __init__(self, api_name: str, status_code: int, response_text: str = None):
        super().__init__(
            f"API error response from {api_name}: {status_code}",
            error_code="API_RESPONSE_ERROR",
            details={"api_name": api_name, "status_code": status_code, "response_text": response_text}
        )


# Data Related Exceptions
class DataException(ForexSignalException):
    """Base exception for data-related errors."""
    pass


class DataNotFound(DataException):
    """Raised when required data is not found."""
    def __init__(self, data_type: str, identifier: str = None):
        super().__init__(
            f"Data not found: {data_type}" + (f" ({identifier})" if identifier else ""),
            error_code="DATA_NOT_FOUND",
            details={"data_type": data_type, "identifier": identifier}
        )


class DataValidationError(DataException):
    """Raised when data validation fails."""
    def __init__(self, field: str, value: str, expected: str = None):
        super().__init__(
            f"Invalid data for field '{field}': {value}" + (f" (expected: {expected})" if expected else ""),
            error_code="DATA_VALIDATION_ERROR",
            details={"field": field, "value": value, "expected": expected}
        )


class InsufficientDataError(DataException):
    """Raised when there's insufficient data for analysis."""
    def __init__(self, data_type: str, required_count: int, actual_count: int):
        super().__init__(
            f"Insufficient {data_type} data: need {required_count}, got {actual_count}",
            error_code="INSUFFICIENT_DATA",
            details={"data_type": data_type, "required_count": required_count, "actual_count": actual_count}
        )


# Configuration Exceptions
class ConfigurationException(ForexSignalException):
    """Base exception for configuration-related errors."""
    pass


class InvalidConfigurationError(ConfigurationException):
    """Raised when configuration is invalid."""
    def __init__(self, config_key: str, reason: str = None):
        super().__init__(
            f"Invalid configuration for '{config_key}'" + (f": {reason}" if reason else ""),
            error_code="INVALID_CONFIGURATION",
            details={"config_key": config_key, "reason": reason}
        )


class MissingConfigurationError(ConfigurationException):
    """Raised when required configuration is missing."""
    def __init__(self, config_key: str):
        super().__init__(
            f"Missing required configuration: {config_key}",
            error_code="MISSING_CONFIGURATION",
            details={"config_key": config_key}
        )


# Signal Generation Exceptions
class SignalException(ForexSignalException):
    """Base exception for signal generation errors."""
    pass


class SignalGenerationError(SignalException):
    """Raised when signal generation fails."""
    def __init__(self, pair: str, reason: str = None):
        super().__init__(
            f"Failed to generate signal for {pair}" + (f": {reason}" if reason else ""),
            error_code="SIGNAL_GENERATION_ERROR",
            details={"pair": pair, "reason": reason}
        )


class InvalidCurrencyPairError(SignalException):
    """Raised when currency pair format is invalid."""
    def __init__(self, pair: str):
        super().__init__(
            f"Invalid currency pair format: {pair}",
            error_code="INVALID_CURRENCY_PAIR",
            details={"pair": pair}
        )


# Cache Exceptions
class CacheException(ForexSignalException):
    """Base exception for cache-related errors."""
    pass


class CacheConnectionError(CacheException):
    """Raised when cache connection fails."""
    def __init__(self, cache_type: str, reason: str = None):
        super().__init__(
            f"Cache connection failed for {cache_type}" + (f": {reason}" if reason else ""),
            error_code="CACHE_CONNECTION_ERROR",
            details={"cache_type": cache_type, "reason": reason}
        )


# Analysis Exceptions
class AnalysisException(ForexSignalException):
    """Base exception for analysis-related errors."""
    pass


class TechnicalAnalysisError(AnalysisException):
    """Raised when technical analysis fails."""
    def __init__(self, indicator: str, reason: str = None):
        super().__init__(
            f"Technical analysis failed for {indicator}" + (f": {reason}" if reason else ""),
            error_code="TECHNICAL_ANALYSIS_ERROR",
            details={"indicator": indicator, "reason": reason}
        )


class SentimentAnalysisError(AnalysisException):
    """Raised when sentiment analysis fails."""
    def __init__(self, source: str, reason: str = None):
        super().__init__(
            f"Sentiment analysis failed for {source}" + (f": {reason}" if reason else ""),
            error_code="SENTIMENT_ANALYSIS_ERROR",
            details={"source": source, "reason": reason}
        )


class EconomicAnalysisError(AnalysisException):
    """Raised when economic analysis fails."""
    def __init__(self, currency: str, reason: str = None):
        super().__init__(
            f"Economic analysis failed for {currency}" + (f": {reason}" if reason else ""),
            error_code="ECONOMIC_ANALYSIS_ERROR",
            details={"currency": currency, "reason": reason}
        )