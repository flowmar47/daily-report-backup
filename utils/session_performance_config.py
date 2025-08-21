#!/usr/bin/env python3
"""
Performance configuration for optimized session management
"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class SessionPerformanceConfig:
    """Configuration for session manager performance tuning"""
    
    # Cache settings
    cache_size: int = 100  # Maximum number of sessions in memory
    cache_ttl_hours: float = 1.0  # Cache time-to-live in hours
    
    # Compression settings
    compression_enabled: bool = True
    compression_level: int = 9  # LZ4 compression level (1-9)
    
    # Concurrency settings
    thread_pool_size: int = 4  # Number of worker threads
    async_operations: bool = True  # Enable async save/load
    
    # Preloading settings
    preload_on_startup: bool = True
    preload_hours: int = 24  # Preload sessions used in last N hours
    
    # Cleanup settings
    auto_cleanup_enabled: bool = True
    cleanup_days: int = 7  # Remove sessions older than N days
    cleanup_interval_hours: int = 24  # Run cleanup every N hours
    
    # Performance monitoring
    metrics_enabled: bool = True
    metrics_sample_size: int = 100  # Keep last N timing samples
    
    # Memory optimization
    lazy_loading: bool = True  # Don't load sessions until needed
    batch_size: int = 10  # Max sessions to load in batch
    
    @classmethod
    def high_performance(cls) -> 'SessionPerformanceConfig':
        """Configuration optimized for speed"""
        return cls(
            cache_size=200,
            cache_ttl_hours=2.0,
            compression_level=3,  # Faster compression
            thread_pool_size=8,
            preload_hours=48
        )
    
    @classmethod
    def low_memory(cls) -> 'SessionPerformanceConfig':
        """Configuration optimized for memory usage"""
        return cls(
            cache_size=50,
            cache_ttl_hours=0.5,
            compression_level=9,  # Maximum compression
            thread_pool_size=2,
            preload_on_startup=False,
            cleanup_days=3
        )
    
    @classmethod
    def balanced(cls) -> 'SessionPerformanceConfig':
        """Balanced configuration (default)"""
        return cls()


# Integration with existing scrapers
def configure_scraper_sessions(config: Optional[SessionPerformanceConfig] = None):
    """Configure session management for all scrapers"""
    if config is None:
        config = SessionPerformanceConfig.balanced()
    
    from .optimized_session_manager import get_optimized_session_manager
    
    manager = get_optimized_session_manager()
    
    # Apply configuration
    manager.cache_size = config.cache_size
    manager.compression_level = config.compression_level
    
    if config.preload_on_startup:
        manager.preload_recent_sessions(config.preload_hours)
    
    return manager