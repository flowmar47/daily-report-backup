#!/usr/bin/env python3
"""
Optimized Session Manager with performance improvements
Implements caching, lazy loading, and concurrent operations
"""

import os
import json
import asyncio
import aiofiles
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, Optional, Any, List
from concurrent.futures import ThreadPoolExecutor
import threading
import hashlib
import pickle
import lz4.frame
from functools import lru_cache
import time

from .secure_session_manager import SecureSessionManager


class OptimizedSessionManager(SecureSessionManager):
    """Enhanced session manager with performance optimizations"""
    
    def __init__(self, base_dir: str = "browser_sessions", 
                 cache_size: int = 100,
                 compression_level: int = 9):
        super().__init__(base_dir)
        
        # Performance settings
        self.cache_size = cache_size
        self.compression_level = compression_level
        
        # In-memory cache
        self._session_cache: Dict[str, Dict[str, Any]] = {}
        self._cache_timestamps: Dict[str, datetime] = {}
        self._cache_lock = threading.RLock()
        
        # Thread pool for concurrent operations
        self._executor = ThreadPoolExecutor(max_workers=4)
        
        # Lazy loading registry
        self._lazy_sessions: Dict[str, str] = {}
        self._scan_sessions()
        
        # Performance metrics
        self._metrics = {
            'cache_hits': 0,
            'cache_misses': 0,
            'load_times': [],
            'save_times': []
        }
    
    def _scan_sessions(self):
        """Scan directory for available sessions (lazy loading)"""
        session_dir = Path(self.base_dir)
        if session_dir.exists():
            for file in session_dir.glob("*.session"):
                session_name = file.stem
                self._lazy_sessions[session_name] = str(file)
    
    @lru_cache(maxsize=32)
    def _get_session_hash(self, session_data: str) -> str:
        """Generate hash for session data (cached)"""
        return hashlib.sha256(session_data.encode()).hexdigest()
    
    def _compress_data(self, data: bytes) -> bytes:
        """Compress data using LZ4 for better performance"""
        return lz4.frame.compress(data, compression_level=self.compression_level)
    
    def _decompress_data(self, data: bytes) -> bytes:
        """Decompress LZ4 data"""
        return lz4.frame.decompress(data)
    
    def save_session(self, session_name: str, session_data: Dict[str, Any], 
                     async_save: bool = True) -> bool:
        """
        Save session with performance optimizations
        
        Args:
            session_name: Name of the session
            session_data: Session data to save
            async_save: Whether to save asynchronously
        """
        start_time = time.time()
        
        try:
            # Update cache immediately
            with self._cache_lock:
                self._session_cache[session_name] = session_data.copy()
                self._cache_timestamps[session_name] = datetime.now()
                
                # Manage cache size
                if len(self._session_cache) > self.cache_size:
                    # Remove oldest cached item
                    oldest = min(self._cache_timestamps.items(), 
                               key=lambda x: x[1])[0]
                    del self._session_cache[oldest]
                    del self._cache_timestamps[oldest]
            
            # Prepare data
            serialized = pickle.dumps(session_data)
            compressed = self._compress_data(serialized)
            encrypted = self._encrypt_data(compressed)
            
            # Save function
            def _save():
                session_path = Path(self.base_dir) / f"{session_name}.session"
                session_path.write_bytes(encrypted)
                # Set secure permissions
                os.chmod(session_path, 0o600)
                # Update lazy registry
                self._lazy_sessions[session_name] = str(session_path)
            
            if async_save:
                # Asynchronous save
                self._executor.submit(_save)
            else:
                # Synchronous save
                _save()
            
            # Record metrics
            save_time = time.time() - start_time
            self._metrics['save_times'].append(save_time)
            if len(self._metrics['save_times']) > 100:
                self._metrics['save_times'].pop(0)
            
            return True
            
        except Exception as e:
            print(f"Error saving session: {e}")
            return False
    
    def load_session(self, session_name: str, 
                     use_cache: bool = True) -> Optional[Dict[str, Any]]:
        """
        Load session with caching and lazy loading
        
        Args:
            session_name: Name of the session
            use_cache: Whether to use cache
        """
        start_time = time.time()
        
        # Check cache first
        if use_cache:
            with self._cache_lock:
                if session_name in self._session_cache:
                    self._metrics['cache_hits'] += 1
                    # Check cache age (expire after 1 hour)
                    cache_age = datetime.now() - self._cache_timestamps[session_name]
                    if cache_age < timedelta(hours=1):
                        return self._session_cache[session_name].copy()
                    else:
                        # Expired cache
                        del self._session_cache[session_name]
                        del self._cache_timestamps[session_name]
        
        self._metrics['cache_misses'] += 1
        
        # Check if session exists (lazy loading)
        if session_name not in self._lazy_sessions:
            return None
        
        try:
            session_path = Path(self._lazy_sessions[session_name])
            if not session_path.exists():
                del self._lazy_sessions[session_name]
                return None
            
            # Load and decrypt
            encrypted = session_path.read_bytes()
            compressed = self._decrypt_data(encrypted)
            serialized = self._decompress_data(compressed)
            session_data = pickle.loads(serialized)
            
            # Update cache
            if use_cache:
                with self._cache_lock:
                    self._session_cache[session_name] = session_data.copy()
                    self._cache_timestamps[session_name] = datetime.now()
            
            # Record metrics
            load_time = time.time() - start_time
            self._metrics['load_times'].append(load_time)
            if len(self._metrics['load_times']) > 100:
                self._metrics['load_times'].pop(0)
            
            return session_data
            
        except Exception as e:
            print(f"Error loading session: {e}")
            return None
    
    async def load_session_async(self, session_name: str) -> Optional[Dict[str, Any]]:
        """Asynchronous session loading"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            self._executor, 
            self.load_session, 
            session_name
        )
    
    def batch_load_sessions(self, session_names: List[str]) -> Dict[str, Dict[str, Any]]:
        """Load multiple sessions concurrently"""
        futures = {
            name: self._executor.submit(self.load_session, name, False)
            for name in session_names
        }
        
        results = {}
        for name, future in futures.items():
            try:
                results[name] = future.result(timeout=5)
            except Exception as e:
                print(f"Error loading session {name}: {e}")
                results[name] = None
        
        return results
    
    def preload_recent_sessions(self, hours: int = 24):
        """Preload recently used sessions into cache"""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        
        for session_name, session_path in self._lazy_sessions.items():
            try:
                path = Path(session_path)
                if path.exists():
                    mtime = datetime.fromtimestamp(path.stat().st_mtime)
                    if mtime > cutoff_time:
                        # Load into cache
                        self.load_session(session_name, use_cache=True)
            except Exception:
                pass
    
    def optimize_cache(self):
        """Optimize cache by removing stale entries"""
        with self._cache_lock:
            current_time = datetime.now()
            stale_sessions = []
            
            for session_name, timestamp in self._cache_timestamps.items():
                age = current_time - timestamp
                if age > timedelta(hours=2):
                    stale_sessions.append(session_name)
            
            for session_name in stale_sessions:
                del self._session_cache[session_name]
                del self._cache_timestamps[session_name]
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get performance metrics"""
        metrics = self._metrics.copy()
        
        # Calculate averages
        if metrics['load_times']:
            metrics['avg_load_time'] = sum(metrics['load_times']) / len(metrics['load_times'])
        else:
            metrics['avg_load_time'] = 0
            
        if metrics['save_times']:
            metrics['avg_save_time'] = sum(metrics['save_times']) / len(metrics['save_times'])
        else:
            metrics['avg_save_time'] = 0
        
        # Cache statistics
        total_requests = metrics['cache_hits'] + metrics['cache_misses']
        if total_requests > 0:
            metrics['cache_hit_rate'] = metrics['cache_hits'] / total_requests
        else:
            metrics['cache_hit_rate'] = 0
        
        metrics['cache_size'] = len(self._session_cache)
        
        return metrics
    
    def cleanup_old_sessions(self, days: int = 7):
        """Remove sessions older than specified days"""
        cutoff_time = datetime.now() - timedelta(days=days)
        removed_count = 0
        
        for session_name, session_path in list(self._lazy_sessions.items()):
            try:
                path = Path(session_path)
                if path.exists():
                    mtime = datetime.fromtimestamp(path.stat().st_mtime)
                    if mtime < cutoff_time:
                        path.unlink()
                        del self._lazy_sessions[session_name]
                        # Remove from cache if present
                        with self._cache_lock:
                            self._session_cache.pop(session_name, None)
                            self._cache_timestamps.pop(session_name, None)
                        removed_count += 1
            except Exception as e:
                print(f"Error cleaning up session {session_name}: {e}")
        
        return removed_count
    
    def __del__(self):
        """Cleanup resources"""
        if hasattr(self, '_executor'):
            self._executor.shutdown(wait=False)


# Singleton instance for shared use
_optimized_manager = None
_manager_lock = threading.Lock()


def get_optimized_session_manager() -> OptimizedSessionManager:
    """Get singleton instance of optimized session manager"""
    global _optimized_manager
    
    if _optimized_manager is None:
        with _manager_lock:
            if _optimized_manager is None:
                _optimized_manager = OptimizedSessionManager()
                # Preload recent sessions on startup
                _optimized_manager.preload_recent_sessions()
    
    return _optimized_manager


# Example usage and performance testing
if __name__ == "__main__":
    import random
    import string
    
    # Initialize manager
    manager = OptimizedSessionManager()
    
    # Generate test data
    def generate_test_session():
        return {
            'cookies': [
                {'name': f'cookie_{i}', 'value': ''.join(random.choices(string.ascii_letters, k=32))}
                for i in range(10)
            ],
            'local_storage': {
                f'key_{i}': ''.join(random.choices(string.ascii_letters, k=100))
                for i in range(20)
            },
            'session_id': ''.join(random.choices(string.ascii_letters, k=16)),
            'timestamp': datetime.now().isoformat()
        }
    
    print("Running performance tests...")
    
    # Test 1: Save performance
    print("\n1. Testing save performance...")
    for i in range(10):
        session_data = generate_test_session()
        manager.save_session(f"test_session_{i}", session_data, async_save=False)
    
    # Test 2: Load performance (with cache)
    print("\n2. Testing load performance with cache...")
    for _ in range(3):
        for i in range(10):
            manager.load_session(f"test_session_{i}")
    
    # Test 3: Batch loading
    print("\n3. Testing batch load performance...")
    session_names = [f"test_session_{i}" for i in range(10)]
    results = manager.batch_load_sessions(session_names)
    
    # Display metrics
    print("\n4. Performance Metrics:")
    metrics = manager.get_performance_metrics()
    print(f"   Cache Hit Rate: {metrics['cache_hit_rate']:.2%}")
    print(f"   Average Load Time: {metrics['avg_load_time']*1000:.2f}ms")
    print(f"   Average Save Time: {metrics['avg_save_time']*1000:.2f}ms")
    print(f"   Cache Size: {metrics['cache_size']} sessions")
    
    # Cleanup
    for i in range(10):
        manager.delete_session(f"test_session_{i}")
    
    print("\nPerformance tests completed!")