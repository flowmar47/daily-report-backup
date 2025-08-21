"""
Rate limiting for API calls
Manages different API rate limits and provides intelligent retry mechanisms
"""
import time
import logging
from functools import wraps
from typing import Dict, Optional, Callable, Any
from datetime import datetime, timedelta
import threading
from collections import defaultdict, deque

import backoff
import requests
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from src.core.config import settings
from .cache_manager import cache_manager

logger = logging.getLogger(__name__)

class RateLimitTracker:
    """Thread-safe rate limit tracking for different APIs"""
    
    def __init__(self):
        self.call_counts = defaultdict(lambda: defaultdict(int))
        self.call_times = defaultdict(lambda: defaultdict(deque))
        self.daily_resets = defaultdict(lambda: datetime.now().replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=1))
        self.lock = threading.Lock()
        
        # Initialize daily reset times
        tomorrow = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=1)
        for api in ['alpha_vantage', 'twelve_data', 'news_api']:
            self.daily_resets[api] = tomorrow
    
    def can_make_call(self, api_name: str, limit_type: str, limit: int, period_seconds: int) -> bool:
        """Check if we can make an API call within the rate limit"""
        with self.lock:
            now = datetime.now()
            
            # Reset daily counters if needed
            if limit_type == 'daily' and now >= self.daily_resets[api_name]:
                self.call_counts[api_name]['daily'] = 0
                self.daily_resets[api_name] = now.replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=1)
            
            # Clean old calls for minute/hour limits
            if limit_type in ['minute', 'hour']:
                cutoff_time = now - timedelta(seconds=period_seconds)
                call_queue = self.call_times[api_name][limit_type]
                while call_queue and call_queue[0] < cutoff_time:
                    call_queue.popleft()
                
                current_count = len(call_queue)
            else:
                current_count = self.call_counts[api_name][limit_type]
            
            return current_count < limit
    
    def record_call(self, api_name: str, limit_type: str):
        """Record that an API call was made"""
        with self.lock:
            now = datetime.now()
            
            if limit_type in ['minute', 'hour']:
                self.call_times[api_name][limit_type].append(now)
            else:
                self.call_counts[api_name][limit_type] += 1
    
    def get_usage_stats(self) -> Dict[str, Dict[str, int]]:
        """Get current usage statistics"""
        with self.lock:
            stats = {}
            for api_name in self.call_counts:
                stats[api_name] = dict(self.call_counts[api_name])
                
                # Add minute/hour counts
                for limit_type in ['minute', 'hour']:
                    if limit_type in self.call_times[api_name]:
                        stats[api_name][limit_type] = len(self.call_times[api_name][limit_type])
            
            return stats
    
    def time_until_reset(self, api_name: str, limit_type: str) -> Optional[int]:
        """Get seconds until the rate limit resets"""
        with self.lock:
            if limit_type == 'daily':
                return int((self.daily_resets[api_name] - datetime.now()).total_seconds())
            elif limit_type == 'minute':
                call_queue = self.call_times[api_name]['minute']
                if call_queue:
                    oldest_call = call_queue[0]
                    reset_time = oldest_call + timedelta(minutes=1)
                    return max(0, int((reset_time - datetime.now()).total_seconds()))
            elif limit_type == 'hour':
                call_queue = self.call_times[api_name]['hour']
                if call_queue:
                    oldest_call = call_queue[0]
                    reset_time = oldest_call + timedelta(hours=1)
                    return max(0, int((reset_time - datetime.now()).total_seconds()))
            
            return None

# Global rate limit tracker
rate_tracker = RateLimitTracker()

def rate_limited(api_name: str, calls_per_day: int = None, calls_per_minute: int = None, 
                calls_per_hour: int = None, priority: int = 1):
    """
    Decorator for rate limiting API calls
    
    Args:
        api_name: Name of the API
        calls_per_day: Daily call limit
        calls_per_minute: Per-minute call limit
        calls_per_hour: Per-hour call limit
        priority: Priority level (1=highest, 5=lowest)
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Check rate limits
            rate_limits = []
            if calls_per_day:
                rate_limits.append(('daily', calls_per_day, 86400))
            if calls_per_hour:
                rate_limits.append(('hour', calls_per_hour, 3600))
            if calls_per_minute:
                rate_limits.append(('minute', calls_per_minute, 60))
            
            # Check all rate limits
            for limit_type, limit, period in rate_limits:
                max_wait = 300  # 5 minutes max wait
                wait_time = 0
                
                while not rate_tracker.can_make_call(api_name, limit_type, limit, period):
                    if wait_time >= max_wait:
                        raise Exception(f"Rate limit exceeded for {api_name} ({limit_type}). Max wait time reached.")
                    
                    reset_time = rate_tracker.time_until_reset(api_name, limit_type)
                    sleep_time = min(reset_time or 60, 60)  # Wait up to 1 minute
                    
                    logger.warning(f"Rate limit hit for {api_name} ({limit_type}). Waiting {sleep_time}s")
                    time.sleep(sleep_time)
                    wait_time += sleep_time
            
            # Make the API call
            try:
                result = func(*args, **kwargs)
                
                # Record successful calls
                for limit_type, _, _ in rate_limits:
                    rate_tracker.record_call(api_name, limit_type)
                
                return result
                
            except Exception as e:
                logger.error(f"API call failed for {api_name}: {e}")
                raise
        
        return wrapper
    return decorator

# API-specific decorators
def alpha_vantage_rate_limit(priority: int = 1):
    """Rate limiter for Alpha Vantage API"""
    return rate_limited(
        api_name='alpha_vantage',
        calls_per_minute=settings.alpha_vantage_rate_limit,
        priority=priority
    )

def twelve_data_rate_limit(priority: int = 2):
    """Rate limiter for Twelve Data API"""
    return rate_limited(
        api_name='twelve_data',
        calls_per_minute=settings.twelve_data_rate_limit,
        priority=priority
    )

def fred_rate_limit(priority: int = 3):
    """Rate limiter for FRED API"""
    return rate_limited(
        api_name='fred',
        calls_per_minute=settings.fred_rate_limit,
        priority=priority
    )

def finnhub_rate_limit(priority: int = 2):
    """Rate limiter for Finnhub API"""
    return rate_limited(
        api_name='finnhub',
        calls_per_minute=settings.finnhub_rate_limit,
        priority=priority
    )

def news_api_rate_limit(priority: int = 3):
    """Rate limiter for News API"""
    return rate_limited(
        api_name='news_api',
        calls_per_minute=settings.news_api_rate_limit,
        priority=priority
    )

def reddit_rate_limit(priority: int = 4):
    """Rate limiter for Reddit API"""
    return rate_limited(
        api_name='reddit',
        calls_per_minute=60,  # Reddit API limit
        priority=priority
    )

class SmartAPIManager:
    """Intelligent API management with fallback strategies"""
    
    def __init__(self):
        self.api_health = defaultdict(lambda: {'status': 'healthy', 'last_check': datetime.now()})
        self.fallback_strategies = {
            'price_data': ['alpha_vantage', 'twelve_data'],
            'economic_data': ['fred'],
            'news_sentiment': ['news_api', 'reddit'],
            'forex_rates': ['alpha_vantage', 'twelve_data']
        }
    
    def get_available_api(self, data_type: str) -> Optional[str]:
        """Get the best available API for a data type"""
        apis = self.fallback_strategies.get(data_type, [])
        
        for api in apis:
            # Check if API is healthy and has capacity
            if self._is_api_available(api):
                return api
        
        return None
    
    def _is_api_available(self, api_name: str) -> bool:
        """Check if an API is available for use"""
        # Check health status
        health_info = self.api_health[api_name]
        if health_info['status'] != 'healthy':
            # Re-check health if it's been more than 10 minutes
            if datetime.now() - health_info['last_check'] > timedelta(minutes=10):
                self._check_api_health(api_name)
        
        if self.api_health[api_name]['status'] != 'healthy':
            return False
        
        # Check rate limits
        if api_name == 'alpha_vantage':
            return rate_tracker.can_make_call(api_name, 'daily', settings.alpha_vantage_rate_limit, 86400)
        elif api_name == 'twelve_data':
            return rate_tracker.can_make_call(api_name, 'daily', settings.twelve_data_rate_limit, 86400)
        elif api_name == 'fred':
            return rate_tracker.can_make_call(api_name, 'minute', settings.fred_rate_limit, 60)
        elif api_name == 'finnhub':
            return rate_tracker.can_make_call(api_name, 'minute', settings.finnhub_rate_limit, 60)
        elif api_name == 'news_api':
            return rate_tracker.can_make_call(api_name, 'daily', settings.news_api_rate_limit * 2, 86400)
        
        return True
    
    def _check_api_health(self, api_name: str):
        """Check if an API is responding"""
        try:
            if api_name == 'alpha_vantage':
                # Simple health check - get a basic quote
                url = f"https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol=EURUSD&apikey={settings.alpha_vantage_api_key}"
                response = requests.get(url, timeout=10)
                if response.status_code == 200:
                    self.api_health[api_name] = {'status': 'healthy', 'last_check': datetime.now()}
                else:
                    self.api_health[api_name] = {'status': 'unhealthy', 'last_check': datetime.now()}
            
            # Add health checks for other APIs as needed
            
        except Exception as e:
            logger.warning(f"Health check failed for {api_name}: {e}")
            self.api_health[api_name] = {'status': 'unhealthy', 'last_check': datetime.now()}
    
    def get_api_statistics(self) -> Dict[str, Any]:
        """Get comprehensive API usage statistics"""
        stats = {
            'rate_limits': rate_tracker.get_usage_stats(),
            'api_health': dict(self.api_health),
            'available_apis': {}
        }
        
        for data_type, apis in self.fallback_strategies.items():
            available = [api for api in apis if self._is_api_available(api)]
            stats['available_apis'][data_type] = available
        
        return stats

# Global API manager
api_manager = SmartAPIManager()

# Retry decorators for network issues
def robust_api_call(max_attempts: int = 3, base_delay: float = 1.0):
    """
    Decorator for robust API calls with exponential backoff
    """
    return retry(
        stop=stop_after_attempt(max_attempts),
        wait=wait_exponential(multiplier=base_delay, min=1, max=10),
        retry=retry_if_exception_type((requests.exceptions.RequestException, ConnectionError)),
        reraise=True
    )

@backoff.on_exception(
    backoff.expo,
    (requests.exceptions.RequestException, ConnectionError),
    max_tries=3,
    max_time=30
)
@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=30),
    retry=retry_if_exception_type((requests.exceptions.RequestException, requests.exceptions.Timeout))
)
def make_request_with_backoff(url: str, **kwargs) -> requests.Response:
    """Make HTTP request with automatic backoff on failures"""
    # Set default timeout if not provided
    kwargs.setdefault('timeout', 10)
    
    response = requests.get(url, **kwargs)
    
    # Raise exception for rate limiting and server errors to trigger retry
    if response.status_code == 429:  # Too Many Requests
        logger.warning(f"Rate limit hit for {url}, will retry with backoff")
        response.raise_for_status()
    elif response.status_code >= 500:  # Server errors
        logger.warning(f"Server error {response.status_code} for {url}, will retry")
        response.raise_for_status()
    
    return response

def cached_api_call(api_name: str, ttl: int = None):
    """
    Decorator that combines caching and rate limiting for API calls
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Generate cache key from function args
            cache_key = f"{api_name}:{func.__name__}:{hash(str(args) + str(sorted(kwargs.items())))}"
            
            # Try cache first
            cached_result = cache_manager.get(cache_key)
            if cached_result is not None:
                logger.debug(f"Cache hit for {api_name}:{func.__name__}")
                return cached_result
            
            # Make API call
            logger.debug(f"Cache miss for {api_name}:{func.__name__}, making API call")
            result = func(*args, **kwargs)
            
            # Cache the result
            cache_ttl = ttl or cache_manager._get_default_ttl(api_name)
            cache_manager.set(cache_key, result, cache_ttl)
            
            return result
        
        return wrapper
    return decorator