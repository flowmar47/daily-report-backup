"""
Cache management for Forex Signal Generator
Handles Redis caching with intelligent TTL and fallback mechanisms
"""
import json
import hashlib
import logging
from typing import Any, Dict, Optional, Union
from functools import wraps
import redis
from datetime import datetime, timedelta

from src.core.config import settings

logger = logging.getLogger(__name__)

class CacheManager:
    """Redis-based cache manager with intelligent TTL and fallback"""
    
    def __init__(self):
        self.redis_client = None
        self.fallback_cache = {}  # In-memory fallback
        self.max_fallback_size = 1000
        self._connect_redis()
    
    def _connect_redis(self):
        """Connect to Redis with error handling"""
        try:
            self.redis_client = redis.from_url(
                settings.redis_url,
                decode_responses=True,
                socket_connect_timeout=settings.redis_timeout,
                socket_timeout=settings.redis_timeout,
                retry_on_timeout=True
            )
            # Test connection
            self.redis_client.ping()
            logger.info("Redis connection established")
        except (redis.ConnectionError, redis.TimeoutError) as e:
            logger.warning(f"Redis connection failed: {e}. Using fallback cache.")
            self.redis_client = None
    
    def _generate_key(self, prefix: str, identifier: str) -> str:
        """Generate cache key with hash for long identifiers"""
        if len(identifier) > 200:
            identifier = hashlib.md5(identifier.encode()).hexdigest()
        return f"forex_signals:{prefix}:{identifier}"
    
    def _serialize_data(self, data: Any) -> str:
        """Serialize data for storage"""
        return json.dumps(data, default=str, separators=(',', ':'))
    
    def _deserialize_data(self, data: str) -> Any:
        """Deserialize data from storage"""
        try:
            return json.loads(data)
        except json.JSONDecodeError:
            return None
    
    def set(self, key: str, value: Any, ttl: int = 3600) -> bool:
        """Store data in cache with TTL"""
        cache_key = self._generate_key("cache", key)
        serialized_value = self._serialize_data(value)
        
        # Try Redis first
        if self.redis_client:
            try:
                self.redis_client.setex(cache_key, ttl, serialized_value)
                return True
            except (redis.ConnectionError, redis.TimeoutError) as e:
                logger.warning(f"Redis set failed: {e}. Using fallback.")
                self.redis_client = None
        
        # Fallback to memory cache
        self._fallback_set(cache_key, serialized_value, ttl)
        return True
    
    def get(self, key: str) -> Optional[Any]:
        """Retrieve data from cache"""
        cache_key = self._generate_key("cache", key)
        
        # Try Redis first
        if self.redis_client:
            try:
                data = self.redis_client.get(cache_key)
                if data:
                    return self._deserialize_data(data)
            except (redis.ConnectionError, redis.TimeoutError) as e:
                logger.warning(f"Redis get failed: {e}. Using fallback.")
                self.redis_client = None
        
        # Fallback to memory cache
        return self._fallback_get(cache_key)
    
    def delete(self, key: str) -> bool:
        """Delete data from cache"""
        cache_key = self._generate_key("cache", key)
        
        # Try Redis first
        if self.redis_client:
            try:
                self.redis_client.delete(cache_key)
            except (redis.ConnectionError, redis.TimeoutError):
                pass
        
        # Remove from fallback cache
        self.fallback_cache.pop(cache_key, None)
        return True
    
    def _fallback_set(self, key: str, value: str, ttl: int):
        """Store in memory fallback cache"""
        if len(self.fallback_cache) >= self.max_fallback_size:
            # Remove oldest entries
            oldest_keys = list(self.fallback_cache.keys())[:100]
            for old_key in oldest_keys:
                self.fallback_cache.pop(old_key, None)
        
        expiry = datetime.now() + timedelta(seconds=ttl)
        self.fallback_cache[key] = {
            'value': value,
            'expiry': expiry
        }
    
    def _fallback_get(self, key: str) -> Optional[Any]:
        """Get from memory fallback cache"""
        if key not in self.fallback_cache:
            return None
        
        cache_entry = self.fallback_cache[key]
        if datetime.now() > cache_entry['expiry']:
            self.fallback_cache.pop(key, None)
            return None
        
        return self._deserialize_data(cache_entry['value'])
    
    def cache_api_response(self, api_name: str, endpoint: str, params: Dict, 
                          response_data: Any, ttl: int = None) -> bool:
        """Cache API response with specific TTL based on data type"""
        if ttl is None:
            ttl = self._get_default_ttl(api_name)
        
        # Create unique cache key from endpoint and params
        param_str = json.dumps(params, sort_keys=True, separators=(',', ':'))
        cache_key = f"{api_name}:{endpoint}:{hashlib.md5(param_str.encode()).hexdigest()}"
        
        # Add timestamp to cached data
        cached_data = {
            'data': response_data,
            'timestamp': datetime.now().isoformat(),
            'api_name': api_name,
            'endpoint': endpoint
        }
        
        return self.set(cache_key, cached_data, ttl)
    
    def get_cached_api_response(self, api_name: str, endpoint: str, 
                               params: Dict) -> Optional[Any]:
        """Retrieve cached API response"""
        param_str = json.dumps(params, sort_keys=True, separators=(',', ':'))
        cache_key = f"{api_name}:{endpoint}:{hashlib.md5(param_str.encode()).hexdigest()}"
        
        cached_data = self.get(cache_key)
        if cached_data and isinstance(cached_data, dict):
            return cached_data.get('data')
        
        return None
    
    def _get_default_ttl(self, api_name: str) -> int:
        """Get default TTL based on API type"""
        ttl_mapping = {
            'alpha_vantage': settings.forex_data_cache_ttl,
            'twelve_data': settings.forex_data_cache_ttl,
            'fred': settings.economic_data_cache_ttl,
            'finnhub': settings.economic_data_cache_ttl,
            'news_api': settings.news_cache_ttl,
            'reddit': settings.news_cache_ttl,
            'central_bank': settings.economic_data_cache_ttl,
            'gdelt': settings.news_cache_ttl
        }
        return ttl_mapping.get(api_name, 3600)
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        stats = {
            'redis_connected': self.redis_client is not None,
            'fallback_entries': len(self.fallback_cache),
            'fallback_max_size': self.max_fallback_size
        }
        
        if self.redis_client:
            try:
                redis_info = self.redis_client.info()
                stats.update({
                    'redis_memory_used': redis_info.get('used_memory_human', 'N/A'),
                    'redis_connected_clients': redis_info.get('connected_clients', 0),
                    'redis_total_commands': redis_info.get('total_commands_processed', 0)
                })
            except (redis.ConnectionError, redis.TimeoutError):
                stats['redis_connected'] = False
        
        return stats
    
    def clear_cache(self, pattern: str = None) -> int:
        """Clear cache entries matching pattern"""
        cleared_count = 0
        
        if self.redis_client:
            try:
                if pattern:
                    cache_pattern = self._generate_key("cache", pattern)
                    keys = self.redis_client.keys(cache_pattern)
                    if keys:
                        cleared_count = self.redis_client.delete(*keys)
                else:
                    # Clear all forex signal cache entries
                    keys = self.redis_client.keys("forex_signals:*")
                    if keys:
                        cleared_count = self.redis_client.delete(*keys)
            except (redis.ConnectionError, redis.TimeoutError):
                pass
        
        # Clear fallback cache
        if pattern:
            cache_pattern = self._generate_key("cache", pattern)
            keys_to_remove = [k for k in self.fallback_cache.keys() if cache_pattern in k]
            for key in keys_to_remove:
                self.fallback_cache.pop(key, None)
                cleared_count += 1
        else:
            cleared_count += len(self.fallback_cache)
            self.fallback_cache.clear()
        
        return cleared_count

def cached(ttl: int = 3600, key_func: callable = None):
    """Decorator for caching function results"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Generate cache key
            if key_func:
                cache_key = key_func(*args, **kwargs)
            else:
                # Default key generation
                key_parts = [func.__name__]
                key_parts.extend(str(arg) for arg in args)
                key_parts.extend(f"{k}={v}" for k, v in sorted(kwargs.items()))
                cache_key = ":".join(key_parts)
            
            # Try to get from cache
            cached_result = cache_manager.get(cache_key)
            if cached_result is not None:
                logger.debug(f"Cache hit for {func.__name__}")
                return cached_result
            
            # Execute function and cache result
            logger.debug(f"Cache miss for {func.__name__}")
            result = func(*args, **kwargs)
            cache_manager.set(cache_key, result, ttl)
            
            return result
        return wrapper
    return decorator

def price_data_cache(ttl: int = None):
    """Specialized cache decorator for price data"""
    if ttl is None:
        ttl = settings.cache_ttl_price_data
    
    def key_func(*args, **kwargs):
        return f"price_data:{args[0] if args else ''}:{kwargs.get('timeframe', '')}"
    
    return cached(ttl=ttl, key_func=key_func)

def economic_data_cache(ttl: int = None):
    """Specialized cache decorator for economic data"""
    if ttl is None:
        ttl = settings.cache_ttl_economic_data
    
    def key_func(*args, **kwargs):
        return f"economic_data:{args[0] if args else ''}:{kwargs.get('indicator', '')}"
    
    return cached(ttl=ttl, key_func=key_func)

# Global cache manager instance
cache_manager = CacheManager()