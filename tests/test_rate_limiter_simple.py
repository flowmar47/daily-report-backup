"""
Simplified unit tests for rate limiting functionality
"""
import pytest
import time
from unittest.mock import Mock, patch
from datetime import datetime, timedelta
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.rate_limiter import (
    RateLimitTracker, rate_limited, alpha_vantage_rate_limit,
    SmartAPIManager, cached_api_call
)

class TestRateLimitTrackerSimple:
    """Simplified tests for rate limit tracking"""
    
    def setup_method(self):
        """Setup test environment"""
        self.tracker = RateLimitTracker()
    
    def test_basic_rate_limiting(self):
        """Test basic rate limiting functionality"""
        api_name = "test_api"
        
        # Should allow calls within limit
        assert self.tracker.can_make_call(api_name, "minute", 5, 60) is True
        self.tracker.record_call(api_name, "minute")
        
        assert self.tracker.can_make_call(api_name, "minute", 5, 60) is True
        self.tracker.record_call(api_name, "minute")
    
    def test_daily_limit_tracking(self):
        """Test daily limit tracking"""
        api_name = "test_api"
        
        # Make some daily calls
        for i in range(3):
            assert self.tracker.can_make_call(api_name, "daily", 10, 86400) is True
            self.tracker.record_call(api_name, "daily")
        
        # Check usage stats
        stats = self.tracker.get_usage_stats()
        assert api_name in stats
        assert stats[api_name]["daily"] == 3
    
    def test_rate_limit_enforcement(self):
        """Test that rate limits are properly enforced"""
        api_name = "test_api"
        limit = 2
        
        # Make calls up to limit
        for i in range(limit):
            assert self.tracker.can_make_call(api_name, "minute", limit, 60) is True
            self.tracker.record_call(api_name, "minute")
        
        # Next call should be blocked
        assert self.tracker.can_make_call(api_name, "minute", limit, 60) is False

class TestRateLimitDecoratorsSimple:
    """Simplified tests for rate limiting decorators"""
    
    def test_alpha_vantage_decorator(self):
        """Test Alpha Vantage rate limiter decorator"""
        call_count = 0
        
        @alpha_vantage_rate_limit()
        def get_data():
            nonlocal call_count
            call_count += 1
            return "success"
        
        # Should work for at least one call
        result = get_data()
        assert result == "success"
        assert call_count == 1
    
    def test_cached_api_call(self):
        """Test cached API call decorator"""
        call_count = 0
        
        @cached_api_call("test_api", ttl=60)
        def fetch_data(param):
            nonlocal call_count
            call_count += 1
            return f"data_{param}"
        
        # First call should execute
        result1 = fetch_data("test")
        assert call_count == 1
        assert result1 == "data_test"
        
        # Second call should use cache
        result2 = fetch_data("test")
        assert call_count == 1  # Should not increment
        assert result2 == "data_test"
    
    def test_rate_limited_decorator_basic(self):
        """Test basic rate limited decorator"""
        call_count = 0
        
        @rate_limited("test_api", calls_per_minute=10)  # High limit to avoid blocking
        def test_function():
            nonlocal call_count
            call_count += 1
            return "success"
        
        # Should work within reasonable limits
        result = test_function()
        assert result == "success"
        assert call_count == 1

class TestSmartAPIManagerSimple:
    """Simplified tests for smart API management"""
    
    def setup_method(self):
        """Setup test environment"""
        self.manager = SmartAPIManager()
    
    def test_get_available_api_basic(self):
        """Test basic API availability check"""
        # Should return an API or None
        api = self.manager.get_available_api('price_data')
        assert api is None or api in ['alpha_vantage', 'twelve_data']
    
    def test_api_statistics(self):
        """Test API statistics collection"""
        stats = self.manager.get_api_statistics()
        
        # Should return a dictionary with expected structure
        assert isinstance(stats, dict)
        assert 'rate_limits' in stats
        assert 'api_health' in stats
        assert 'available_apis' in stats
    
    def test_fallback_strategies(self):
        """Test that fallback strategies are properly configured"""
        strategies = self.manager.fallback_strategies
        
        assert 'price_data' in strategies
        assert 'economic_data' in strategies
        assert 'news_sentiment' in strategies
        
        # Price data should have multiple fallback options
        assert len(strategies['price_data']) >= 2
    
    @patch('requests.get')
    def test_api_health_check_success(self, mock_get):
        """Test successful API health check"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_get.return_value = mock_response
        
        self.manager._check_api_health('alpha_vantage')
        
        # Should mark API as healthy
        assert self.manager.api_health['alpha_vantage']['status'] == 'healthy'
    
    @patch('requests.get')
    def test_api_health_check_failure(self, mock_get):
        """Test failed API health check"""
        mock_response = Mock()
        mock_response.status_code = 500
        mock_get.return_value = mock_response
        
        self.manager._check_api_health('alpha_vantage')
        
        # Should mark API as unhealthy
        assert self.manager.api_health['alpha_vantage']['status'] == 'unhealthy'

class TestRobustAPICallSimple:
    """Simplified tests for robust API calls"""
    
    @patch('requests.get')
    def test_successful_request(self, mock_get):
        """Test successful API request"""
        from src.rate_limiter import make_request_with_backoff
        
        mock_response = Mock()
        mock_response.status_code = 200
        mock_get.return_value = mock_response
        
        response = make_request_with_backoff("http://test.com")
        assert response.status_code == 200
    
    @patch('requests.get')
    def test_request_retry(self, mock_get):
        """Test request retry mechanism"""
        from src.rate_limiter import make_request_with_backoff
        import requests
        
        # First call fails, second succeeds
        mock_get.side_effect = [
            requests.exceptions.RequestException("Network error"),
            Mock(status_code=200)
        ]
        
        response = make_request_with_backoff("http://test.com")
        assert response.status_code == 200
        assert mock_get.call_count == 2

class TestIntegrationSimple:
    """Simplified integration tests"""
    
    def test_decorator_combination(self):
        """Test combining multiple decorators"""
        call_count = 0
        
        @cached_api_call("integration_test", ttl=60)
        @rate_limited("integration_test", calls_per_minute=10)
        def fetch_data(symbol):
            nonlocal call_count
            call_count += 1
            return {"symbol": symbol, "price": 1.2345}
        
        # First call should execute
        result1 = fetch_data("EURUSD")
        assert call_count == 1
        assert result1["symbol"] == "EURUSD"
        
        # Second call should use cache
        result2 = fetch_data("EURUSD")
        assert call_count == 1  # Should not increment
        assert result2 == result1
    
    def test_api_manager_basic_workflow(self):
        """Test basic API manager workflow"""
        manager = SmartAPIManager()
        
        # Should be able to get statistics without error
        stats = manager.get_api_statistics()
        assert isinstance(stats, dict)
        
        # Should be able to check for available APIs
        api = manager.get_available_api('price_data')
        # Result can be None or a valid API name
        assert api is None or isinstance(api, str)