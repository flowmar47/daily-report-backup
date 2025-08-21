#!/usr/bin/env python3
"""
Async HTTP Client Utility
High-performance async HTTP client with connection pooling, caching, and monitoring
"""

import aiohttp
import asyncio
import time
import json
import hashlib
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union
from pathlib import Path
import logging
from dataclasses import dataclass, asdict
import pickle

logger = logging.getLogger(__name__)

@dataclass
class CacheEntry:
    """Cache entry data structure"""
    data: Any
    timestamp: datetime
    ttl_seconds: int
    headers: Dict[str, str]
    
    def is_expired(self) -> bool:
        """Check if cache entry is expired"""
        return datetime.now() > self.timestamp + timedelta(seconds=self.ttl_seconds)

@dataclass
class RequestMetrics:
    """Request performance metrics"""
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    cache_hits: int = 0
    cache_misses: int = 0
    total_response_time: float = 0.0
    average_response_time: float = 0.0
    bytes_downloaded: int = 0
    
    def add_request(self, success: bool, response_time: float, bytes_size: int = 0, cache_hit: bool = False):
        """Add request metrics"""
        self.total_requests += 1
        self.total_response_time += response_time
        self.average_response_time = self.total_response_time / self.total_requests
        self.bytes_downloaded += bytes_size
        
        if cache_hit:
            self.cache_hits += 1
        else:
            self.cache_misses += 1
            
        if success:
            self.successful_requests += 1
        else:
            self.failed_requests += 1

class AsyncHttpClient:
    """High-performance async HTTP client with caching and monitoring"""
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        
        # Connection pool settings
        self.connector = aiohttp.TCPConnector(
            limit=self.config.get('connection_pool_size', 100),
            limit_per_host=self.config.get('connections_per_host', 30),
            ttl_dns_cache=self.config.get('dns_cache_ttl', 300),
            use_dns_cache=True,
            keepalive_timeout=self.config.get('keepalive_timeout', 30),
            enable_cleanup_closed=True,
            ssl=False if self.config.get('disable_ssl_verify', False) else None
        )
        
        # Session timeout
        self.timeout = aiohttp.ClientTimeout(
            total=self.config.get('request_timeout', 30),
            connect=self.config.get('connect_timeout', 10),
            sock_read=self.config.get('read_timeout', 20)
        )
        
        # Rate limiting
        self.rate_limiter = asyncio.Semaphore(self.config.get('concurrent_requests', 10))
        self.request_delay = self.config.get('request_delay', 0.1)
        
        # Caching
        self.cache_enabled = self.config.get('cache_enabled', True)
        self.cache_dir = Path(self.config.get('cache_dir', 'cache'))
        self.cache_dir.mkdir(exist_ok=True)
        self.memory_cache: Dict[str, CacheEntry] = {}
        self.max_memory_cache_size = self.config.get('max_memory_cache_size', 1000)
        
        # Default headers
        self.default_headers = {
            'User-Agent': self.config.get('user_agent', 
                'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36'),
            'Accept': 'application/json, text/html, application/xhtml+xml, application/xml;q=0.9, */*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        }
        
        # Performance metrics
        self.metrics = RequestMetrics()
        
        # Session
        self._session: Optional[aiohttp.ClientSession] = None
        self._session_lock = asyncio.Lock()

    async def get_session(self) -> aiohttp.ClientSession:
        """Get or create session with lazy initialization"""
        if self._session is None or self._session.closed:
            async with self._session_lock:
                if self._session is None or self._session.closed:
                    self._session = aiohttp.ClientSession(
                        connector=self.connector,
                        timeout=self.timeout,
                        headers=self.default_headers
                    )
                    logger.info("🔗 Created new HTTP session")
        return self._session

    def _get_cache_key(self, url: str, params: Dict = None, headers: Dict = None) -> str:
        """Generate cache key for request"""
        cache_data = {
            'url': url,
            'params': params or {},
            'headers': headers or {}
        }
        cache_string = json.dumps(cache_data, sort_keys=True)
        return hashlib.md5(cache_string.encode()).hexdigest()

    def _get_from_memory_cache(self, cache_key: str) -> Optional[CacheEntry]:
        """Get entry from memory cache"""
        if cache_key in self.memory_cache:
            entry = self.memory_cache[cache_key]
            if not entry.is_expired():
                return entry
            else:
                # Remove expired entry
                del self.memory_cache[cache_key]
        return None

    def _save_to_memory_cache(self, cache_key: str, entry: CacheEntry):
        """Save entry to memory cache with size limit"""
        # Clean up expired entries if cache is getting full
        if len(self.memory_cache) >= self.max_memory_cache_size:
            expired_keys = [k for k, v in self.memory_cache.items() if v.is_expired()]
            for key in expired_keys:
                del self.memory_cache[key]
            
            # If still at limit, remove oldest entries
            if len(self.memory_cache) >= self.max_memory_cache_size:
                # Remove 10% of oldest entries
                sorted_entries = sorted(self.memory_cache.items(), key=lambda x: x[1].timestamp)
                entries_to_remove = len(sorted_entries) // 10
                for key, _ in sorted_entries[:entries_to_remove]:
                    del self.memory_cache[key]
        
        self.memory_cache[cache_key] = entry

    def _get_from_disk_cache(self, cache_key: str) -> Optional[CacheEntry]:
        """Get entry from disk cache"""
        cache_file = self.cache_dir / f"{cache_key}.cache"
        try:
            if cache_file.exists():
                with open(cache_file, 'rb') as f:
                    entry = pickle.load(f)
                    if not entry.is_expired():
                        return entry
                    else:
                        # Remove expired file
                        cache_file.unlink()
        except Exception as e:
            logger.warning(f"Error reading disk cache: {e}")
        return None

    def _save_to_disk_cache(self, cache_key: str, entry: CacheEntry):
        """Save entry to disk cache"""
        cache_file = self.cache_dir / f"{cache_key}.cache"
        try:
            with open(cache_file, 'wb') as f:
                pickle.dump(entry, f)
        except Exception as e:
            logger.warning(f"Error writing disk cache: {e}")

    async def request(self, method: str, url: str, params: Dict = None, 
                     headers: Dict = None, data: Any = None, json_data: Dict = None,
                     cache_ttl: int = None, **kwargs) -> Optional[Dict[str, Any]]:
        """Make async HTTP request with caching and rate limiting"""
        
        # Merge headers
        request_headers = self.default_headers.copy()
        if headers:
            request_headers.update(headers)
        
        # Check cache for GET requests
        cache_key = None
        if method.upper() == 'GET' and self.cache_enabled and cache_ttl is not None:
            cache_key = self._get_cache_key(url, params, request_headers)
            
            # Try memory cache first
            cached_entry = self._get_from_memory_cache(cache_key)
            if cached_entry:
                self.metrics.add_request(True, 0.001, 0, cache_hit=True)  # Very fast cache hit
                logger.debug(f"📦 Memory cache hit for {url}")
                return cached_entry.data
            
            # Try disk cache
            cached_entry = self._get_from_disk_cache(cache_key)
            if cached_entry:
                # Save to memory cache for faster access
                self._save_to_memory_cache(cache_key, cached_entry)
                self.metrics.add_request(True, 0.01, 0, cache_hit=True)  # Fast disk cache hit
                logger.debug(f"💽 Disk cache hit for {url}")
                return cached_entry.data
        
        # Rate limiting
        async with self.rate_limiter:
            if self.request_delay > 0:
                await asyncio.sleep(self.request_delay)
            
            start_time = time.time()
            session = await self.get_session()
            
            try:
                # Prepare request kwargs
                request_kwargs = {
                    'params': params,
                    'headers': request_headers,
                    **kwargs
                }
                
                if data is not None:
                    request_kwargs['data'] = data
                if json_data is not None:
                    request_kwargs['json'] = json_data
                
                async with session.request(method, url, **request_kwargs) as response:
                    response_time = time.time() - start_time
                    
                    # Get response data
                    content_type = response.headers.get('content-type', '').lower()
                    if 'json' in content_type:
                        response_data = await response.json()
                    else:
                        response_data = await response.text()
                    
                    # Calculate response size
                    content_length = response.headers.get('content-length')
                    response_size = int(content_length) if content_length else len(str(response_data))
                    
                    # Check if request was successful
                    response.raise_for_status()
                    
                    # Update metrics
                    self.metrics.add_request(True, response_time, response_size, cache_hit=False)
                    
                    result = {
                        'data': response_data,
                        'status': response.status,
                        'headers': dict(response.headers),
                        'url': str(response.url),
                        'response_time': response_time
                    }
                    
                    # Cache successful GET requests
                    if (method.upper() == 'GET' and self.cache_enabled and 
                        cache_ttl is not None and cache_key and response.status == 200):
                        
                        cache_entry = CacheEntry(
                            data=result,
                            timestamp=datetime.now(),
                            ttl_seconds=cache_ttl,
                            headers=dict(response.headers)
                        )
                        
                        # Save to both memory and disk cache
                        self._save_to_memory_cache(cache_key, cache_entry)
                        if cache_ttl > 300:  # Only disk cache for longer TTL
                            self._save_to_disk_cache(cache_key, cache_entry)
                    
                    logger.debug(f"✅ {method} {url} completed in {response_time:.2f}s")
                    return result
                    
            except asyncio.TimeoutError:
                response_time = time.time() - start_time
                self.metrics.add_request(False, response_time)
                logger.error(f"⏰ Request timeout for {method} {url} after {response_time:.2f}s")
                return None
                
            except aiohttp.ClientError as e:
                response_time = time.time() - start_time
                self.metrics.add_request(False, response_time)
                logger.error(f"❌ Client error for {method} {url}: {e}")
                return None
                
            except Exception as e:
                response_time = time.time() - start_time
                self.metrics.add_request(False, response_time)
                logger.error(f"❌ Unexpected error for {method} {url}: {e}")
                return None

    async def get(self, url: str, params: Dict = None, headers: Dict = None, 
                 cache_ttl: int = 3600, **kwargs) -> Optional[Dict[str, Any]]:
        """Make GET request with caching"""
        return await self.request('GET', url, params=params, headers=headers, 
                                cache_ttl=cache_ttl, **kwargs)

    async def post(self, url: str, data: Any = None, json_data: Dict = None, 
                  headers: Dict = None, **kwargs) -> Optional[Dict[str, Any]]:
        """Make POST request"""
        return await self.request('POST', url, data=data, json_data=json_data, 
                                headers=headers, **kwargs)

    async def put(self, url: str, data: Any = None, json_data: Dict = None, 
                 headers: Dict = None, **kwargs) -> Optional[Dict[str, Any]]:
        """Make PUT request"""
        return await self.request('PUT', url, data=data, json_data=json_data, 
                                headers=headers, **kwargs)

    async def delete(self, url: str, headers: Dict = None, **kwargs) -> Optional[Dict[str, Any]]:
        """Make DELETE request"""
        return await self.request('DELETE', url, headers=headers, **kwargs)

    async def download_file(self, url: str, file_path: Path, headers: Dict = None, 
                           chunk_size: int = 8192) -> bool:
        """Download file with progress tracking"""
        session = await self.get_session()
        
        try:
            async with session.get(url, headers=headers) as response:
                response.raise_for_status()
                
                file_path.parent.mkdir(parents=True, exist_ok=True)
                
                with open(file_path, 'wb') as f:
                    downloaded = 0
                    async for chunk in response.content.iter_chunked(chunk_size):
                        f.write(chunk)
                        downloaded += len(chunk)
                
                logger.info(f"📥 Downloaded {downloaded} bytes to {file_path}")
                return True
                
        except Exception as e:
            logger.error(f"❌ Download failed for {url}: {e}")
            return False

    def clear_cache(self, memory_only: bool = False):
        """Clear cache"""
        # Clear memory cache
        self.memory_cache.clear()
        logger.info("🗑️ Memory cache cleared")
        
        # Clear disk cache
        if not memory_only:
            try:
                for cache_file in self.cache_dir.glob("*.cache"):
                    cache_file.unlink()
                logger.info("🗑️ Disk cache cleared")
            except Exception as e:
                logger.warning(f"Error clearing disk cache: {e}")

    def get_metrics(self) -> Dict[str, Any]:
        """Get performance metrics"""
        cache_hit_rate = 0
        if self.metrics.total_requests > 0:
            cache_hit_rate = (self.metrics.cache_hits / self.metrics.total_requests) * 100
        
        success_rate = 0
        if self.metrics.total_requests > 0:
            success_rate = (self.metrics.successful_requests / self.metrics.total_requests) * 100
        
        return {
            **asdict(self.metrics),
            'cache_hit_rate_percent': round(cache_hit_rate, 2),
            'success_rate_percent': round(success_rate, 2),
            'memory_cache_size': len(self.memory_cache),
            'connection_pool_size': self.connector.limit,
            'active_connections': len(self.connector._conns)
        }

    async def close(self):
        """Close session and cleanup resources"""
        if self._session and not self._session.closed:
            await self._session.close()
            logger.info("🔚 HTTP session closed")
        
        if self.connector:
            await self.connector.close()
            logger.info("🔌 Connection pool closed")

# Global client instance
_global_client: Optional[AsyncHttpClient] = None

async def get_http_client(config: Dict[str, Any] = None) -> AsyncHttpClient:
    """Get global HTTP client instance"""
    global _global_client
    
    if _global_client is None:
        _global_client = AsyncHttpClient(config)
        logger.info("🌐 Created global HTTP client")
    
    return _global_client

async def close_global_client():
    """Close global HTTP client"""
    global _global_client
    
    if _global_client:
        await _global_client.close()
        _global_client = None

# Context manager for client lifecycle
class AsyncHttpClientManager:
    """Context manager for HTTP client lifecycle"""
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config
        self.client: Optional[AsyncHttpClient] = None
    
    async def __aenter__(self) -> AsyncHttpClient:
        self.client = AsyncHttpClient(self.config)
        return self.client
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.client:
            await self.client.close()

async def main():
    """Test the async HTTP client"""
    config = {
        'connection_pool_size': 50,
        'concurrent_requests': 10,
        'request_delay': 0.1,
        'cache_enabled': True
    }
    
    async with AsyncHttpClientManager(config) as client:
        # Test GET request with caching
        response = await client.get('https://httpbin.org/json', cache_ttl=60)
        if response:
            print(f"✅ Response status: {response['status']}")
            print(f"📊 Response time: {response['response_time']:.2f}s")
        
        # Test cached request (should be much faster)
        response2 = await client.get('https://httpbin.org/json', cache_ttl=60)
        if response2:
            print(f"📦 Cached response time: {response2['response_time']:.2f}s")
        
        # Print metrics
        metrics = client.get_metrics()
        print(f"📈 Metrics: {json.dumps(metrics, indent=2)}")

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())