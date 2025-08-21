"""
Unit tests for cache management
"""
import pytest
import json
import time
from unittest.mock import Mock, patch
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.cache_manager import CacheManager, cached, price_data_cache, economic_data_cache

class TestCacheManager:
    """Test cache manager functionality"""
    
    def setup_method(self):
        """Setup test environment"""
        self.cache = CacheManager()
        # Use fallback cache for testing (no Redis dependency)
        self.cache.redis_client = None
    
    def test_cache_set_get(self):
        """Test basic cache set and get operations"""
        test_key = "test_key"
        test_value = {"data": "test_data", "number": 123}
        
        # Set cache
        result = self.cache.set(test_key, test_value, ttl=60)
        assert result is True
        
        # Get cache
        cached_value = self.cache.get(test_key)
        assert cached_value == test_value
    
    def test_cache_expiry(self):
        """Test cache expiry functionality"""
        test_key = "expiry_test"
        test_value = "test_data"
        
        # Set with very short TTL
        self.cache.set(test_key, test_value, ttl=1)
        
        # Should be available immediately
        assert self.cache.get(test_key) == test_value
        
        # Wait for expiry
        time.sleep(1.1)
        
        # Should be None after expiry
        assert self.cache.get(test_key) is None
    
    def test_cache_delete(self):
        """Test cache deletion"""
        test_key = "delete_test"
        test_value = "test_data"
        
        # Set cache
        self.cache.set(test_key, test_value)
        assert self.cache.get(test_key) == test_value
        
        # Delete cache
        self.cache.delete(test_key)
        assert self.cache.get(test_key) is None
    
    def test_api_response_caching(self):
        """Test API response caching"""
        api_name = "test_api"
        endpoint = "/test"
        params = {"symbol": "EURUSD", "interval": "4h"}
        response_data = {"price": 1.2345, "timestamp": "2024-01-01"}
        
        # Cache API response
        result = self.cache.cache_api_response(api_name, endpoint, params, response_data, ttl=60)
        assert result is True
        
        # Retrieve cached response
        cached_response = self.cache.get_cached_api_response(api_name, endpoint, params)
        assert cached_response == response_data
    
    def test_api_response_caching_different_params(self):
        """Test that different parameters create different cache entries"""
        api_name = "test_api"
        endpoint = "/test"
        params1 = {"symbol": "EURUSD"}
        params2 = {"symbol": "GBPUSD"}
        response1 = {"price": 1.2345}
        response2 = {"price": 1.5678}
        
        # Cache different responses
        self.cache.cache_api_response(api_name, endpoint, params1, response1)
        self.cache.cache_api_response(api_name, endpoint, params2, response2)
        
        # Should get different responses
        cached1 = self.cache.get_cached_api_response(api_name, endpoint, params1)
        cached2 = self.cache.get_cached_api_response(api_name, endpoint, params2)
        
        assert cached1 == response1
        assert cached2 == response2
    
    def test_fallback_cache_size_limit(self):
        """Test fallback cache size limiting"""
        # Set a small max size for testing
        self.cache.max_fallback_size = 5
        
        # Add more entries than the limit
        for i in range(10):
            self.cache.set(f"test_key_{i}", f"value_{i}")
        
        # Should not exceed max size
        assert len(self.cache.fallback_cache) <= self.cache.max_fallback_size
    
    def test_key_generation(self):
        """Test cache key generation"""
        prefix = "test"
        short_id = "short"
        long_id = "a" * 300  # Very long identifier
        
        short_key = self.cache._generate_key(prefix, short_id)
        long_key = self.cache._generate_key(prefix, long_id)
        
        assert short_key == "forex_signals:test:short"
        assert len(long_key) < len(f"forex_signals:{prefix}:{long_id}")
        assert "forex_signals:test:" in long_key
    
    def test_data_serialization(self):
        """Test data serialization and deserialization"""
        test_data = {
            "string": "test",
            "number": 123,
            "float": 12.34,
            "list": [1, 2, 3],
            "nested": {"key": "value"}
        }
        
        # Serialize
        serialized = self.cache._serialize_data(test_data)
        assert isinstance(serialized, str)
        
        # Deserialize
        deserialized = self.cache._deserialize_data(serialized)
        assert deserialized == test_data
    
    def test_cache_stats(self):
        """Test cache statistics"""
        stats = self.cache.get_cache_stats()
        
        assert isinstance(stats, dict)
        assert 'redis_connected' in stats
        assert 'fallback_entries' in stats
        assert 'fallback_max_size' in stats
        assert stats['redis_connected'] is False  # We disabled Redis for testing
    
    def test_clear_cache(self):
        """Test cache clearing"""
        # Add some test data
        self.cache.set("test1", "value1")
        self.cache.set("test2", "value2")
        
        # Clear cache
        cleared_count = self.cache.clear_cache()
        
        assert cleared_count >= 2
        assert self.cache.get("test1") is None
        assert self.cache.get("test2") is None

class TestCacheDecorators:
    """Test cache decorators"""
    
    def setup_method(self):
        """Setup test environment"""
        # Clear any existing cache
        from src.cache_manager import cache_manager
        cache_manager.clear_cache()
    
    def test_cached_decorator(self):
        """Test cached decorator functionality"""
        call_count = 0
        
        @cached(ttl=60)
        def test_function(param1, param2=None):
            nonlocal call_count
            call_count += 1
            return f"result_{param1}_{param2}"
        
        # First call should execute function
        result1 = test_function("a", param2="b")
        assert call_count == 1
        assert result1 == "result_a_b"
        
        # Second call should use cache
        result2 = test_function("a", param2="b")
        assert call_count == 1  # Should not increment
        assert result2 == "result_a_b"
        
        # Different parameters should execute function
        result3 = test_function("c", param2="d")
        assert call_count == 2
        assert result3 == "result_c_d"
    
    def test_price_data_cache_decorator(self):
        """Test price data cache decorator"""
        call_count = 0
        
        @price_data_cache()
        def get_price_data(symbol, timeframe="1h"):
            nonlocal call_count
            call_count += 1
            return {"symbol": symbol, "timeframe": timeframe, "price": 1.2345}
        
        # First call
        result1 = get_price_data("EURUSD", "4h")
        assert call_count == 1
        
        # Second call with same parameters should use cache
        result2 = get_price_data("EURUSD", "4h")
        assert call_count == 1
        assert result1 == result2
    
    def test_economic_data_cache_decorator(self):
        """Test economic data cache decorator"""
        call_count = 0
        
        @economic_data_cache()
        def get_economic_data(country, indicator="GDP"):
            nonlocal call_count
            call_count += 1
            return {"country": country, "indicator": indicator, "value": 2.5}
        
        # First call
        result1 = get_economic_data("USD", "DFF")
        assert call_count == 1
        
        # Second call should use cache
        result2 = get_economic_data("USD", "DFF")
        assert call_count == 1
        assert result1 == result2