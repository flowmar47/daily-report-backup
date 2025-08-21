"""Unit tests for custom exception classes."""

import pytest

from src.core.exceptions import (
    ForexSignalException,
    APIException,
    APIKeyNotFound,
    InvalidAPICredentials,
    APIRateLimitExceeded,
    APITimeoutError,
    APIResponseError,
    DataException,
    DataNotFound,
    DataValidationError,
    InsufficientDataError,
    ConfigurationException,
    InvalidConfigurationError,
    MissingConfigurationError,
    SignalException,
    SignalGenerationError,
    InvalidCurrencyPairError,
    CacheException,
    CacheConnectionError,
    AnalysisException,
    TechnicalAnalysisError,
    SentimentAnalysisError,
    EconomicAnalysisError
)


class TestForexSignalException:
    """Test base ForexSignalException class."""
    
    def test_basic_exception(self):
        """Test basic exception creation."""
        exc = ForexSignalException("Test message")
        assert str(exc) == "Test message"
        assert exc.message == "Test message"
        assert exc.error_code is None
        assert exc.details == {}
    
    def test_exception_with_error_code(self):
        """Test exception with error code."""
        exc = ForexSignalException("Test message", error_code="TEST_ERROR")
        assert exc.error_code == "TEST_ERROR"
    
    def test_exception_with_details(self):
        """Test exception with details."""
        details = {"key": "value", "number": 123}
        exc = ForexSignalException("Test message", details=details)
        assert exc.details == details
    
    def test_exception_inheritance(self):
        """Test that ForexSignalException inherits from Exception."""
        exc = ForexSignalException("Test message")
        assert isinstance(exc, Exception)


class TestAPIExceptions:
    """Test API-related exceptions."""
    
    def test_api_key_not_found(self):
        """Test APIKeyNotFound exception."""
        exc = APIKeyNotFound("alpha_vantage")
        assert "API key not found for alpha_vantage" in str(exc)
        assert exc.error_code == "API_KEY_MISSING"
        assert exc.details["api_name"] == "alpha_vantage"
        assert isinstance(exc, APIException)
    
    def test_invalid_api_credentials(self):
        """Test InvalidAPICredentials exception."""
        exc = InvalidAPICredentials("twelve_data", status_code=401)
        assert "Invalid API credentials for twelve_data" in str(exc)
        assert exc.error_code == "API_CREDENTIALS_INVALID"
        assert exc.details["api_name"] == "twelve_data"
        assert exc.details["status_code"] == 401
    
    def test_api_rate_limit_exceeded(self):
        """Test APIRateLimitExceeded exception."""
        exc = APIRateLimitExceeded("fred", retry_after=60)
        assert "Rate limit exceeded for fred" in str(exc)
        assert exc.error_code == "API_RATE_LIMIT_EXCEEDED"
        assert exc.details["api_name"] == "fred"
        assert exc.details["retry_after"] == 60
    
    def test_api_timeout_error(self):
        """Test APITimeoutError exception."""
        exc = APITimeoutError("finnhub", timeout_duration=30.5)
        assert "API request timeout for finnhub after 30.5s" in str(exc)
        assert exc.error_code == "API_TIMEOUT"
        assert exc.details["api_name"] == "finnhub"
        assert exc.details["timeout_duration"] == 30.5
    
    def test_api_response_error(self):
        """Test APIResponseError exception."""
        exc = APIResponseError("news_api", status_code=500, response_text="Internal Server Error")
        assert "API error response from news_api: 500" in str(exc)
        assert exc.error_code == "API_RESPONSE_ERROR"
        assert exc.details["api_name"] == "news_api"
        assert exc.details["status_code"] == 500
        assert exc.details["response_text"] == "Internal Server Error"


class TestDataExceptions:
    """Test data-related exceptions."""
    
    def test_data_not_found(self):
        """Test DataNotFound exception."""
        exc = DataNotFound("forex_data", identifier="EURUSD")
        assert "Data not found: forex_data (EURUSD)" in str(exc)
        assert exc.error_code == "DATA_NOT_FOUND"
        assert exc.details["data_type"] == "forex_data"
        assert exc.details["identifier"] == "EURUSD"
    
    def test_data_not_found_without_identifier(self):
        """Test DataNotFound exception without identifier."""
        exc = DataNotFound("economic_data")
        assert "Data not found: economic_data" in str(exc)
        assert exc.details["identifier"] is None
    
    def test_data_validation_error(self):
        """Test DataValidationError exception."""
        exc = DataValidationError("price", "invalid", expected="numeric")
        assert "Invalid data for field 'price': invalid (expected: numeric)" in str(exc)
        assert exc.error_code == "DATA_VALIDATION_ERROR"
        assert exc.details["field"] == "price"
        assert exc.details["value"] == "invalid"
        assert exc.details["expected"] == "numeric"
    
    def test_insufficient_data_error(self):
        """Test InsufficientDataError exception."""
        exc = InsufficientDataError("price_points", required_count=100, actual_count=50)
        assert "Insufficient price_points data: need 100, got 50" in str(exc)
        assert exc.error_code == "INSUFFICIENT_DATA"
        assert exc.details["data_type"] == "price_points"
        assert exc.details["required_count"] == 100
        assert exc.details["actual_count"] == 50


class TestConfigurationExceptions:
    """Test configuration-related exceptions."""
    
    def test_invalid_configuration_error(self):
        """Test InvalidConfigurationError exception."""
        exc = InvalidConfigurationError("log_level", reason="must be one of DEBUG, INFO, WARNING, ERROR")
        assert "Invalid configuration for 'log_level': must be one of DEBUG, INFO, WARNING, ERROR" in str(exc)
        assert exc.error_code == "INVALID_CONFIGURATION"
        assert exc.details["config_key"] == "log_level"
        assert exc.details["reason"] == "must be one of DEBUG, INFO, WARNING, ERROR"
    
    def test_invalid_configuration_error_without_reason(self):
        """Test InvalidConfigurationError exception without reason."""
        exc = InvalidConfigurationError("api_key")
        assert "Invalid configuration for 'api_key'" in str(exc)
        assert exc.details["reason"] is None
    
    def test_missing_configuration_error(self):
        """Test MissingConfigurationError exception."""
        exc = MissingConfigurationError("redis_url")
        assert "Missing required configuration: redis_url" in str(exc)
        assert exc.error_code == "MISSING_CONFIGURATION"
        assert exc.details["config_key"] == "redis_url"


class TestSignalExceptions:
    """Test signal generation exceptions."""
    
    def test_signal_generation_error(self):
        """Test SignalGenerationError exception."""
        exc = SignalGenerationError("EURUSD", reason="insufficient data")
        assert "Failed to generate signal for EURUSD: insufficient data" in str(exc)
        assert exc.error_code == "SIGNAL_GENERATION_ERROR"
        assert exc.details["pair"] == "EURUSD"
        assert exc.details["reason"] == "insufficient data"
    
    def test_signal_generation_error_without_reason(self):
        """Test SignalGenerationError exception without reason."""
        exc = SignalGenerationError("GBPUSD")
        assert "Failed to generate signal for GBPUSD" in str(exc)
        assert exc.details["reason"] is None
    
    def test_invalid_currency_pair_error(self):
        """Test InvalidCurrencyPairError exception."""
        exc = InvalidCurrencyPairError("INVALID")
        assert "Invalid currency pair format: INVALID" in str(exc)
        assert exc.error_code == "INVALID_CURRENCY_PAIR"
        assert exc.details["pair"] == "INVALID"


class TestCacheExceptions:
    """Test cache-related exceptions."""
    
    def test_cache_connection_error(self):
        """Test CacheConnectionError exception."""
        exc = CacheConnectionError("redis", reason="connection refused")
        assert "Cache connection failed for redis: connection refused" in str(exc)
        assert exc.error_code == "CACHE_CONNECTION_ERROR"
        assert exc.details["cache_type"] == "redis"
        assert exc.details["reason"] == "connection refused"
    
    def test_cache_connection_error_without_reason(self):
        """Test CacheConnectionError exception without reason."""
        exc = CacheConnectionError("memory")
        assert "Cache connection failed for memory" in str(exc)
        assert exc.details["reason"] is None


class TestAnalysisExceptions:
    """Test analysis-related exceptions."""
    
    def test_technical_analysis_error(self):
        """Test TechnicalAnalysisError exception."""
        exc = TechnicalAnalysisError("RSI", reason="insufficient price data")
        assert "Technical analysis failed for RSI: insufficient price data" in str(exc)
        assert exc.error_code == "TECHNICAL_ANALYSIS_ERROR"
        assert exc.details["indicator"] == "RSI"
        assert exc.details["reason"] == "insufficient price data"
    
    def test_sentiment_analysis_error(self):
        """Test SentimentAnalysisError exception."""
        exc = SentimentAnalysisError("reddit", reason="API rate limit exceeded")
        assert "Sentiment analysis failed for reddit: API rate limit exceeded" in str(exc)
        assert exc.error_code == "SENTIMENT_ANALYSIS_ERROR"
        assert exc.details["source"] == "reddit"
        assert exc.details["reason"] == "API rate limit exceeded"
    
    def test_economic_analysis_error(self):
        """Test EconomicAnalysisError exception."""
        exc = EconomicAnalysisError("USD", reason="missing economic indicators")
        assert "Economic analysis failed for USD: missing economic indicators" in str(exc)
        assert exc.error_code == "ECONOMIC_ANALYSIS_ERROR"
        assert exc.details["currency"] == "USD"
        assert exc.details["reason"] == "missing economic indicators"


class TestExceptionInheritance:
    """Test exception inheritance hierarchy."""
    
    def test_api_exception_inheritance(self):
        """Test that API exceptions inherit correctly."""
        exc = APIKeyNotFound("test_api")
        assert isinstance(exc, APIException)
        assert isinstance(exc, ForexSignalException)
        assert isinstance(exc, Exception)
    
    def test_data_exception_inheritance(self):
        """Test that data exceptions inherit correctly."""
        exc = DataNotFound("test_data")
        assert isinstance(exc, DataException)
        assert isinstance(exc, ForexSignalException)
        assert isinstance(exc, Exception)
    
    def test_configuration_exception_inheritance(self):
        """Test that configuration exceptions inherit correctly."""
        exc = InvalidConfigurationError("test_config")
        assert isinstance(exc, ConfigurationException)
        assert isinstance(exc, ForexSignalException)
        assert isinstance(exc, Exception)
    
    def test_signal_exception_inheritance(self):
        """Test that signal exceptions inherit correctly."""
        exc = SignalGenerationError("EURUSD")
        assert isinstance(exc, SignalException)
        assert isinstance(exc, ForexSignalException)
        assert isinstance(exc, Exception)
    
    def test_cache_exception_inheritance(self):
        """Test that cache exceptions inherit correctly."""
        exc = CacheConnectionError("redis")
        assert isinstance(exc, CacheException)
        assert isinstance(exc, ForexSignalException)
        assert isinstance(exc, Exception)
    
    def test_analysis_exception_inheritance(self):
        """Test that analysis exceptions inherit correctly."""
        exc = TechnicalAnalysisError("RSI")
        assert isinstance(exc, AnalysisException)
        assert isinstance(exc, ForexSignalException)
        assert isinstance(exc, Exception)


class TestExceptionDetails:
    """Test exception details and error codes."""
    
    def test_exception_details_are_dict(self):
        """Test that exception details are always dictionaries."""
        exc = ForexSignalException("Test message")
        assert isinstance(exc.details, dict)
    
    def test_exception_details_default_empty(self):
        """Test that exception details default to empty dict."""
        exc = ForexSignalException("Test message", details=None)
        assert exc.details == {}
    
    def test_error_codes_are_strings(self):
        """Test that error codes are strings when provided."""
        exceptions_with_codes = [
            APIKeyNotFound("test"),
            InvalidAPICredentials("test"),
            DataNotFound("test"),
            InvalidConfigurationError("test"),
            SignalGenerationError("test"),
            CacheConnectionError("test"),
            TechnicalAnalysisError("test")
        ]
        
        for exc in exceptions_with_codes:
            assert isinstance(exc.error_code, str)
            assert len(exc.error_code) > 0
    
    def test_exception_message_accessibility(self):
        """Test that exception messages are accessible."""
        message = "Test exception message"
        exc = ForexSignalException(message)
        
        # Test different ways to access the message
        assert str(exc) == message
        assert exc.message == message
        assert exc.args[0] == message


if __name__ == '__main__':
    pytest.main([__file__])