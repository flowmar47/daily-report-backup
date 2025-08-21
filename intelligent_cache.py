#!/usr/bin/env python3
"""
Intelligent Caching Layer
Advanced caching system with TTL, LRU eviction, compression, and smart invalidation
"""

import asyncio
import json
import pickle
import gzip
import hashlib
import time
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Union, Tuple
from pathlib import Path
from dataclasses import dataclass, asdict
from enum import Enum
import logging
import threading
from collections import OrderedDict
import weakref

logger = logging.getLogger(__name__)

class CacheEntryType(Enum):
    """Types of cache entries"""
    SESSION_DATA = "session_data"
    API_RESPONSE = "api_response"
    PARSED_DATA = "parsed_data"
    FILE_CONTENT = "file_content"
    USER_DATA = "user_data"

@dataclass
class CacheStats:
    """Cache performance statistics"""
    hits: int = 0
    misses: int = 0
    sets: int = 0
    deletes: int = 0
    evictions: int = 0
    expired_cleanups: int = 0
    total_size_bytes: int = 0
    average_access_time: float = 0.0
    
    def hit_rate(self) -> float:
        """Calculate cache hit rate percentage"""
        total = self.hits + self.misses
        return (self.hits / total * 100) if total > 0 else 0.0

@dataclass
class CacheEntry:
    """Individual cache entry with metadata"""
    key: str
    value: Any
    entry_type: CacheEntryType
    created_at: datetime
    last_accessed: datetime
    access_count: int
    ttl_seconds: int
    compressed: bool = False
    size_bytes: int = 0
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}
    
    def is_expired(self) -> bool:
        """Check if entry has expired"""
        if self.ttl_seconds <= 0:  # Never expires
            return False
        return datetime.now() > self.created_at + timedelta(seconds=self.ttl_seconds)
    
    def age_seconds(self) -> float:
        """Get age of entry in seconds"""
        return (datetime.now() - self.created_at).total_seconds()
    
    def last_access_seconds(self) -> float:
        """Get seconds since last access"""
        return (datetime.now() - self.last_accessed).total_seconds()
    
    def update_access(self):
        """Update access statistics"""
        self.last_accessed = datetime.now()
        self.access_count += 1

class IntelligentCache:
    """Intelligent multi-layer cache with advanced features"""
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        
        # Cache configuration
        self.max_memory_entries = self.config.get('max_memory_entries', 1000)
        self.max_memory_size_mb = self.config.get('max_memory_size_mb', 100)
        self.max_disk_size_mb = self.config.get('max_disk_size_mb', 500)
        self.default_ttl = self.config.get('default_ttl', 3600)  # 1 hour
        self.cleanup_interval = self.config.get('cleanup_interval', 300)  # 5 minutes
        self.compression_threshold = self.config.get('compression_threshold', 1024)  # 1KB
        self.enable_compression = self.config.get('enable_compression', True)
        
        # Cache directories
        self.cache_dir = Path(self.config.get('cache_dir', 'cache'))
        self.session_cache_dir = self.cache_dir / 'sessions'
        self.api_cache_dir = self.cache_dir / 'api_responses'
        self.data_cache_dir = self.cache_dir / 'parsed_data'
        
        # Create directories
        for dir_path in [self.session_cache_dir, self.api_cache_dir, self.data_cache_dir]:
            dir_path.mkdir(parents=True, exist_ok=True)
        
        # Memory cache (LRU-like with access patterns)
        self.memory_cache: OrderedDict[str, CacheEntry] = OrderedDict()
        self.cache_lock = threading.RLock()
        
        # Statistics
        self.stats = CacheStats()
        
        # Background tasks
        self.cleanup_task: Optional[asyncio.Task] = None
        self._shutdown = False
        
        # Type-specific configurations
        self.type_configs = {
            CacheEntryType.SESSION_DATA: {
                'default_ttl': self.config.get('session_ttl', 3600),
                'disk_cache': True,
                'compression': False  # Session data is usually small
            },
            CacheEntryType.API_RESPONSE: {
                'default_ttl': self.config.get('api_response_ttl', 1800),  # 30 minutes
                'disk_cache': True,
                'compression': True
            },
            CacheEntryType.PARSED_DATA: {
                'default_ttl': self.config.get('parsed_data_ttl', 7200),  # 2 hours
                'disk_cache': True,
                'compression': True
            },
            CacheEntryType.FILE_CONTENT: {
                'default_ttl': self.config.get('file_content_ttl', 1800),
                'disk_cache': True,
                'compression': True
            },
            CacheEntryType.USER_DATA: {
                'default_ttl': self.config.get('user_data_ttl', 86400),  # 24 hours
                'disk_cache': False,  # Sensitive data
                'compression': False
            }
        }
        
        logger.info(f"🧠 Intelligent cache initialized - Memory: {self.max_memory_entries} entries, "
                   f"Disk: {self.max_disk_size_mb}MB")
    
    def _generate_key(self, namespace: str, identifier: str, 
                     params: Dict[str, Any] = None) -> str:
        """Generate a unique cache key"""
        key_parts = [namespace, identifier]
        
        if params:
            # Sort params for consistent key generation
            param_str = json.dumps(params, sort_keys=True, separators=(',', ':'))
            key_parts.append(param_str)
        
        key_string = '|'.join(key_parts)
        return hashlib.sha256(key_string.encode()).hexdigest()[:32]
    
    def _serialize_value(self, value: Any, compress: bool = False) -> Tuple[bytes, bool]:
        """Serialize and optionally compress value"""
        # Serialize
        if isinstance(value, (str, bytes)):
            serialized = value.encode() if isinstance(value, str) else value
        else:
            serialized = pickle.dumps(value, protocol=pickle.HIGHEST_PROTOCOL)
        
        # Compress if enabled and size threshold met
        compressed = False
        if (compress and self.enable_compression and 
            len(serialized) > self.compression_threshold):
            try:
                compressed_data = gzip.compress(serialized, compresslevel=6)
                if len(compressed_data) < len(serialized):  # Only use if actually smaller
                    serialized = compressed_data
                    compressed = True
                    logger.debug(f"Compressed data: {len(serialized)} -> {len(compressed_data)} bytes")
            except Exception as e:
                logger.warning(f"Compression failed: {e}")
        
        return serialized, compressed
    
    def _deserialize_value(self, data: bytes, compressed: bool = False) -> Any:
        """Deserialize and decompress value"""
        try:
            # Decompress if needed
            if compressed:
                data = gzip.decompress(data)
            
            # Try to deserialize as pickle first
            try:
                return pickle.loads(data)
            except (pickle.PickleError, EOFError):
                # Fallback to string
                return data.decode()
                
        except Exception as e:
            logger.error(f"Deserialization failed: {e}")
            raise
    
    def _get_disk_path(self, key: str, entry_type: CacheEntryType) -> Path:
        """Get disk path for cache entry"""
        type_dir_map = {
            CacheEntryType.SESSION_DATA: self.session_cache_dir,
            CacheEntryType.API_RESPONSE: self.api_cache_dir,
            CacheEntryType.PARSED_DATA: self.data_cache_dir,
            CacheEntryType.FILE_CONTENT: self.data_cache_dir,
            CacheEntryType.USER_DATA: self.cache_dir / 'user_data'
        }
        
        cache_dir = type_dir_map.get(entry_type, self.cache_dir)
        cache_dir.mkdir(parents=True, exist_ok=True)
        
        return cache_dir / f"{key}.cache"
    
    async def get(self, namespace: str, identifier: str, 
                 params: Dict[str, Any] = None) -> Optional[Any]:
        """Get value from cache"""
        key = self._generate_key(namespace, identifier, params)
        start_time = time.time()
        
        with self.cache_lock:
            # Try memory cache first
            if key in self.memory_cache:
                entry = self.memory_cache[key]
                
                if entry.is_expired():
                    # Remove expired entry
                    del self.memory_cache[key]
                    self.stats.expired_cleanups += 1
                    logger.debug(f"Removed expired memory entry: {key}")
                else:
                    # Hit! Update access stats and move to end (most recently used)
                    entry.update_access()
                    self.memory_cache.move_to_end(key)
                    self.stats.hits += 1
                    
                    access_time = time.time() - start_time
                    self._update_average_access_time(access_time)
                    
                    logger.debug(f"Memory cache hit: {key} (age: {entry.age_seconds():.1f}s)")
                    return entry.value
        
        # Try disk cache
        disk_value = await self._get_from_disk(key)
        if disk_value is not None:
            entry, value = disk_value
            
            # Add to memory cache for faster future access
            await self._add_to_memory_cache(entry)
            
            self.stats.hits += 1
            access_time = time.time() - start_time
            self._update_average_access_time(access_time)
            
            logger.debug(f"Disk cache hit: {key}")
            return value
        
        # Cache miss
        self.stats.misses += 1
        access_time = time.time() - start_time
        self._update_average_access_time(access_time)
        
        logger.debug(f"Cache miss: {key}")
        return None
    
    async def set(self, namespace: str, identifier: str, value: Any,
                 entry_type: CacheEntryType = CacheEntryType.USER_DATA,
                 ttl: int = None, params: Dict[str, Any] = None,
                 metadata: Dict[str, Any] = None) -> bool:
        """Set value in cache"""
        key = self._generate_key(namespace, identifier, params)
        
        # Get type-specific configuration
        type_config = self.type_configs.get(entry_type, {})
        if ttl is None:
            ttl = type_config.get('default_ttl', self.default_ttl)
        
        # Create cache entry
        serialized_data, compressed = self._serialize_value(
            value, 
            compress=type_config.get('compression', False)
        )
        
        entry = CacheEntry(
            key=key,
            value=value,
            entry_type=entry_type,
            created_at=datetime.now(),
            last_accessed=datetime.now(),
            access_count=1,
            ttl_seconds=ttl,
            compressed=compressed,
            size_bytes=len(serialized_data),
            metadata=metadata or {}
        )
        
        # Add to memory cache
        await self._add_to_memory_cache(entry)
        
        # Add to disk cache if configured
        if type_config.get('disk_cache', True):
            await self._save_to_disk(entry, serialized_data)
        
        self.stats.sets += 1
        self.stats.total_size_bytes += entry.size_bytes
        
        logger.debug(f"Cache set: {key} (type: {entry_type.value}, ttl: {ttl}s, size: {entry.size_bytes} bytes)")
        return True
    
    async def _add_to_memory_cache(self, entry: CacheEntry):
        """Add entry to memory cache with eviction if needed"""
        with self.cache_lock:
            # Check if we need to evict entries
            await self._evict_if_needed()
            
            # Add/update entry
            self.memory_cache[entry.key] = entry
            self.memory_cache.move_to_end(entry.key)  # Mark as most recently used
    
    async def _evict_if_needed(self):
        """Evict entries if cache limits are exceeded"""
        # Check entry count limit
        while len(self.memory_cache) >= self.max_memory_entries:
            # Remove least recently used entry
            oldest_key, oldest_entry = self.memory_cache.popitem(last=False)
            self.stats.evictions += 1
            self.stats.total_size_bytes = max(0, self.stats.total_size_bytes - oldest_entry.size_bytes)
            logger.debug(f"Evicted LRU entry: {oldest_key}")
        
        # Check memory size limit
        max_size_bytes = self.max_memory_size_mb * 1024 * 1024
        current_size = sum(entry.size_bytes for entry in self.memory_cache.values())
        
        while current_size > max_size_bytes and self.memory_cache:
            # Remove least recently used entry
            oldest_key, oldest_entry = self.memory_cache.popitem(last=False)
            current_size -= oldest_entry.size_bytes
            self.stats.evictions += 1
            self.stats.total_size_bytes = max(0, self.stats.total_size_bytes - oldest_entry.size_bytes)
            logger.debug(f"Evicted oversized entry: {oldest_key} ({oldest_entry.size_bytes} bytes)")
    
    async def _save_to_disk(self, entry: CacheEntry, serialized_data: bytes):
        """Save entry to disk cache"""
        try:
            disk_path = self._get_disk_path(entry.key, entry.entry_type)
            
            # Create cache file data
            cache_data = {
                'entry': asdict(entry),
                'data': serialized_data
            }
            
            # Write to temporary file first, then rename for atomicity
            temp_path = disk_path.with_suffix('.tmp')
            with open(temp_path, 'wb') as f:
                pickle.dump(cache_data, f, protocol=pickle.HIGHEST_PROTOCOL)
            
            temp_path.rename(disk_path)
            logger.debug(f"Saved to disk: {entry.key} -> {disk_path}")
            
        except Exception as e:
            logger.error(f"Failed to save to disk cache: {e}")
    
    async def _get_from_disk(self, key: str) -> Optional[Tuple[CacheEntry, Any]]:
        """Get entry from disk cache"""
        # Try all possible entry types
        for entry_type in CacheEntryType:
            disk_path = self._get_disk_path(key, entry_type)
            
            if disk_path.exists():
                try:
                    with open(disk_path, 'rb') as f:
                        cache_data = pickle.load(f)
                    
                    # Reconstruct cache entry
                    entry_dict = cache_data['entry']
                    entry_dict['created_at'] = datetime.fromisoformat(entry_dict['created_at'])
                    entry_dict['last_accessed'] = datetime.fromisoformat(entry_dict['last_accessed'])
                    entry_dict['entry_type'] = CacheEntryType(entry_dict['entry_type'])
                    
                    entry = CacheEntry(**entry_dict)
                    
                    # Check if expired
                    if entry.is_expired():
                        disk_path.unlink()  # Remove expired file
                        logger.debug(f"Removed expired disk entry: {key}")
                        continue
                    
                    # Deserialize data
                    value = self._deserialize_value(
                        cache_data['data'], 
                        entry.compressed
                    )
                    
                    # Update access stats
                    entry.update_access()
                    
                    return entry, value
                    
                except Exception as e:
                    logger.warning(f"Failed to load disk cache {disk_path}: {e}")
                    # Remove corrupted file
                    try:
                        disk_path.unlink()
                    except:
                        pass
        
        return None
    
    async def delete(self, namespace: str, identifier: str, 
                    params: Dict[str, Any] = None) -> bool:
        """Delete entry from cache"""
        key = self._generate_key(namespace, identifier, params)
        
        deleted = False
        
        # Remove from memory cache
        with self.cache_lock:
            if key in self.memory_cache:
                entry = self.memory_cache.pop(key)
                self.stats.deletes += 1
                self.stats.total_size_bytes = max(0, self.stats.total_size_bytes - entry.size_bytes)
                deleted = True
                logger.debug(f"Deleted from memory: {key}")
        
        # Remove from disk cache
        for entry_type in CacheEntryType:
            disk_path = self._get_disk_path(key, entry_type)
            if disk_path.exists():
                try:
                    disk_path.unlink()
                    deleted = True
                    logger.debug(f"Deleted from disk: {key}")
                except Exception as e:
                    logger.warning(f"Failed to delete disk cache: {e}")
        
        return deleted
    
    async def clear(self, entry_type: CacheEntryType = None, 
                   namespace: str = None) -> int:
        """Clear cache entries"""
        cleared_count = 0
        
        # Clear memory cache
        with self.cache_lock:
            if entry_type is None and namespace is None:
                # Clear all
                cleared_count += len(self.memory_cache)
                self.memory_cache.clear()
                self.stats.total_size_bytes = 0
            else:
                # Selective clear
                keys_to_remove = []
                for key, entry in self.memory_cache.items():
                    if ((entry_type is None or entry.entry_type == entry_type) and
                        (namespace is None or key.startswith(hashlib.sha256(namespace.encode()).hexdigest()[:8]))):
                        keys_to_remove.append(key)
                
                for key in keys_to_remove:
                    entry = self.memory_cache.pop(key)
                    self.stats.total_size_bytes = max(0, self.stats.total_size_bytes - entry.size_bytes)
                    cleared_count += 1
        
        # Clear disk cache
        if entry_type is None:
            cache_dirs = [self.session_cache_dir, self.api_cache_dir, self.data_cache_dir]
        else:
            cache_dirs = [self._get_disk_path("dummy", entry_type).parent]
        
        for cache_dir in cache_dirs:
            if cache_dir.exists():
                try:
                    for cache_file in cache_dir.glob("*.cache"):
                        cache_file.unlink()
                        cleared_count += 1
                except Exception as e:
                    logger.warning(f"Failed to clear disk cache directory {cache_dir}: {e}")
        
        logger.info(f"🗑️ Cleared {cleared_count} cache entries")
        return cleared_count
    
    async def cleanup_expired(self):
        """Clean up expired entries"""
        start_time = time.time()
        cleaned_count = 0
        
        # Clean memory cache
        with self.cache_lock:
            expired_keys = []
            for key, entry in self.memory_cache.items():
                if entry.is_expired():
                    expired_keys.append(key)
            
            for key in expired_keys:
                entry = self.memory_cache.pop(key)
                self.stats.total_size_bytes = max(0, self.stats.total_size_bytes - entry.size_bytes)
                cleaned_count += 1
        
        # Clean disk cache
        for cache_dir in [self.session_cache_dir, self.api_cache_dir, self.data_cache_dir]:
            if cache_dir.exists():
                for cache_file in cache_dir.glob("*.cache"):
                    try:
                        # Check file age
                        file_age = time.time() - cache_file.stat().st_mtime
                        if file_age > self.default_ttl:
                            cache_file.unlink()
                            cleaned_count += 1
                    except Exception as e:
                        logger.warning(f"Error checking cache file {cache_file}: {e}")
        
        cleanup_time = time.time() - start_time
        self.stats.expired_cleanups += cleaned_count
        
        if cleaned_count > 0:
            logger.info(f"🧹 Cleaned {cleaned_count} expired entries in {cleanup_time:.2f}s")
    
    def _update_average_access_time(self, access_time: float):
        """Update average access time statistics"""
        total_accesses = self.stats.hits + self.stats.misses
        if total_accesses == 1:
            self.stats.average_access_time = access_time
        else:
            # Rolling average
            self.stats.average_access_time = (
                (self.stats.average_access_time * (total_accesses - 1) + access_time) / total_accesses
            )
    
    async def start_background_cleanup(self):
        """Start background cleanup task"""
        if self.cleanup_task is None:
            self.cleanup_task = asyncio.create_task(self._background_cleanup_loop())
            logger.info("🔄 Started background cache cleanup")
    
    async def _background_cleanup_loop(self):
        """Background cleanup loop"""
        while not self._shutdown:
            try:
                await asyncio.sleep(self.cleanup_interval)
                await self.cleanup_expired()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Background cleanup error: {e}")
                await asyncio.sleep(60)  # Wait before retrying
    
    async def stop(self):
        """Stop cache and cleanup resources"""
        self._shutdown = True
        
        if self.cleanup_task:
            self.cleanup_task.cancel()
            try:
                await self.cleanup_task
            except asyncio.CancelledError:
                pass
        
        logger.info("🛑 Intelligent cache stopped")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        memory_size_mb = sum(entry.size_bytes for entry in self.memory_cache.values()) / (1024 * 1024)
        
        # Calculate disk usage
        disk_size_mb = 0
        for cache_dir in [self.session_cache_dir, self.api_cache_dir, self.data_cache_dir]:
            if cache_dir.exists():
                try:
                    disk_size_mb += sum(f.stat().st_size for f in cache_dir.glob("*.cache")) / (1024 * 1024)
                except:
                    pass
        
        return {
            **asdict(self.stats),
            'hit_rate_percent': round(self.stats.hit_rate(), 2),
            'memory_entries': len(self.memory_cache),
            'memory_size_mb': round(memory_size_mb, 2),
            'disk_size_mb': round(disk_size_mb, 2),
            'average_access_time_ms': round(self.stats.average_access_time * 1000, 2)
        }

# Global cache instance
_global_cache: Optional[IntelligentCache] = None

def get_cache(config: Dict[str, Any] = None) -> IntelligentCache:
    """Get global cache instance"""
    global _global_cache
    
    if _global_cache is None:
        _global_cache = IntelligentCache(config)
        logger.info("🧠 Created global intelligent cache")
    
    return _global_cache

async def main():
    """Test the intelligent cache"""
    config = {
        'max_memory_entries': 100,
        'max_memory_size_mb': 10,
        'default_ttl': 60,
        'cleanup_interval': 30
    }
    
    cache = IntelligentCache(config)
    await cache.start_background_cleanup()
    
    try:
        # Test different cache operations
        await cache.set("test", "key1", {"data": "test_value"}, CacheEntryType.API_RESPONSE)
        await cache.set("session", "user1", {"token": "abc123"}, CacheEntryType.SESSION_DATA, ttl=300)
        
        # Test retrieval
        value1 = await cache.get("test", "key1")
        value2 = await cache.get("session", "user1")
        
        print(f"Retrieved values: {value1}, {value2}")
        
        # Test cache stats
        stats = cache.get_stats()
        print(f"Cache stats: {json.dumps(stats, indent=2)}")
        
        # Test cleanup
        await cache.cleanup_expired()
        
    finally:
        await cache.stop()

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())