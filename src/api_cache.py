#!/usr/bin/env python3
"""
API Cache Manager
Caches API responses to reduce rate limit issues
Especially important for 6 AM scheduled runs
"""

import json
import os
from datetime import datetime, timedelta
from typing import Dict, Optional, Any
import logging

logger = logging.getLogger(__name__)

class APICache:
    """Simple file-based cache for API responses"""
    
    def __init__(self, cache_dir: str = "cache"):
        self.cache_dir = cache_dir
        os.makedirs(cache_dir, exist_ok=True)
        
        # Cache TTLs in seconds
        self.ttl_config = {
            'forex_price': 30,        # 30 seconds for prices
            'forex_data': 300,        # 5 minutes for historical data
            'economic': 86400,        # 24 hours for economic data
            'sentiment': 21600,       # 6 hours for sentiment
            'news': 3600,            # 1 hour for news
        }
    
    def get(self, key: str, cache_type: str = 'forex_price') -> Optional[Any]:
        """Get cached data if not expired"""
        
        cache_file = os.path.join(self.cache_dir, f"{key}.json")
        
        if not os.path.exists(cache_file):
            return None
        
        try:
            with open(cache_file, 'r') as f:
                cached = json.load(f)
            
            # Check expiry
            cached_time = datetime.fromisoformat(cached['timestamp'])
            ttl = self.ttl_config.get(cache_type, 300)
            
            if datetime.now() - cached_time < timedelta(seconds=ttl):
                logger.info(f"✅ Cache hit for {key}")
                return cached['data']
            else:
                logger.info(f"⏰ Cache expired for {key}")
                return None
                
        except Exception as e:
            logger.warning(f"Cache read error for {key}: {e}")
            return None
    
    def set(self, key: str, data: Any, cache_type: str = 'forex_price'):
        """Cache data with timestamp"""
        
        cache_file = os.path.join(self.cache_dir, f"{key}.json")
        
        try:
            # Convert datetime objects to string for JSON serialization
            if isinstance(data, dict):
                data_copy = data.copy()
                for k, v in data_copy.items():
                    if isinstance(v, datetime):
                        data_copy[k] = v.isoformat()
                data = data_copy
            
            cached = {
                'timestamp': datetime.now().isoformat(),
                'type': cache_type,
                'data': data
            }
            
            with open(cache_file, 'w') as f:
                json.dump(cached, f)
            
            logger.info(f"💾 Cached {key} (TTL: {self.ttl_config.get(cache_type, 300)}s)")
            
        except Exception as e:
            logger.warning(f"Cache write error for {key}: {e}")
    
    def clear_expired(self):
        """Clear expired cache entries"""
        
        for filename in os.listdir(self.cache_dir):
            if filename.endswith('.json'):
                filepath = os.path.join(self.cache_dir, filename)
                
                try:
                    with open(filepath, 'r') as f:
                        cached = json.load(f)
                    
                    cached_time = datetime.fromisoformat(cached['timestamp'])
                    cache_type = cached.get('type', 'forex_price')
                    ttl = self.ttl_config.get(cache_type, 300)
                    
                    if datetime.now() - cached_time > timedelta(seconds=ttl):
                        os.remove(filepath)
                        logger.info(f"🗑️  Cleared expired cache: {filename}")
                        
                except Exception as e:
                    logger.warning(f"Error checking cache file {filename}: {e}")
    
    def clear_all(self):
        """Clear all cache"""
        
        for filename in os.listdir(self.cache_dir):
            if filename.endswith('.json'):
                filepath = os.path.join(self.cache_dir, filename)
                try:
                    os.remove(filepath)
                except:
                    pass
        
        logger.info("🗑️  Cleared all cache")

# Global cache instance
api_cache = APICache()

def get_cached_or_fetch(key: str, fetch_func, cache_type: str = 'forex_price'):
    """Helper to get cached data or fetch if not available"""
    
    # Check cache first
    cached = api_cache.get(key, cache_type)
    if cached is not None:
        return cached
    
    # Fetch new data
    data = fetch_func()
    
    if data is not None:
        # Cache the result
        api_cache.set(key, data, cache_type)
    
    return data