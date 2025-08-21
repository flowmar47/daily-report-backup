"""Advanced caching optimization for API responses and data processing."""

import hashlib
import json
import time
from typing import Any, Dict, List, Optional, Callable, Union
from datetime import datetime, timedelta
from functools import wraps
from dataclasses import dataclass
import threading
from collections import defaultdict, OrderedDict

from .logging_config import get_logger
from .exceptions import CacheException, CacheConnectionError


logger = get_logger(__name__)


@dataclass
class CacheEntry:
    """Represents a cache entry with metadata."""
    data: Any
    timestamp: float
    ttl: int
    access_count: int = 0
    last_accessed: float = 0
    size_bytes: int = 0
    tags: List[str] = None
    
    def __post_init__(self):
        if self.tags is None:
            self.tags = []
        self.last_accessed = time.time()
        if isinstance(self.data, (str, bytes)):
            self.size_bytes = len(self.data)
        else:
            # Estimate size for other data types
            try:
                self.size_bytes = len(json.dumps(self.data, default=str))
            except (TypeError, ValueError):
                self.size_bytes = 1024  # Default estimate
    
    def is_expired(self) -> bool:
        """Check if cache entry is expired."""
        return time.time() - self.timestamp > self.ttl
    
    def access(self) -> Any:
        """Access the cached data and update metadata."""
        self.access_count += 1
        self.last_accessed = time.time()
        return self.data


class LRUCache:
    """Thread-safe LRU cache with size limits and TTL support."""
    
    def __init__(self, max_size: int = 1000, max_memory_mb: int = 100):
        self.max_size = max_size
        self.max_memory_bytes = max_memory_mb * 1024 * 1024
        self.cache: OrderedDict[str, CacheEntry] = OrderedDict()
        self.lock = threading.RLock()
        self.stats = {
            'hits': 0,
            'misses': 0,
            'evictions': 0,
            'memory_evictions': 0
        }
    
    def _evict_expired(self) -> None:
        """Remove expired entries."""
        current_time = time.time()
        expired_keys = [
            key for key, entry in self.cache.items()
            if current_time - entry.timestamp > entry.ttl
        ]
        
        for key in expired_keys:
            del self.cache[key]
            self.stats['evictions'] += 1
    
    def _evict_lru(self) -> None:
        """Evict least recently used entries to maintain size limits."""
        # Evict by count
        while len(self.cache) >= self.max_size:
            self.cache.popitem(last=False)
            self.stats['evictions'] += 1
        
        # Evict by memory usage
        total_memory = sum(entry.size_bytes for entry in self.cache.values())
        while total_memory > self.max_memory_bytes and self.cache:
            _, entry = self.cache.popitem(last=False)
            total_memory -= entry.size_bytes
            self.stats['memory_evictions'] += 1
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        with self.lock:
            self._evict_expired()
            
            if key in self.cache:
                entry = self.cache[key]
                if not entry.is_expired():
                    # Move to end (most recently used)
                    self.cache.move_to_end(key)
                    self.stats['hits'] += 1
                    return entry.access()
                else:
                    del self.cache[key]
                    self.stats['evictions'] += 1
            
            self.stats['misses'] += 1
            return None
    
    def set(self, key: str, value: Any, ttl: int = 3600, tags: List[str] = None) -> None:
        """Set value in cache."""
        with self.lock:
            entry = CacheEntry(
                data=value,
                timestamp=time.time(),
                ttl=ttl,
                tags=tags or []
            )
            
            self.cache[key] = entry
            self.cache.move_to_end(key)
            
            self._evict_lru()
    
    def delete(self, key: str) -> bool:
        """Delete key from cache."""
        with self.lock:
            if key in self.cache:
                del self.cache[key]
                return True
            return False
    
    def clear(self) -> None:
        """Clear all cache entries."""
        with self.lock:
            self.cache.clear()
    
    def clear_by_tags(self, tags: List[str]) -> int:
        """Clear cache entries by tags."""
        with self.lock:
            keys_to_delete = []
            for key, entry in self.cache.items():
                if any(tag in entry.tags for tag in tags):
                    keys_to_delete.append(key)
            
            for key in keys_to_delete:
                del self.cache[key]
            
            return len(keys_to_delete)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        with self.lock:
            total_memory = sum(entry.size_bytes for entry in self.cache.values())
            hit_rate = self.stats['hits'] / (self.stats['hits'] + self.stats['misses']) if (self.stats['hits'] + self.stats['misses']) > 0 else 0
            
            return {
                'size': len(self.cache),
                'max_size': self.max_size,
                'memory_usage_mb': total_memory / (1024 * 1024),
                'max_memory_mb': self.max_memory_bytes / (1024 * 1024),
                'hit_rate': hit_rate,
                **self.stats
            }


class SmartCacheManager:
    """Advanced cache manager with intelligent caching strategies."""
    
    def __init__(self):
        self.caches: Dict[str, LRUCache] = {
            'api_responses': LRUCache(max_size=500, max_memory_mb=50),
            'processed_data': LRUCache(max_size=200, max_memory_mb=30),
            'analysis_results': LRUCache(max_size=100, max_memory_mb=20),
            'temporary': LRUCache(max_size=50, max_memory_mb=10)
        }
        self.cache_strategies = {
            'api_responses': self._api_response_strategy,
            'processed_data': self._processed_data_strategy,
            'analysis_results': self._analysis_results_strategy
        }
    
    def _generate_cache_key(self, prefix: str, *args, **kwargs) -> str:
        """Generate a consistent cache key."""
        # Create a deterministic key from arguments
        key_data = {
            'args': args,
            'kwargs': sorted(kwargs.items()) if kwargs else {}
        }
        
        key_string = json.dumps(key_data, sort_keys=True, default=str)
        key_hash = hashlib.md5(key_string.encode()).hexdigest()[:16]
        
        return f"{prefix}:{key_hash}"
    
    def _api_response_strategy(self, api_name: str, endpoint: str, params: Dict) -> Dict[str, Any]:
        """Caching strategy for API responses."""
        # Longer TTL for stable data, shorter for volatile data
        ttl_map = {
            'alpha_vantage': 3600,  # 1 hour for forex data
            'twelve_data': 1800,    # 30 minutes for real-time data
            'fred': 14400,          # 4 hours for economic data
            'finnhub': 3600,        # 1 hour for economic calendar
            'news_api': 1800,       # 30 minutes for news
            'reddit': 900           # 15 minutes for social sentiment
        }
        
        return {
            'ttl': ttl_map.get(api_name, 3600),
            'tags': [api_name, 'api_response'],
            'cache_name': 'api_responses'
        }
    
    def _processed_data_strategy(self, data_type: str, timeframe: str = None) -> Dict[str, Any]:
        """Caching strategy for processed data."""
        # Adjust TTL based on data type and timeframe
        base_ttl = 3600
        
        if timeframe:
            timeframe_multipliers = {
                '1min': 0.1,
                '5min': 0.2,
                '15min': 0.5,
                '30min': 0.8,
                '1hour': 1.0,
                '4hour': 2.0,
                'daily': 4.0
            }
            multiplier = timeframe_multipliers.get(timeframe, 1.0)
            ttl = int(base_ttl * multiplier)
        else:
            ttl = base_ttl
        
        return {
            'ttl': ttl,
            'tags': [data_type, 'processed_data', timeframe] if timeframe else [data_type, 'processed_data'],
            'cache_name': 'processed_data'
        }
    
    def _analysis_results_strategy(self, analysis_type: str, pair: str = None) -> Dict[str, Any]:
        """Caching strategy for analysis results."""
        # Analysis results can be cached longer as they're computationally expensive
        ttl_map = {
            'technical': 1800,      # 30 minutes
            'sentiment': 900,       # 15 minutes
            'economic': 3600,       # 1 hour
            'signal': 600           # 10 minutes
        }
        
        tags = [analysis_type, 'analysis']
        if pair:
            tags.append(pair)
        
        return {
            'ttl': ttl_map.get(analysis_type, 1800),
            'tags': tags,
            'cache_name': 'analysis_results'
        }
    
    def get(self, cache_type: str, key: str) -> Optional[Any]:
        """Get value from specific cache."""
        if cache_type not in self.caches:
            logger.warning(f"Unknown cache type: {cache_type}")
            return None
        
        return self.caches[cache_type].get(key)
    
    def set(self, cache_type: str, key: str, value: Any, **strategy_kwargs) -> None:
        """Set value in cache using intelligent strategy."""
        if cache_type not in self.caches:
            logger.warning(f"Unknown cache type: {cache_type}")
            return
        
        # Apply caching strategy
        if cache_type in self.cache_strategies:
            strategy = self.cache_strategies[cache_type](**strategy_kwargs)
            ttl = strategy.get('ttl', 3600)
            tags = strategy.get('tags', [])
            target_cache = strategy.get('cache_name', cache_type)
        else:
            ttl = 3600
            tags = []
            target_cache = cache_type
        
        if target_cache in self.caches:
            self.caches[target_cache].set(key, value, ttl=ttl, tags=tags)
    
    def invalidate_by_tags(self, tags: List[str]) -> int:
        """Invalidate cache entries across all caches by tags."""
        total_cleared = 0
        for cache in self.caches.values():
            total_cleared += cache.clear_by_tags(tags)
        
        logger.info(f"Invalidated {total_cleared} cache entries with tags: {tags}")
        return total_cleared
    
    def get_global_stats(self) -> Dict[str, Any]:
        """Get statistics for all caches."""
        stats = {}
        total_memory = 0
        total_entries = 0
        
        for cache_name, cache in self.caches.items():
            cache_stats = cache.get_stats()
            stats[cache_name] = cache_stats
            total_memory += cache_stats['memory_usage_mb']
            total_entries += cache_stats['size']
        
        stats['global'] = {
            'total_memory_mb': total_memory,
            'total_entries': total_entries
        }
        
        return stats


# Global cache manager instance
cache_optimizer = SmartCacheManager()


def smart_cache(cache_type: str = 'api_responses', key_prefix: str = None, **strategy_kwargs):
    """Decorator for intelligent caching of function results."""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Generate cache key
            prefix = key_prefix or f"{func.__module__}.{func.__name__}"
            cache_key = cache_optimizer._generate_cache_key(prefix, *args, **kwargs)
            
            # Try to get from cache
            cached_result = cache_optimizer.get(cache_type, cache_key)
            if cached_result is not None:
                logger.debug(f"Cache hit for {prefix}: {cache_key}")
                return cached_result
            
            # Execute function and cache result
            try:
                result = func(*args, **kwargs)
                cache_optimizer.set(cache_type, cache_key, result, **strategy_kwargs)
                logger.debug(f"Cached result for {prefix}: {cache_key}")
                return result
            except Exception as e:
                logger.error(f"Function execution failed for {prefix}: {e}")
                raise
        
        return wrapper
    return decorator


def cache_api_response(api_name: str, endpoint: str = None):
    """Decorator specifically for API response caching."""
    return smart_cache(
        cache_type='api_responses',
        key_prefix=f"api.{api_name}.{endpoint or 'default'}",
        api_name=api_name,
        endpoint=endpoint or 'default',
        params={}
    )


def cache_analysis_result(analysis_type: str, pair: str = None):
    """Decorator specifically for analysis result caching."""
    return smart_cache(
        cache_type='analysis_results',
        key_prefix=f"analysis.{analysis_type}",
        analysis_type=analysis_type,
        pair=pair
    )


def cache_processed_data(data_type: str, timeframe: str = None):
    """Decorator specifically for processed data caching."""
    return smart_cache(
        cache_type='processed_data',
        key_prefix=f"data.{data_type}",
        data_type=data_type,
        timeframe=timeframe
    )


class CacheWarmer:
    """Utility to pre-warm cache with frequently accessed data."""
    
    def __init__(self, cache_manager: SmartCacheManager):
        self.cache_manager = cache_manager
        self.warming_tasks = []
    
    def add_warming_task(self, func: Callable, args: tuple = (), kwargs: dict = None, 
                        cache_type: str = 'api_responses', **strategy_kwargs):
        """Add a function to be executed for cache warming."""
        self.warming_tasks.append({
            'func': func,
            'args': args,
            'kwargs': kwargs or {},
            'cache_type': cache_type,
            'strategy_kwargs': strategy_kwargs
        })
    
    def warm_cache(self) -> Dict[str, Any]:
        """Execute all warming tasks."""
        results = {
            'success': 0,
            'failed': 0,
            'errors': []
        }
        
        for task in self.warming_tasks:
            try:
                # Execute function (should be decorated with caching)
                task['func'](*task['args'], **task['kwargs'])
                results['success'] += 1
                logger.debug(f"Cache warming successful for {task['func'].__name__}")
            except Exception as e:
                results['failed'] += 1
                results['errors'].append({
                    'function': task['func'].__name__,
                    'error': str(e)
                })
                logger.error(f"Cache warming failed for {task['func'].__name__}: {e}")
        
        logger.info(f"Cache warming completed: {results['success']} success, {results['failed']} failed")
        return results


# Global cache warmer instance
cache_warmer = CacheWarmer(cache_optimizer)