"""Custom exceptions for stock alerts system"""


class StockAlertError(Exception):
    """Base exception for stock alerts system"""
    pass


class DataFetchError(StockAlertError):
    """Error fetching data from API"""
    pass


class ValidationError(StockAlertError):
    """Data validation error"""
    pass


class RateLimitError(StockAlertError):
    """API rate limit exceeded"""
    pass


class ConfigurationError(StockAlertError):
    """Configuration error"""
    pass


class MarketClosedError(StockAlertError):
    """Market is closed error"""
    pass
