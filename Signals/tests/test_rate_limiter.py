"""
Unit tests for rate limiting functionality
"""
import pytest
import time
import threading
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.rate_limiter import (
    RateLimitTracker, rate_limited, alpha_vantage_rate_limit,
    SmartAPIManager, cached_api_call, rate_tracker, api_manager
)

class TestRateLimitTracker:
    """Test rate limit tracking functionality"""
    
    def setup_method(self):
        """Setup test environment"""
        self.tracker = RateLimitTracker()
    
    def test_can_make_call_within_limit(self):
        """Test that calls within limit are allowed"""
        api_name = "test_api"
        
        # Should allow calls within limit
        for i in range(5):
            assert self.tracker.can_make_call(api_name, "minute", 10, 60) is True
            self.tracker.record_call(api_name, "minute")
    
    def test_rate_limit_enforcement(self):
        """Test that rate limits are enforced"""
        api_name = "test_api"
        limit = 3
        
        # Make calls up to limit
        for i in range(limit):
            assert self.tracker.can_make_call(api_name, "minute", limit, 60) is True
            self.tracker.record_call(api_name, "minute")
        
        # Next call should be blocked
        assert self.tracker.can_make_call(api_name, "minute", limit, 60) is False
    
    def test_daily_limit_reset(self):
        """Test daily limit reset functionality"""
        api_name = "test_api"
        
        # Set up past daily reset time
        past_time = datetime.now() - timedelta(days=1)
        self.tracker.daily_resets[api_name] = past_time
        self.tracker.call_counts[api_name]["daily"] = 100
        
        # Should allow call after reset check
        assert self.tracker.can_make_call(api_name, "daily", 25, 86400) is True
        
        # Daily count should be reset
        assert self.tracker.call_counts[api_name]["daily"] == 0
    
    def test_minute_limit_window(self):
        """Test minute-based rate limiting window"""
        api_name = "test_api"
        limit = 5
        
        # Fill up the minute limit
        for i in range(limit):
            assert self.tracker.can_make_call(api_name, "minute", limit, 60) is True
            self.tracker.record_call(api_name, "minute")
        
        # Should be blocked
        assert self.tracker.can_make_call(api_name, "minute", limit, 60) is False
        
        # Simulate time passing (mock the call times)
        old_time = datetime.now() - timedelta(seconds=70)
        for _ in range(limit):
            self.tracker.call_times[api_name]["minute"].appendleft(old_time)
        
        # Should allow calls again after old calls expire
        assert self.tracker.can_make_call(api_name, "minute", limit, 60) is True
    
    def test_usage_stats(self):
        """Test usage statistics reporting"""
        api_name = "test_api"
        
        # Make some calls
        for i in range(3):
            self.tracker.record_call(api_name, "daily")
            self.tracker.record_call(api_name, "minute")
        
        stats = self.tracker.get_usage_stats()
        
        assert api_name in stats
        assert stats[api_name]["daily"] == 3
        assert stats[api_name]["minute"] == 3
    
    def test_thread_safety(self):
        """Test thread safety of rate tracker"""
        api_name = "test_api"
        limit = 100
        
        def make_calls():
            for _ in range(10):
                if self.tracker.can_make_call(api_name, "minute", limit, 60):
                    self.tracker.record_call(api_name, "minute")
        
        # Run multiple threads
        threads = []
        for _ in range(5):
            thread = threading.Thread(target=make_calls)
            threads.append(thread)
            thread.start()
        
        for thread in threads:
            thread.join()
        
        # Should have recorded exactly 50 calls
        stats = self.tracker.get_usage_stats()
        assert stats[api_name]["minute"] == 50

class TestRateLimitDecorators:
    """Test rate limiting decorators"""
    
    def setup_method(self):
        """Setup test environment"""
        # Clear any existing rate tracking
        global rate_tracker
        rate_tracker = RateLimitTracker()
    
    def test_rate_limited_decorator(self):
        """Test basic rate limited decorator"""
        call_count = 0
        
        @rate_limited("test_api", calls_per_minute=2)
        def test_function():
            nonlocal call_count
            call_count += 1
            return "success"
        
        # First two calls should succeed
        assert test_function() == "success"
        assert test_function() == "success"
        assert call_count == 2
        
        # Third call should be rate limited - we'll use a short timeout for testing
        with pytest.raises(Exception, match="Rate limit exceeded"):
            with patch.object(rate_tracker, 'time_until_reset', return_value=300):  # Mock long wait
                test_function()
    
    def test_alpha_vantage_rate_limit_decorator(self):
        """Test Alpha Vantage specific rate limiter"""
        call_count = 0
        
        @alpha_vantage_rate_limit()
        def get_alpha_vantage_data():
            nonlocal call_count
            call_count += 1
            return {"data": "test"}
        
        # Should work within daily limit
        result = get_alpha_vantage_data()
        assert result == {"data": "test"}
        assert call_count == 1
    
    def test_cached_api_call_decorator(self):
        """Test cached API call decorator"""
        call_count = 0
        
        @cached_api_call("test_api", ttl=60)
        def fetch_data(param):
            nonlocal call_count
            call_count += 1
            return f"data_{param}"
        
        # First call should execute function
        result1 = fetch_data("test")
        assert call_count == 1
        assert result1 == "data_test"
        
        # Second call should use cache
        result2 = fetch_data("test")
        assert call_count == 1  # Should not increment
        assert result2 == "data_test"
        
        # Different parameter should execute function
        result3 = fetch_data("different")
        assert call_count == 2
        assert result3 == "data_different"

class TestSmartAPIManager:
    """Test smart API management"""
    
    def setup_method(self):
        """Setup test environment"""
        self.manager = SmartAPIManager()
    
    def test_get_available_api(self):
        """Test getting available API for data type"""
        # Mock API availability
        with patch.object(self.manager, '_is_api_available') as mock_available:
            mock_available.return_value = True
            
            api = self.manager.get_available_api('price_data')
            assert api in ['alpha_vantage', 'twelve_data']
    
    def test_api_fallback_strategy(self):
        """Test API fallback when primary is unavailable"""
        with patch.object(self.manager, '_is_api_available') as mock_available:
            # First API unavailable, second available
            mock_available.side_effect = [False, True]
            
            api = self.manager.get_available_api('price_data')
            assert api == 'twelve_data'  # Should fallback to second API
    
    def test_api_health_check(self):
        """Test API health checking"""
        api_name = "alpha_vantage"
        
        # Mock successful health check
        with patch('requests.get') as mock_get:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_get.return_value = mock_response
            
            self.manager._check_api_health(api_name)
            
            assert self.manager.api_health[api_name]['status'] == 'healthy'
    
    def test_api_health_check_failure(self):
        """Test API health check failure handling"""
        api_name = "alpha_vantage"
        
        # Mock failed health check
        with patch('requests.get') as mock_get:
            mock_response = Mock()
            mock_response.status_code = 500
            mock_get.return_value = mock_response
            
            self.manager._check_api_health(api_name)
            
            assert self.manager.api_health[api_name]['status'] == 'unhealthy'
    
    def test_get_api_statistics(self):
        """Test API statistics reporting"""
        stats = self.manager.get_api_statistics()
        
        assert 'rate_limits' in stats
        assert 'api_health' in stats
        assert 'available_apis' in stats
        
        # Should have statistics for different data types
        assert 'price_data' in stats['available_apis']
        assert 'economic_data' in stats['available_apis']
    
    def test_api_availability_check(self):
        """Test comprehensive API availability checking"""
        # Test with healthy API and available rate limit
        with patch.object(rate_tracker, 'can_make_call', return_value=True):
            result = self.manager._is_api_available('alpha_vantage')
            assert result is True
        
        # Test with rate limit exceeded
        with patch.object(rate_tracker, 'can_make_call', return_value=False):
            result = self.manager._is_api_available('alpha_vantage')
            assert result is False

class TestRobustAPICall:
    """Test robust API call functionality"""
    
    def test_make_request_with_backoff_success(self):
        """Test successful request with backoff"""
        from src.rate_limiter import make_request_with_backoff
        
        with patch('requests.get') as mock_get:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"status": "success"}
            mock_get.return_value = mock_response
            
            response = make_request_with_backoff("http://test.com")
            assert response.status_code == 200
    
    def test_make_request_with_backoff_retry(self):
        """Test request retry on failure"""
        from src.rate_limiter import make_request_with_backoff
        import requests
        
        with patch('requests.get') as mock_get:
            # First call fails, second succeeds
            mock_get.side_effect = [
                requests.exceptions.ConnectionError("Connection failed"),
                Mock(status_code=200)
            ]
            
            response = make_request_with_backoff("http://test.com")
            assert response.status_code == 200
            assert mock_get.call_count == 2

class TestIntegration:
    """Integration tests for rate limiting system"""
    
    def test_full_rate_limiting_workflow(self):
        """Test complete rate limiting workflow"""
        # Create a test function with rate limiting and caching
        call_count = 0
        
        @cached_api_call("test_api", ttl=60)
        @rate_limited("test_api", calls_per_minute=5)
        def fetch_test_data(symbol):
            nonlocal call_count
            call_count += 1
            return {"symbol": symbol, "price": 1.2345}
        
        # First call should execute function
        result1 = fetch_test_data("EURUSD")
        assert call_count == 1
        assert result1["symbol"] == "EURUSD"
        
        # Second call with same parameter should use cache
        result2 = fetch_test_data("EURUSD")
        assert call_count == 1  # Should not increment due to cache
        assert result2 == result1
        
        # Third call with different parameter should execute function
        result3 = fetch_test_data("GBPUSD")
        assert call_count == 2
        assert result3["symbol"] == "GBPUSD"
    
    def test_api_manager_integration(self):
        """Test API manager integration with rate limiting"""
        # Test that API manager correctly identifies available APIs
        available_api = api_manager.get_available_api('price_data')
        
        # Should return an API name or None
        assert available_api is None or available_api in ['alpha_vantage', 'twelve_data']
        
        # Get statistics
        stats = api_manager.get_api_statistics()
        assert isinstance(stats, dict)
        assert 'rate_limits' in stats