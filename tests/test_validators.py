"""Unit tests for input validation utilities."""

import pytest
from datetime import datetime, timedelta

from src.core.validators import (
    CurrencyPairValidator,
    TimeframeValidator,
    PriceValidator,
    DateTimeValidator,
    APIParameterValidator,
    SignalValidator,
    validate_currency_pair,
    validate_currency_pairs,
    validate_timeframe,
    validate_price
)
from src.core.exceptions import (
    DataValidationError,
    InvalidCurrencyPairError
)


class TestCurrencyPairValidator:
    """Test currency pair validation."""
    
    def test_valid_currency_pairs(self):
        """Test validation of valid currency pairs."""
        valid_pairs = ['EURUSD', 'GBPUSD', 'USDJPY', 'USDCHF', 'AUDUSD']
        
        for pair in valid_pairs:
            result = CurrencyPairValidator.validate_currency_pair(pair)
            assert result == pair
    
    def test_currency_pair_normalization(self):
        """Test currency pair normalization."""
        test_cases = [
            ('eurusd', 'EURUSD'),
            ('EUR/USD', 'EURUSD'),
            ('eur usd', 'EURUSD'),
            ('  GBPUSD  ', 'GBPUSD')
        ]
        
        for input_pair, expected in test_cases:
            result = CurrencyPairValidator.validate_currency_pair(input_pair)
            assert result == expected
    
    def test_invalid_currency_pair_format(self):
        """Test validation of invalid currency pair formats."""
        invalid_pairs = ['EUR', 'EURUSDGBP', 'EU1USD', '123456', '']
        
        for pair in invalid_pairs:
            with pytest.raises(InvalidCurrencyPairError):
                CurrencyPairValidator.validate_currency_pair(pair)
    
    def test_unsupported_currencies(self):
        """Test validation with unsupported currencies."""
        invalid_pairs = ['XXXYYY', 'ABCDEF', 'USDZZZ']
        
        for pair in invalid_pairs:
            with pytest.raises(DataValidationError):
                CurrencyPairValidator.validate_currency_pair(pair)
    
    def test_same_base_and_quote(self):
        """Test validation when base and quote currencies are the same."""
        with pytest.raises(DataValidationError):
            CurrencyPairValidator.validate_currency_pair('USDUS D')
    
    def test_validate_currency_pairs_list(self):
        """Test validation of currency pairs list."""
        pairs = ['EURUSD', 'GBPUSD', 'USDJPY']
        result = CurrencyPairValidator.validate_currency_pairs(pairs)
        assert result == pairs
    
    def test_empty_currency_pairs_list(self):
        """Test validation of empty currency pairs list."""
        with pytest.raises(DataValidationError):
            CurrencyPairValidator.validate_currency_pairs([])
    
    def test_non_list_input(self):
        """Test validation with non-list input."""
        with pytest.raises(DataValidationError):
            CurrencyPairValidator.validate_currency_pairs('EURUSD')


class TestTimeframeValidator:
    """Test timeframe validation."""
    
    def test_valid_timeframes(self):
        """Test validation of valid timeframes."""
        valid_timeframes = ['1min', '5min', '15min', '30min', '1hour', '4hour', 'daily']
        
        for timeframe in valid_timeframes:
            result = TimeframeValidator.validate_timeframe(timeframe)
            assert result == timeframe
    
    def test_timeframe_aliases(self):
        """Test timeframe alias conversion."""
        test_cases = [
            ('1m', '1min'),
            ('5m', '5min'),
            ('1h', '1hour'),
            ('4h', '4hour'),
            ('1d', 'daily'),
            ('1w', 'weekly')
        ]
        
        for alias, expected in test_cases:
            result = TimeframeValidator.validate_timeframe(alias)
            assert result == expected
    
    def test_invalid_timeframes(self):
        """Test validation of invalid timeframes."""
        invalid_timeframes = ['2min', '3hour', '2daily', 'invalid', '']
        
        for timeframe in invalid_timeframes:
            with pytest.raises(DataValidationError):
                TimeframeValidator.validate_timeframe(timeframe)
    
    def test_case_insensitive(self):
        """Test case insensitive timeframe validation."""
        result = TimeframeValidator.validate_timeframe('DAILY')
        assert result == 'daily'


class TestPriceValidator:
    """Test price validation."""
    
    def test_valid_prices(self):
        """Test validation of valid prices."""
        test_cases = [
            (1.1234, 1.1234),
            ('1.1234', 1.1234),
            ('$1.50', 1.50),
            ('1,234.56', 1234.56),
            (100, 100.0)
        ]
        
        for input_price, expected in test_cases:
            result = PriceValidator.validate_price(input_price)
            assert result == expected
    
    def test_price_range_validation(self):
        """Test price range validation."""
        # Too low
        with pytest.raises(DataValidationError):
            PriceValidator.validate_price(0.00001)
        
        # Too high
        with pytest.raises(DataValidationError):
            PriceValidator.validate_price(2000000)
    
    def test_invalid_price_formats(self):
        """Test validation of invalid price formats."""
        invalid_prices = ['abc', '', 'not_a_number', None]
        
        for price in invalid_prices:
            with pytest.raises(DataValidationError):
                PriceValidator.validate_price(price)
    
    def test_pip_value_validation(self):
        """Test pip value validation."""
        # JPY pairs
        result = PriceValidator.validate_pip_value(0.01, 'USDJPY')
        assert result == 0.01
        
        # Non-JPY pairs
        result = PriceValidator.validate_pip_value(0.0001, 'EURUSD')
        assert result == 0.0001
    
    def test_invalid_pip_values(self):
        """Test validation of invalid pip values."""
        # Too large for non-JPY pair
        with pytest.raises(DataValidationError):
            PriceValidator.validate_pip_value(0.1, 'EURUSD')
        
        # Too small for JPY pair
        with pytest.raises(DataValidationError):
            PriceValidator.validate_pip_value(0.0001, 'USDJPY')


class TestDateTimeValidator:
    """Test datetime validation."""
    
    def test_valid_datetime_formats(self):
        """Test validation of valid datetime formats."""
        test_cases = [
            '2023-12-25 15:30:00',
            '2023-12-25T15:30:00',
            '2023-12-25T15:30:00Z',
            '2023-12-25',
            '25/12/2023',
            '12/25/2023'
        ]
        
        for dt_string in test_cases:
            result = DateTimeValidator.validate_datetime_string(dt_string)
            assert isinstance(result, datetime)
    
    def test_invalid_datetime_formats(self):
        """Test validation of invalid datetime formats."""
        invalid_dates = ['invalid', '2023-13-01', '32/12/2023', '', None]
        
        for dt_string in invalid_dates:
            with pytest.raises(DataValidationError):
                DateTimeValidator.validate_datetime_string(dt_string)
    
    def test_date_range_validation(self):
        """Test date range validation."""
        start_date = datetime(2023, 1, 1)
        end_date = datetime(2023, 12, 31)
        
        result_start, result_end = DateTimeValidator.validate_date_range(start_date, end_date)
        assert result_start == start_date
        assert result_end == end_date
    
    def test_invalid_date_range(self):
        """Test validation of invalid date ranges."""
        start_date = datetime(2023, 12, 31)
        end_date = datetime(2023, 1, 1)
        
        with pytest.raises(DataValidationError):
            DateTimeValidator.validate_date_range(start_date, end_date)
    
    def test_date_range_too_large(self):
        """Test validation of date range that's too large."""
        start_date = datetime(2020, 1, 1)
        end_date = datetime(2030, 1, 1)  # 10 years
        
        with pytest.raises(DataValidationError):
            DateTimeValidator.validate_date_range(start_date, end_date)


class TestAPIParameterValidator:
    """Test API parameter validation."""
    
    def test_valid_api_keys(self):
        """Test validation of valid API keys."""
        valid_keys = [
            'abcd1234efgh5678',
            'very_long_api_key_with_underscores_123456789',
            'SHORT123'
        ]
        
        for key in valid_keys:
            result = APIParameterValidator.validate_api_key(key, 'test_api')
            assert result == key
    
    def test_invalid_api_keys(self):
        """Test validation of invalid API keys."""
        invalid_keys = [
            '',  # Empty
            '   ',  # Whitespace only
            'short',  # Too short
            'test',  # Placeholder
            'demo',  # Placeholder
            'a' * 200  # Too long
        ]
        
        for key in invalid_keys:
            with pytest.raises(DataValidationError):
                APIParameterValidator.validate_api_key(key, 'test_api')
    
    def test_valid_urls(self):
        """Test validation of valid URLs."""
        valid_urls = [
            'https://api.example.com',
            'http://localhost:8080',
            'https://api.example.com/v1/data?param=value',
            'https://192.168.1.1:3000/api'
        ]
        
        for url in valid_urls:
            result = APIParameterValidator.validate_url(url)
            assert result == url
    
    def test_invalid_urls(self):
        """Test validation of invalid URLs."""
        invalid_urls = [
            'not_a_url',
            'ftp://example.com',  # Wrong protocol
            'https://',  # Incomplete
            '',  # Empty
            'example.com'  # Missing protocol
        ]
        
        for url in invalid_urls:
            with pytest.raises(DataValidationError):
                APIParameterValidator.validate_url(url)
    
    def test_query_parameter_sanitization(self):
        """Test query parameter sanitization."""
        test_cases = [
            ('normal_param', 'normal_param'),
            ('param<script>', 'paramscript'),
            ('param"with"quotes', 'paramwithquotes'),
            ('param&with&ampersands', 'paramwithampersands'),
            ('a' * 200, 'a' * 100)  # Length limit
        ]
        
        for input_param, expected in test_cases:
            result = APIParameterValidator.sanitize_query_parameter(input_param)
            assert result == expected


class TestSignalValidator:
    """Test signal validation."""
    
    def test_valid_signal_types(self):
        """Test validation of valid signal types."""
        valid_signals = ['BUY', 'SELL', 'HOLD', 'buy', 'sell', 'hold']
        
        for signal in valid_signals:
            result = SignalValidator.validate_signal_type(signal)
            assert result == signal.upper()
    
    def test_invalid_signal_types(self):
        """Test validation of invalid signal types."""
        invalid_signals = ['INVALID', 'LONG', 'SHORT', '', None]
        
        for signal in invalid_signals:
            with pytest.raises(DataValidationError):
                SignalValidator.validate_signal_type(signal)
    
    def test_confidence_validation(self):
        """Test confidence score validation."""
        valid_confidences = [0.0, 0.5, 1.0, 0.75]
        
        for confidence in valid_confidences:
            result = SignalValidator.validate_confidence(confidence)
            assert result == confidence
    
    def test_invalid_confidence_values(self):
        """Test validation of invalid confidence values."""
        invalid_confidences = [-0.1, 1.1, 'invalid', None]
        
        for confidence in invalid_confidences:
            with pytest.raises(DataValidationError):
                SignalValidator.validate_confidence(confidence)
    
    def test_pip_target_validation(self):
        """Test pip target validation."""
        valid_targets = [10, 50, 100, 500]
        
        for target in valid_targets:
            result = SignalValidator.validate_pip_target(target)
            assert result == target
    
    def test_invalid_pip_targets(self):
        """Test validation of invalid pip targets."""
        invalid_targets = [0, -10, 1001, 'invalid', None]
        
        for target in invalid_targets:
            with pytest.raises(DataValidationError):
                SignalValidator.validate_pip_target(target)


class TestConvenienceFunctions:
    """Test convenience validation functions."""
    
    def test_validate_currency_pair_function(self):
        """Test convenience currency pair validation function."""
        result = validate_currency_pair('EURUSD')
        assert result == 'EURUSD'
    
    def test_validate_currency_pairs_function(self):
        """Test convenience currency pairs validation function."""
        pairs = ['EURUSD', 'GBPUSD']
        result = validate_currency_pairs(pairs)
        assert result == pairs
    
    def test_validate_timeframe_function(self):
        """Test convenience timeframe validation function."""
        result = validate_timeframe('1hour')
        assert result == '1hour'
    
    def test_validate_price_function(self):
        """Test convenience price validation function."""
        result = validate_price(1.1234)
        assert result == 1.1234


if __name__ == '__main__':
    pytest.main([__file__])