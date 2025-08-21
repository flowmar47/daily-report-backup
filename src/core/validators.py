"""Input validation and sanitization utilities for the forex signal system."""

import re
from typing import List, Optional, Union, Any
from datetime import datetime, timedelta
from decimal import Decimal, InvalidOperation

from .exceptions import DataValidationError, InvalidCurrencyPairError


class CurrencyPairValidator:
    """Validator for currency pair formats and operations."""
    
    # Standard currency pair format: 6 characters (XXXYYY)
    CURRENCY_PAIR_PATTERN = re.compile(r'^[A-Z]{6}$')
    
    # Major currency codes
    MAJOR_CURRENCIES = {
        'USD', 'EUR', 'GBP', 'JPY', 'CHF', 'CAD', 'AUD', 'NZD'
    }
    
    # All supported currency codes
    SUPPORTED_CURRENCIES = MAJOR_CURRENCIES.union({
        'SEK', 'NOK', 'DKK', 'PLN', 'CZK', 'HUF', 'TRY', 'ZAR',
        'MXN', 'BRL', 'CNY', 'HKD', 'SGD', 'KRW', 'INR', 'THB'
    })
    
    @classmethod
    def validate_currency_pair(cls, pair: str) -> str:
        """Validate and normalize currency pair format."""
        if not isinstance(pair, str):
            raise DataValidationError('currency_pair', str(pair), 'string')
        
        # Normalize to uppercase and remove spaces
        normalized_pair = pair.upper().replace(' ', '').replace('/', '')
        
        # Check format
        if not cls.CURRENCY_PAIR_PATTERN.match(normalized_pair):
            raise InvalidCurrencyPairError(pair)
        
        # Extract base and quote currencies
        base_currency = normalized_pair[:3]
        quote_currency = normalized_pair[3:]
        
        # Validate individual currencies
        if base_currency not in cls.SUPPORTED_CURRENCIES:
            raise DataValidationError('base_currency', base_currency, f'one of {cls.SUPPORTED_CURRENCIES}')
        
        if quote_currency not in cls.SUPPORTED_CURRENCIES:
            raise DataValidationError('quote_currency', quote_currency, f'one of {cls.SUPPORTED_CURRENCIES}')
        
        # Ensure base and quote are different
        if base_currency == quote_currency:
            raise DataValidationError('currency_pair', pair, 'different base and quote currencies')
        
        return normalized_pair
    
    @classmethod
    def validate_currency_pairs(cls, pairs: List[str]) -> List[str]:
        """Validate a list of currency pairs."""
        if not isinstance(pairs, list):
            raise DataValidationError('currency_pairs', str(pairs), 'list')
        
        if not pairs:
            raise DataValidationError('currency_pairs', '[]', 'non-empty list')
        
        validated_pairs = []
        for pair in pairs:
            validated_pairs.append(cls.validate_currency_pair(pair))
        
        return validated_pairs


class TimeframeValidator:
    """Validator for timeframe parameters."""
    
    VALID_TIMEFRAMES = {
        '1min', '5min', '15min', '30min', '1hour', '2hour', '4hour', 
        '6hour', '8hour', '12hour', 'daily', 'weekly', 'monthly'
    }
    
    # Mapping for alternative formats
    TIMEFRAME_ALIASES = {
        '1m': '1min', '5m': '5min', '15m': '15min', '30m': '30min',
        '1h': '1hour', '2h': '2hour', '4h': '4hour', '6h': '6hour',
        '8h': '8hour', '12h': '12hour', '1d': 'daily', '1w': 'weekly', '1M': 'monthly'
    }
    
    @classmethod
    def validate_timeframe(cls, timeframe: str) -> str:
        """Validate and normalize timeframe."""
        if not isinstance(timeframe, str):
            raise DataValidationError('timeframe', str(timeframe), 'string')
        
        normalized = timeframe.lower().strip()
        
        # Check aliases first
        if normalized in cls.TIMEFRAME_ALIASES:
            return cls.TIMEFRAME_ALIASES[normalized]
        
        # Check direct match
        if normalized in cls.VALID_TIMEFRAMES:
            return normalized
        
        raise DataValidationError('timeframe', timeframe, f'one of {cls.VALID_TIMEFRAMES}')


class PriceValidator:
    """Validator for price and financial data."""
    
    @staticmethod
    def validate_price(price: Union[str, float, int], field_name: str = 'price') -> float:
        """Validate and convert price to float."""
        try:
            if isinstance(price, str):
                # Remove common formatting
                cleaned_price = price.replace(',', '').replace('$', '').strip()
                price_value = float(cleaned_price)
            else:
                price_value = float(price)
            
            # Check for reasonable price range (0.0001 to 1,000,000)
            if not (0.0001 <= price_value <= 1_000_000):
                raise DataValidationError(field_name, str(price), 'price between 0.0001 and 1,000,000')
            
            return price_value
            
        except (ValueError, TypeError) as e:
            raise DataValidationError(field_name, str(price), 'valid numeric price') from e
    
    @staticmethod
    def validate_pip_value(pip_value: Union[str, float, int], pair: str) -> float:
        """Validate pip value for a currency pair."""
        try:
            pip_float = float(pip_value)
            
            # JPY pairs typically have pip value of 0.01, others 0.0001
            if 'JPY' in pair.upper():
                expected_range = (0.001, 0.1)
            else:
                expected_range = (0.00001, 0.001)
            
            if not (expected_range[0] <= pip_float <= expected_range[1]):
                raise DataValidationError('pip_value', str(pip_value), f'value between {expected_range[0]} and {expected_range[1]}')
            
            return pip_float
            
        except (ValueError, TypeError) as e:
            raise DataValidationError('pip_value', str(pip_value), 'valid numeric pip value') from e


class DateTimeValidator:
    """Validator for date and time parameters."""
    
    @staticmethod
    def validate_datetime_string(dt_string: str, field_name: str = 'datetime') -> datetime:
        """Validate and parse datetime string."""
        if not isinstance(dt_string, str):
            raise DataValidationError(field_name, str(dt_string), 'string')
        
        # Common datetime formats
        formats = [
            '%Y-%m-%d %H:%M:%S',
            '%Y-%m-%dT%H:%M:%S',
            '%Y-%m-%dT%H:%M:%SZ',
            '%Y-%m-%d',
            '%d/%m/%Y',
            '%m/%d/%Y'
        ]
        
        for fmt in formats:
            try:
                return datetime.strptime(dt_string, fmt)
            except ValueError:
                continue
        
        raise DataValidationError(field_name, dt_string, 'valid datetime format')
    
    @staticmethod
    def validate_date_range(start_date: datetime, end_date: datetime) -> tuple:
        """Validate date range."""
        if start_date >= end_date:
            raise DataValidationError('date_range', f'{start_date} to {end_date}', 'start_date < end_date')
        
        # Check if range is reasonable (not more than 5 years)
        max_range = timedelta(days=5*365)
        if end_date - start_date > max_range:
            raise DataValidationError('date_range', f'{start_date} to {end_date}', 'range <= 5 years')
        
        return start_date, end_date


class APIParameterValidator:
    """Validator for API parameters and requests."""
    
    @staticmethod
    def validate_api_key(api_key: str, api_name: str) -> str:
        """Validate API key format."""
        if not isinstance(api_key, str):
            raise DataValidationError('api_key', str(api_key), 'string')
        
        cleaned_key = api_key.strip()
        
        if not cleaned_key:
            raise DataValidationError('api_key', 'empty', 'non-empty string')
        
        # Basic length validation (most API keys are 16-64 characters)
        if not (8 <= len(cleaned_key) <= 128):
            raise DataValidationError('api_key', f'length {len(cleaned_key)}', 'length between 8 and 128 characters')
        
        # Check for suspicious patterns
        if cleaned_key.lower() in ['test', 'demo', 'example', 'placeholder']:
            raise DataValidationError('api_key', cleaned_key, 'valid API key (not placeholder)')
        
        return cleaned_key
    
    @staticmethod
    def validate_url(url: str, field_name: str = 'url') -> str:
        """Validate URL format."""
        if not isinstance(url, str):
            raise DataValidationError(field_name, str(url), 'string')
        
        url = url.strip()
        
        # Basic URL validation
        url_pattern = re.compile(
            r'^https?://'  # http:// or https://
            r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+'  # domain...
            r'(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|'  # host...
            r'localhost|'  # localhost...
            r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
            r'(?::\d+)?'  # optional port
            r'(?:/?|[/?]\S+)$', re.IGNORECASE)
        
        if not url_pattern.match(url):
            raise DataValidationError(field_name, url, 'valid URL format')
        
        return url
    
    @staticmethod
    def sanitize_query_parameter(param: str, max_length: int = 100) -> str:
        """Sanitize query parameter to prevent injection attacks."""
        if not isinstance(param, str):
            param = str(param)
        
        # Remove potentially dangerous characters
        sanitized = re.sub(r'[<>"\';\\&]', '', param)
        
        # Limit length
        if len(sanitized) > max_length:
            sanitized = sanitized[:max_length]
        
        return sanitized.strip()


class SignalValidator:
    """Validator for trading signal parameters."""
    
    VALID_SIGNAL_TYPES = {'BUY', 'SELL', 'HOLD'}
    
    @staticmethod
    def validate_signal_type(signal_type: str) -> str:
        """Validate signal type."""
        if not isinstance(signal_type, str):
            raise DataValidationError('signal_type', str(signal_type), 'string')
        
        normalized = signal_type.upper().strip()
        
        if normalized not in SignalValidator.VALID_SIGNAL_TYPES:
            raise DataValidationError('signal_type', signal_type, f'one of {SignalValidator.VALID_SIGNAL_TYPES}')
        
        return normalized
    
    @staticmethod
    def validate_confidence(confidence: Union[float, int]) -> float:
        """Validate confidence score (0.0 to 1.0)."""
        try:
            conf_float = float(confidence)
            
            if not (0.0 <= conf_float <= 1.0):
                raise DataValidationError('confidence', str(confidence), 'value between 0.0 and 1.0')
            
            return conf_float
            
        except (ValueError, TypeError) as e:
            raise DataValidationError('confidence', str(confidence), 'numeric value') from e
    
    @staticmethod
    def validate_pip_target(pip_target: Union[int, float]) -> int:
        """Validate pip target (positive integer)."""
        try:
            pip_int = int(pip_target)
            
            if pip_int <= 0:
                raise DataValidationError('pip_target', str(pip_target), 'positive integer')
            
            if pip_int > 1000:  # Reasonable upper limit
                raise DataValidationError('pip_target', str(pip_target), 'pip target <= 1000')
            
            return pip_int
            
        except (ValueError, TypeError) as e:
            raise DataValidationError('pip_target', str(pip_target), 'positive integer') from e


# Convenience functions for common validations
def validate_currency_pair(pair: str) -> str:
    """Convenience function to validate a single currency pair."""
    return CurrencyPairValidator.validate_currency_pair(pair)


def validate_currency_pairs(pairs: List[str]) -> List[str]:
    """Convenience function to validate multiple currency pairs."""
    return CurrencyPairValidator.validate_currency_pairs(pairs)


def validate_timeframe(timeframe: str) -> str:
    """Convenience function to validate timeframe."""
    return TimeframeValidator.validate_timeframe(timeframe)


def validate_price(price: Union[str, float, int], field_name: str = 'price') -> float:
    """Convenience function to validate price."""
    return PriceValidator.validate_price(price, field_name)