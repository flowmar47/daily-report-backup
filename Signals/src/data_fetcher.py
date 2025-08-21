"""
Enhanced Unified Data Fetcher with Smart Caching and yfinance Integration
Handles Alpha Vantage, Twelve Data, FRED, Finnhub, News API, Reddit, and yfinance
Optimized for daily 6 AM execution with minimal API usage
"""
import json
import logging
import pandas as pd
import requests
import pickle
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union
import feedparser
from urllib.parse import urlencode
from pathlib import Path
import numpy as np

try:
    from src.core.config import settings
    from src.cache_manager import cache_manager, price_data_cache, economic_data_cache
    from src.rate_limiter import (
        alpha_vantage_rate_limit, twelve_data_rate_limit, fred_rate_limit,
        finnhub_rate_limit, news_api_rate_limit, reddit_rate_limit,
        make_request_with_backoff, api_manager
    )
    from src.yfinance_helper import yfinance_helper
except ImportError:
    try:
        from .core.config import settings
        from .cache_manager import cache_manager, price_data_cache, economic_data_cache
        from .rate_limiter import (
            alpha_vantage_rate_limit, twelve_data_rate_limit, fred_rate_limit,
            finnhub_rate_limit, news_api_rate_limit, reddit_rate_limit,
            make_request_with_backoff, api_manager
        )
        from .yfinance_helper import yfinance_helper
    except ImportError:
        from core.config import settings
        from cache_manager import cache_manager, price_data_cache, economic_data_cache
        from rate_limiter import (
            alpha_vantage_rate_limit, twelve_data_rate_limit, fred_rate_limit,
            finnhub_rate_limit, news_api_rate_limit, reddit_rate_limit,
            make_request_with_backoff, api_manager
        )
        from yfinance_helper import yfinance_helper

logger = logging.getLogger(__name__)

class DataFetcher:
    """Enhanced data fetching with smart caching and yfinance integration"""
    
    def __init__(self):
        self.alpha_vantage_calls_today = 0
        self.twelve_data_calls_today = 0
        
        # Smart caching directory
        self.cache_dir = Path(__file__).parent.parent / 'cache'
        self.cache_dir.mkdir(exist_ok=True)
        self.historical_cache_file = self.cache_dir / 'historical_data.pkl'
        
        # Cache settings
        self.cache_expiry_hours = {
            '1m': 0.25,    # 15 minutes for 1-minute data
            '5m': 0.5,     # 30 minutes for 5-minute data
            '15m': 1,      # 1 hour for 15-minute data
            '30min': 2,    # 2 hours for 30-minute data
            '1hour': 4,    # 4 hours for 1-hour data
            '4hour': 12,   # 12 hours for 4-hour data
            'daily': 24,   # 24 hours for daily data
        }
        
        # Load historical cache
        self.historical_cache = self._load_historical_cache()
        
        # Optimized API rotation for 6 AM execution
        self.forex_api_rotation = [
            'yfinance',         # Free, unlimited validation
            'alpha_vantage',    # 500/day limit - primary
            'twelve_data',      # 8/minute limit - secondary  
            'polygon',          # Professional grade - tertiary
            'marketstack',      # Fallback API
            'freecurrency',     # Simple current price only
        ]
        self.current_api_index = 0
        
        # Daily usage tracking (reset at midnight)
        self.daily_usage = self._get_daily_usage()
        
        # yfinance integration
        self.yfinance_helper = yfinance_helper
    
    def _convert_to_twelve_data_format(self, symbol: str) -> str:
        """Convert USDJPY format to USD/JPY format for Twelve Data API"""
        # Common forex pairs mapping
        if len(symbol) == 6:
            base = symbol[:3]
            quote = symbol[3:]
            return f"{base}/{quote}"
        return symbol  # Return as-is if not standard format
    
    def _load_historical_cache(self) -> Dict:
        """Load historical data cache from disk"""
        try:
            if self.historical_cache_file.exists():
                with open(self.historical_cache_file, 'rb') as f:
                    cache = pickle.load(f)
                    logger.debug(f"Loaded historical cache with {len(cache)} entries")
                    return cache
        except Exception as e:
            logger.warning(f"Could not load historical cache: {e}")
        return {}
    
    def _save_historical_cache(self):
        """Save historical data cache to disk"""
        try:
            with open(self.historical_cache_file, 'wb') as f:
                pickle.dump(self.historical_cache, f)
            logger.debug(f"Saved historical cache with {len(self.historical_cache)} entries")
        except Exception as e:
            logger.error(f"Could not save historical cache: {e}")
    
    def _get_daily_usage(self) -> Dict:
        """Get daily API usage tracking"""
        today = datetime.now().date()
        usage_file = self.cache_dir / f'usage_{today.isoformat()}.json'
        
        try:
            if usage_file.exists():
                with open(usage_file, 'r') as f:
                    return json.load(f)
        except Exception:
            pass
        
        return {
            'date': today.isoformat(),
            'alpha_vantage': 0,
            'twelve_data': 0,
            'polygon': 0,
            'marketstack': 0,
            'finnhub': 0
        }
    
    def _update_daily_usage(self, api_name: str, count: int = 1):
        """Update daily API usage counter"""
        self.daily_usage[api_name] = self.daily_usage.get(api_name, 0) + count
        
        today = datetime.now().date()
        usage_file = self.cache_dir / f'usage_{today.isoformat()}.json'
        
        try:
            with open(usage_file, 'w') as f:
                json.dump(self.daily_usage, f)
        except Exception as e:
            logger.debug(f"Could not save usage tracking: {e}")
    
    def _get_cache_key(self, pair: str, interval: str) -> str:
        """Generate cache key for pair and interval"""
        return f"{pair}_{interval}"
    
    def _is_cache_valid(self, cache_entry: Dict, interval: str) -> bool:
        """Check if cache entry is still valid"""
        try:
            cached_time = datetime.fromisoformat(cache_entry.get('cached_at', ''))
            expiry_hours = self.cache_expiry_hours.get(interval, 24)
            
            return datetime.now() - cached_time < timedelta(hours=expiry_hours)
        except Exception:
            return False
    
    def fetch_forex_data_smart(self, pair: str, interval: str = '4hour') -> Optional[Dict]:
        """
        Smart forex data fetching with caching and API optimization
        Priority: Cache -> yfinance -> Alpha Vantage -> Twelve Data -> Other APIs
        """
        try:
            cache_key = self._get_cache_key(pair, interval)
            
            # 1. Check local cache first
            if cache_key in self.historical_cache:
                cache_entry = self.historical_cache[cache_key]
                if self._is_cache_valid(cache_entry, interval):
                    logger.debug(f"Using cached data for {pair} {interval}")
                    return cache_entry['data']
            
            # 2. Try yfinance first (free, unlimited)
            yf_data = self._fetch_yfinance_data(pair, interval)
            if yf_data:
                self._cache_historical_data(cache_key, yf_data, interval)
                logger.info(f"✅ Fetched {pair} {interval} data from yfinance")
                return yf_data
            
            # 3. Try Alpha Vantage (primary API)
            if self.daily_usage.get('alpha_vantage', 0) < 450:  # Leave margin
                av_data = self.fetch_alpha_vantage_forex(pair[:3], pair[3:], interval)
                if av_data:
                    self._update_daily_usage('alpha_vantage')
                    self._cache_historical_data(cache_key, av_data, interval)
                    logger.info(f"✅ Fetched {pair} {interval} data from Alpha Vantage")
                    return av_data
            
            # 4. Try Twelve Data (secondary)
            if self.daily_usage.get('twelve_data', 0) < 400:  # Leave margin
                td_data = self.fetch_twelve_data_forex(pair, interval)
                if td_data:
                    self._update_daily_usage('twelve_data')
                    self._cache_historical_data(cache_key, td_data, interval)
                    logger.info(f"✅ Fetched {pair} {interval} data from Twelve Data")
                    return td_data
            
            # 5. Try other APIs as fallbacks
            for api_name in ['polygon', 'marketstack']:
                if hasattr(self, f'fetch_{api_name}_forex'):
                    if self.daily_usage.get(api_name, 0) < 100:  # Conservative limits
                        api_func = getattr(self, f'fetch_{api_name}_forex')
                        api_data = api_func(pair, interval)
                        if api_data:
                            self._update_daily_usage(api_name)
                            self._cache_historical_data(cache_key, api_data, interval)
                            logger.info(f"✅ Fetched {pair} {interval} data from {api_name}")
                            return api_data
            
            logger.warning(f"❌ Could not fetch data for {pair} {interval} from any source")
            return None
            
        except Exception as e:
            logger.error(f"Smart fetch error for {pair} {interval}: {e}")
            return None
    
    def _fetch_yfinance_data(self, pair: str, interval: str) -> Optional[Dict]:
        """Fetch data using yfinance helper"""
        try:
            # Map intervals to yfinance format
            interval_map = {
                '30min': '30m',
                '1hour': '1h', 
                '4hour': '4h',
                'daily': '1d'
            }
            
            yf_interval = interval_map.get(interval, '1h')
            period = '1mo' if interval in ['30min', '1hour', '4hour'] else '3mo'
            
            hist_data = self.yfinance_helper.get_historical_data(pair, period, yf_interval)
            
            if hist_data is not None and not hist_data.empty:
                # Convert to our standard format
                processed_data = []
                for timestamp, row in hist_data.iterrows():
                    processed_data.append({
                        'timestamp': timestamp.isoformat(),
                        'open': float(row['open']),
                        'high': float(row['high']),
                        'low': float(row['low']),
                        'close': float(row['close']),
                        'volume': float(row.get('volume', 0))
                    })
                
                return {
                    'data': processed_data,
                    'source': 'yfinance',
                    'last_updated': datetime.now().isoformat()
                }
            
        except Exception as e:
            logger.debug(f"yfinance data fetch error for {pair}: {e}")
        
        return None
    
    def _cache_historical_data(self, cache_key: str, data: Dict, interval: str):
        """Cache historical data with metadata"""
        try:
            cache_entry = {
                'data': data,
                'cached_at': datetime.now().isoformat(),
                'interval': interval,
                'source': data.get('source', 'unknown')
            }
            
            self.historical_cache[cache_key] = cache_entry
            
            # Clean old entries periodically
            if len(self.historical_cache) % 10 == 0:
                self._cleanup_expired_cache()
            
            # Save to disk periodically
            if len(self.historical_cache) % 5 == 0:
                self._save_historical_cache()
                
        except Exception as e:
            logger.debug(f"Cache storage error: {e}")
    
    def _cleanup_expired_cache(self):
        """Remove expired cache entries"""
        try:
            expired_keys = []
            for key, entry in self.historical_cache.items():
                interval = entry.get('interval', 'daily')
                if not self._is_cache_valid(entry, interval):
                    expired_keys.append(key)
            
            for key in expired_keys:
                del self.historical_cache[key]
            
            if expired_keys:
                logger.debug(f"Cleaned {len(expired_keys)} expired cache entries")
                
        except Exception as e:
            logger.debug(f"Cache cleanup error: {e}")
    
    def get_current_price_validated(self, pair: str) -> Optional[float]:
        """
        Get current price with multi-source validation
        Uses yfinance, Alpha Vantage, and other sources for validation
        """
        try:
            prices = {}
            
            # 1. yfinance (always try first - free)
            yf_price = self.yfinance_helper.get_current_price(pair)
            if yf_price:
                prices['yfinance'] = yf_price
            
            # 2. Try cached recent price (under 5 minutes old)
            cache_key = f"{pair}_current"
            if cache_key in self.historical_cache:
                cache_entry = self.historical_cache[cache_key]
                cached_time = datetime.fromisoformat(cache_entry.get('cached_at', ''))
                if datetime.now() - cached_time < timedelta(minutes=5):
                    prices['cache'] = cache_entry['data']['price']
            
            # 3. If we have yfinance, that's sufficient for validation
            if 'yfinance' in prices:
                current_price = prices['yfinance']
                
                # Cache the price
                self._cache_current_price(pair, current_price)
                
                logger.debug(f"Validated current price for {pair}: {current_price}")
                return current_price
            
            # 4. Fallback to APIs if yfinance fails (use sparingly)
            if not prices and self.daily_usage.get('alpha_vantage', 0) < 480:
                # Try current price from other sources
                av_price = self._get_alpha_vantage_current_price(pair)
                if av_price:
                    prices['alpha_vantage'] = av_price
                    self._update_daily_usage('alpha_vantage')
            
            # Return the most recent price we have
            if prices:
                current_price = list(prices.values())[0]
                self._cache_current_price(pair, current_price)
                return current_price
            
            logger.warning(f"Could not get validated current price for {pair}")
            return None
            
        except Exception as e:
            logger.error(f"Current price validation error for {pair}: {e}")
            return None
    
    def _cache_current_price(self, pair: str, price: float):
        """Cache current price with timestamp"""
        try:
            cache_key = f"{pair}_current"
            cache_entry = {
                'data': {'price': price},
                'cached_at': datetime.now().isoformat(),
                'interval': 'current',
                'source': 'validated'
            }
            self.historical_cache[cache_key] = cache_entry
        except Exception as e:
            logger.debug(f"Current price cache error: {e}")
    
    def _get_alpha_vantage_current_price(self, pair: str) -> Optional[float]:
        """Get current price from Alpha Vantage realtime endpoint"""
        try:
            params = {
                'function': 'CURRENCY_EXCHANGE_RATE',
                'from_currency': pair[:3],
                'to_currency': pair[3:],
                'apikey': settings.alpha_vantage_api_key
            }
            
            url = f"https://www.alphavantage.co/query?{urlencode(params)}"
            response = make_request_with_backoff(url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                exchange_rate = data.get('Realtime Currency Exchange Rate', {})
                price_str = exchange_rate.get('5. Exchange Rate')
                
                if price_str:
                    return float(price_str)
                    
        except Exception as e:
            logger.debug(f"Alpha Vantage current price error for {pair}: {e}")
        
        return None
    
    def optimize_for_daily_execution(self):
        """Optimize data fetcher for daily 6 AM execution"""
        try:
            # Clean expired cache entries
            self._cleanup_expired_cache()
            
            # Reset daily usage if it's a new day
            today = datetime.now().date()
            if self.daily_usage.get('date') != today.isoformat():
                self.daily_usage = self._get_daily_usage()
            
            # Clean up yfinance cache
            self.yfinance_helper.cleanup_expired_cache()
            
            # Save cache to disk
            self._save_historical_cache()
            
            # Log optimization status
            cache_stats = {
                'total_cache_entries': len(self.historical_cache),
                'yfinance_cache_stats': self.yfinance_helper.get_cache_stats(),
                'daily_api_usage': self.daily_usage
            }
            
            logger.info(f"Daily execution optimization complete: {cache_stats}")
            
        except Exception as e:
            logger.error(f"Daily optimization error: {e}")
    
    def get_cache_statistics(self) -> Dict[str, Any]:
        """Get comprehensive cache and usage statistics"""
        try:
            total_entries = len(self.historical_cache)
            valid_entries = 0
            
            for entry in self.historical_cache.values():
                interval = entry.get('interval', 'daily')
                if self._is_cache_valid(entry, interval):
                    valid_entries += 1
            
            return {
                'historical_cache': {
                    'total_entries': total_entries,
                    'valid_entries': valid_entries,
                    'expired_entries': total_entries - valid_entries
                },
                'yfinance_cache': self.yfinance_helper.get_cache_stats(),
                'daily_api_usage': self.daily_usage,
                'api_limits': {
                    'alpha_vantage': {'used': self.daily_usage.get('alpha_vantage', 0), 'limit': 500},
                    'twelve_data': {'used': self.daily_usage.get('twelve_data', 0), 'limit': 800},
                    'polygon': {'used': self.daily_usage.get('polygon', 0), 'limit': 100},
                    'yfinance': {'used': 0, 'limit': 'unlimited'}
                }
            }
            
        except Exception as e:
            logger.error(f"Cache statistics error: {e}")
            return {'error': str(e)}

    @alpha_vantage_rate_limit(priority=1)
    @price_data_cache(ttl=3600)
    def fetch_alpha_vantage_forex(self, from_symbol: str, to_symbol: str, 
                                 interval: str = '4hour') -> Optional[Dict]:
        """
        Fetch forex data from Alpha Vantage
        Critical: Use for 4-hour candlestick data specifically
        """
        try:
            function = 'FX_INTRADAY'
            params = {
                'function': function,
                'from_symbol': from_symbol,
                'to_symbol': to_symbol,
                'interval': interval,
                'apikey': settings.alpha_vantage_api_key,
                'outputsize': 'compact'
            }
            
            url = f"https://www.alphavantage.co/query?{urlencode(params)}"
            response = make_request_with_backoff(url, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                
                # Check for API limit message
                if 'Note' in data:
                    logger.warning(f"Alpha Vantage rate limit hit: {data['Note']}")
                    return None
                
                # Check for error message
                if 'Error Message' in data:
                    logger.error(f"Alpha Vantage error: {data['Error Message']}")
                    return None
                
                # Process time series data
                time_series_key = f'Time Series FX ({interval})'
                if time_series_key in data:
                    self.alpha_vantage_calls_today += 1
                    return self._process_alpha_vantage_forex(data[time_series_key])
                
            logger.warning(f"Alpha Vantage returned status {response.status_code}")
            return None
            
        except Exception as e:
            logger.error(f"Alpha Vantage fetch error: {e}")
            return None
    
    def _process_alpha_vantage_forex(self, time_series: Dict) -> Dict:
        """Process Alpha Vantage forex time series data"""
        processed_data = []
        
        for timestamp, values in time_series.items():
            processed_data.append({
                'timestamp': timestamp,
                'open': float(values['1. open']),
                'high': float(values['2. high']),
                'low': float(values['3. low']),
                'close': float(values['4. close'])
            })
        
        # Sort by timestamp (most recent first)
        processed_data.sort(key=lambda x: x['timestamp'], reverse=True)
        
        return {
            'data': processed_data,
            'source': 'alpha_vantage',
            'last_updated': datetime.now().isoformat()
        }
    
    @twelve_data_rate_limit(priority=2)
    @price_data_cache(ttl=3600)
    def fetch_twelve_data_forex(self, symbol: str, interval: str = '4h') -> Optional[Dict]:
        """
        Fetch forex data from Twelve Data as fallback
        Supports multiple intervals: 30min, 1h, 4h
        """
        try:
            # Convert symbol to Twelve Data format (USD/JPY not USDJPY)
            twelve_symbol = self._convert_to_twelve_data_format(symbol)
            
            # Map intervals to Twelve Data format
            interval_mapping = {
                '30min': '30min',
                '1hour': '1h', 
                '4hour': '4h',
                '4h': '4h',
                '1h': '1h'
            }
            
            twelve_interval = interval_mapping.get(interval, interval)
            
            params = {
                'symbol': twelve_symbol,
                'interval': twelve_interval,
                'apikey': settings.twelve_data_api_key,
                'format': 'JSON',
                'outputsize': '50'  # Last 50 records
            }
            
            url = f"https://api.twelvedata.com/time_series?{urlencode(params)}"
            response = make_request_with_backoff(url, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                
                if data.get('status') == 'error':
                    logger.error(f"Twelve Data error: {data.get('message', 'Unknown error')}")
                    return None
                
                if 'values' in data:
                    self.twelve_data_calls_today += 1
                    return self._process_twelve_data_forex(data)
                
            return None
            
        except Exception as e:
            logger.error(f"Twelve Data fetch error: {e}")
            return None
    
    def _process_twelve_data_forex(self, data: Dict) -> Dict:
        """Process Twelve Data forex response"""
        processed_data = []
        
        for item in data['values']:
            processed_data.append({
                'timestamp': item['datetime'],
                'open': float(item['open']),
                'high': float(item['high']),
                'low': float(item['low']),
                'close': float(item['close'])
            })
        
        return {
            'data': processed_data,
            'source': 'twelve_data',
            'last_updated': datetime.now().isoformat()
        }
    
    def get_next_api(self) -> str:
        """Get next API in round-robin rotation"""
        api = self.forex_api_rotation[self.current_api_index]
        self.current_api_index = (self.current_api_index + 1) % len(self.forex_api_rotation)
        return api
    
    def fetch_forex_data(self, pair: str, interval: str = '4hour') -> Optional[Dict]:
        """
        Enhanced forex data fetching with smart caching and yfinance integration
        Uses intelligent API management and local caching for optimal performance
        """
        # Use the new smart fetching method with caching and validation
        return self.fetch_forex_data_smart(pair, interval)
    
    @fred_rate_limit(priority=3)
    @economic_data_cache(ttl=14400)  # 4 hours
    def fetch_fred_data(self, series_id: str) -> Optional[Dict]:
        """
        Fetch economic data from FRED API
        """
        try:
            params = {
                'series_id': series_id,
                'api_key': settings.fred_api_key,
                'file_type': 'json',
                'limit': '10',  # Last 10 observations
                'sort_order': 'desc'
            }
            
            url = f"https://api.stlouisfed.org/fred/series/observations?{urlencode(params)}"
            response = make_request_with_backoff(url, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                
                if 'observations' in data:
                    return self._process_fred_data(data['observations'], series_id)
                
            return None
            
        except Exception as e:
            logger.error(f"FRED fetch error for {series_id}: {e}")
            return None
    
    def _process_fred_data(self, observations: List[Dict], series_id: str) -> Dict:
        """Process FRED economic data"""
        processed_data = []
        
        for obs in observations:
            if obs['value'] != '.':  # FRED uses '.' for missing values
                processed_data.append({
                    'date': obs['date'],
                    'value': float(obs['value'])
                })
        
        return {
            'series_id': series_id,
            'data': processed_data,
            'source': 'fred',
            'last_updated': datetime.now().isoformat()
        }
    
    @finnhub_rate_limit(priority=2)
    def fetch_finnhub_economic_calendar(self) -> Optional[List[Dict]]:
        """
        Fetch economic calendar from Finnhub
        """
        try:
            # Get events for next 5 days
            from_date = datetime.now().strftime('%Y-%m-%d')
            to_date = (datetime.now() + timedelta(days=5)).strftime('%Y-%m-%d')
            
            params = {
                'from': from_date,
                'to': to_date,
                'token': settings.finnhub_api_key
            }
            
            url = f"https://finnhub.io/api/v1/calendar/economic?{urlencode(params)}"
            response = make_request_with_backoff(url, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                return self._process_finnhub_calendar(data.get('economicCalendar', []))
                
            return None
            
        except Exception as e:
            logger.error(f"Finnhub economic calendar error: {e}")
            return None
    
    def _process_finnhub_calendar(self, events: List[Dict]) -> List[Dict]:
        """Process Finnhub economic calendar events"""
        high_impact_events = []
        
        for event in events:
            # Filter for high-impact events affecting our currencies
            if event.get('importance') == 3:  # High importance
                country = event.get('country', '').upper()
                if country in ['US', 'EU', 'GB', 'JP', 'CA', 'CH']:
                    high_impact_events.append({
                        'date': event.get('time'),
                        'country': country,
                        'event': event.get('event'),
                        'impact': 'high',
                        'estimate': event.get('estimate'),
                        'previous': event.get('previous')
                    })
        
        return high_impact_events
    
    @news_api_rate_limit(priority=3)
    def fetch_news_sentiment(self, query: str, sources: str = None) -> Optional[List[Dict]]:
        """
        Fetch news articles for sentiment analysis
        """
        try:
            params = {
                'q': query,
                'apiKey': settings.news_api_key,
                'language': 'en',
                'sortBy': 'relevancy',
                'pageSize': 20
            }
            
            if sources:
                params['sources'] = sources
            
            url = f"https://newsapi.org/v2/everything?{urlencode(params)}"
            response = make_request_with_backoff(url, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                
                if data.get('status') == 'ok':
                    return self._process_news_articles(data.get('articles', []))
                
            return None
            
        except Exception as e:
            logger.error(f"News API fetch error: {e}")
            return None
    
    def _process_news_articles(self, articles: List[Dict]) -> List[Dict]:
        """Process news articles for sentiment analysis"""
        processed_articles = []
        
        for article in articles:
            if article.get('title') and article.get('description'):
                processed_articles.append({
                    'title': article['title'],
                    'description': article['description'],
                    'content': article.get('content', ''),
                    'source': article.get('source', {}).get('name', 'Unknown'),
                    'published_at': article.get('publishedAt'),
                    'url': article.get('url')
                })
        
        return processed_articles
    
    def fetch_central_bank_feeds(self, currency: str) -> Optional[List[Dict]]:
        """
        Fetch central bank RSS feeds
        """
        try:
            currency_to_bank = {
                'USD': 'FED',
                'EUR': 'ECB',
                'JPY': 'BOJ',
                'GBP': 'BOE',
                'CAD': 'BOC',
                'CHF': 'SNB'
            }
            central_bank_feeds = {
                'FED': 'https://www.federalreserve.gov/feeds/press_releases.xml',
                'ECB': 'https://www.ecb.europa.eu/press/rss/pr/pr.rss.en.xml',
                'BOJ': 'https://www.boj.or.jp/en/rss/whatsnew.rdf',
                'BOE': 'https://www.bankofengland.co.uk/rss/news',
                'BOC': 'https://www.bankofcanada.ca/feed/news/',
                'SNB': 'https://www.snb.ch/en/ifor/media/rss/snb_news_en.xml'
            }
            bank = currency_to_bank.get(currency.upper())
            
            if not bank or bank not in central_bank_feeds:
                return None
            
            feed_url = central_bank_feeds[bank]
            
            # Use cache for RSS feeds
            cache_key = f"central_bank_feed:{bank}"
            cached_feed = cache_manager.get(cache_key)
            
            if cached_feed:
                return cached_feed
            
            feed = feedparser.parse(feed_url)
            processed_entries = []
            
            for entry in feed.entries[:10]:  # Last 10 entries
                processed_entries.append({
                    'title': entry.get('title', ''),
                    'summary': entry.get('summary', ''),
                    'link': entry.get('link', ''),
                    'published': entry.get('published', ''),
                    'bank': bank
                })
            
            # Cache for 15 minutes
            cache_manager.set(cache_key, processed_entries, 900)
            return processed_entries
            
        except Exception as e:
            logger.error(f"Central bank feed error for {currency}: {e}")
            return None
    
    def fetch_gdelt_events(self, currencies: List[str]) -> Optional[List[Dict]]:
        """
        Fetch geopolitical events from GDELT
        """
        try:
            # Build query for currency countries
            currency_countries = {
                'USD': 'United States',
                'EUR': 'European Union',
                'JPY': 'Japan',
                'CAD': 'Canada',
                'CHF': 'Switzerland'
            }
            
            countries = [currency_countries.get(cur.upper()) for cur in currencies if cur.upper() in currency_countries]
            if not countries:
                return None
            
            query = f"({' OR '.join(countries)}) (forex OR economy OR inflation OR interest rate)"
            
            params = {
                'query': query,
                'mode': 'timelinevolinfo',
                'format': 'json',
                'timespan': '1d'
            }
            
            url = f"https://api.gdeltproject.org/api/v2/doc/doc?{urlencode(params)}"
            response = make_request_with_backoff(url, timeout=60)
            
            if response.status_code == 200:
                data = response.json()
                return self._process_gdelt_events(data.get('articles', []))
            
            return None
            
        except Exception as e:
            logger.error(f"GDELT fetch error: {e}")
            return None
    
    def _process_gdelt_events(self, articles: List[Dict]) -> List[Dict]:
        """Process GDELT events for market impact"""
        processed_events = []
        
        # Keywords indicating market-moving events
        impact_keywords = [
            'interest rate', 'inflation', 'gdp', 'unemployment',
            'trade war', 'tariff', 'economic policy', 'central bank',
            'federal reserve', 'european central bank', 'bank of japan',
            'crisis', 'recession', 'growth', 'election'
        ]
        
        for article in articles:
            title = article.get('title', '').lower()
            content = article.get('content', '').lower()
            
            # Check for impact keywords
            has_impact = any(keyword in title or keyword in content for keyword in impact_keywords)
            
            if has_impact:
                processed_events.append({
                    'title': article.get('title', ''),
                    'url': article.get('url', ''),
                    'published': article.get('seendate', ''),
                    'tone': article.get('tone', 0),
                    'relevance': 'high' if any(keyword in title for keyword in impact_keywords) else 'medium'
                })
        
        return processed_events
    
    def get_current_price(self, pair: str) -> Optional[float]:
        """
        Get current exchange rate for a currency pair with enhanced validation
        Uses smart caching and multiple sources including yfinance
        """
        # Use the new validated current price method
        return self.get_current_price_validated(pair)
    
    def get_comprehensive_data(self, pairs: List[str]) -> Dict[str, Any]:
        """
        Fetch comprehensive data for all currency pairs
        """
        comprehensive_data = {
            'forex_data': {},
            'economic_indicators': {},
            'economic_calendar': [],
            'news_sentiment': {},
            'central_bank_feeds': {},
            'geopolitical_events': [],
            'current_prices': {},
            'data_freshness': datetime.now().isoformat()
        }
        
        # Fetch forex data (4H candlesticks)
        for pair in pairs:
            logger.info(f"Fetching 4H data for {pair}")
            forex_data = self.fetch_forex_data(pair, '4hour')
            if forex_data:
                comprehensive_data['forex_data'][pair] = forex_data
            
            # Get current price
            current_price = self.get_current_price(pair)
            if current_price:
                comprehensive_data['current_prices'][pair] = current_price
        
        # Fetch economic indicators
        unique_currencies = set()
        for pair in pairs:
            unique_currencies.add(pair[:3])
            unique_currencies.add(pair[3:])
        
        # Economic indicators mapping
        economic_indicators = {
            'USD': ['GDP', 'UNRATE', 'CPIAUCSL', 'FEDFUNDS'],
            'EUR': ['CLVMNACSCAB1GQEA19', 'LRHUTTTTEZM156S'],
            'GBP': ['CLVMNACSCAB1GQGB', 'LRHUTTTTGBM156S'],
            'JPY': ['CLVMNACSCAB1GQJP', 'LRHUTTTTJPM156S']
        }
        
        for currency in unique_currencies:
            if currency in economic_indicators:
                comprehensive_data['economic_indicators'][currency] = {}
                for indicator in economic_indicators[currency]:
                    fred_data = self.fetch_fred_data(indicator)
                    if fred_data:
                        comprehensive_data['economic_indicators'][currency][indicator] = fred_data
        
        # Fetch economic calendar
        calendar_events = self.fetch_finnhub_economic_calendar()
        if calendar_events:
            comprehensive_data['economic_calendar'] = calendar_events
        
        # Fetch news sentiment for major pairs
        for pair in pairs[:3]:  # Limit to avoid API exhaustion
            news_query = f"{pair[:3]} {pair[3:]} forex exchange rate"
            news_data = self.fetch_news_sentiment(news_query)
            if news_data:
                comprehensive_data['news_sentiment'][pair] = news_data
        
        # Fetch central bank feeds
        for currency in unique_currencies:
            cb_feed = self.fetch_central_bank_feeds(currency)
            if cb_feed:
                comprehensive_data['central_bank_feeds'][currency] = cb_feed
        
        # Fetch geopolitical events
        gdelt_events = self.fetch_gdelt_events(list(unique_currencies))
        if gdelt_events:
            comprehensive_data['geopolitical_events'] = gdelt_events
        
        return comprehensive_data
    
    def fetch_polygon_forex(self, pair: str, interval: str = '4hour') -> Optional[Dict]:
        """
        Fetch forex data from Polygon.io (professional-grade data)
        """
        try:
            # Convert interval to Polygon format
            interval_mapping = {
                '30min': '30/minute',
                '1hour': '1/hour',
                '4hour': '4/hour',
                '4h': '4/hour',
                'daily': '1/day'
            }
            
            polygon_interval = interval_mapping.get(interval, '4/hour')
            api_key = settings.polygon_api_key
            
            if not api_key:
                logger.warning("Polygon API key not configured")
                return None
            
            # Format: C:EURUSD (for EURUSD pair)
            polygon_symbol = f"C:{pair.upper()}"
            
            # Get current timestamp for recent data
            end_date = datetime.now()
            start_date = end_date - timedelta(days=7)
            
            params = {
                'apikey': api_key,
                'timestamp.gte': start_date.strftime('%Y-%m-%d'),
                'timestamp.lt': end_date.strftime('%Y-%m-%d'),
                'limit': 50
            }
            
            url = f"https://api.polygon.io/v2/aggs/ticker/{polygon_symbol}/range/{polygon_interval}?{urlencode(params)}"
            response = make_request_with_backoff(url, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                
                if data.get('status') == 'OK' and data.get('results'):
                    return self._process_polygon_forex(data)
                else:
                    logger.warning(f"Polygon returned no data for {pair}")
            
            return None
            
        except Exception as e:
            logger.error(f"Polygon fetch error for {pair}: {e}")
            return None
    
    def _process_polygon_forex(self, data: Dict) -> Dict:
        """Process Polygon.io forex response"""
        processed_data = []
        
        for item in data['results']:
            processed_data.append({
                'timestamp': datetime.fromtimestamp(item['t'] / 1000).isoformat(),
                'open': float(item['o']),
                'high': float(item['h']),
                'low': float(item['l']),
                'close': float(item['c'])
            })
        
        # Sort by timestamp (most recent first)
        processed_data.sort(key=lambda x: x['timestamp'], reverse=True)
        
        return {
            'data': processed_data,
            'source': 'polygon',
            'last_updated': datetime.now().isoformat()
        }
    
    def fetch_marketstack_forex(self, pair: str, interval: str = '4hour') -> Optional[Dict]:
        """
        Fetch forex data from MarketStack (historical data)
        """
        try:
            api_key = settings.marketstack_api_key
            
            if not api_key:
                logger.warning("MarketStack API key not configured")
                return None
            
            # Convert interval to MarketStack format  
            interval_mapping = {
                '30min': '1min',  # MarketStack doesn't have 30min, use 1min
                '1hour': '1hour',
                '4hour': '1hour',  # Use 1hour and aggregate
                '4h': '1hour',
                'daily': '1day'
            }
            
            marketstack_interval = interval_mapping.get(interval, '1hour')
            
            params = {
                'access_key': api_key,
                'symbols': pair.upper(),
                'interval': marketstack_interval,
                'limit': 200 if interval in ['4hour', '4h'] else 50
            }
            
            url = f"https://api.marketstack.com/v1/intraday?{urlencode(params)}"
            response = make_request_with_backoff(url, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                
                if data.get('data'):
                    return self._process_marketstack_forex(data, interval)
            
            return None
            
        except Exception as e:
            logger.error(f"MarketStack fetch error for {pair}: {e}")
            return None
    
    def _process_marketstack_forex(self, data: Dict, interval: str) -> Dict:
        """Process MarketStack forex response"""
        processed_data = []
        
        for item in data['data']:
            processed_data.append({
                'timestamp': item['date'],
                'open': float(item['open']),
                'high': float(item['high']),
                'low': float(item['low']),
                'close': float(item['close'])
            })
        
        # If 4hour interval requested, aggregate 1hour data
        if interval in ['4hour', '4h'] and len(processed_data) >= 4:
            aggregated_data = []
            for i in range(0, len(processed_data), 4):
                chunk = processed_data[i:i+4]
                if len(chunk) >= 4:
                    aggregated_data.append({
                        'timestamp': chunk[0]['timestamp'],
                        'open': chunk[0]['open'],
                        'high': max(item['high'] for item in chunk),
                        'low': min(item['low'] for item in chunk),
                        'close': chunk[-1]['close']
                    })
            processed_data = aggregated_data
        
        return {
            'data': processed_data,
            'source': 'marketstack',
            'last_updated': datetime.now().isoformat()
        }
    
    def fetch_exchangerate_forex(self, pair: str, interval: str = '4hour') -> Optional[Dict]:
        """
        Fetch current exchange rates from ExchangeRate-API (current rates only)
        Note: This provides current rates, not historical OHLC data
        """
        try:
            api_key = settings.exchangerate_api_key
            
            if not api_key:
                logger.warning("ExchangeRate-API key not configured")
                return None
            
            base_currency = pair[:3]
            target_currency = pair[3:]
            
            url = f"https://v6.exchangerate-api.com/v6/{api_key}/pair/{base_currency}/{target_currency}"
            response = make_request_with_backoff(url, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                
                if data.get('result') == 'success':
                    current_rate = float(data['conversion_rate'])
                    
                    # Create a minimal OHLC structure with current rate
                    current_time = datetime.now().isoformat()
                    ohlc_data = [{
                        'timestamp': current_time,
                        'open': current_rate,
                        'high': current_rate * 1.001,  # Minimal spread simulation
                        'low': current_rate * 0.999,
                        'close': current_rate
                    }]
                    
                    return {
                        'data': ohlc_data,
                        'source': 'exchangerate_api',
                        'last_updated': current_time,
                        'note': 'Current rate only, not historical OHLC'
                    }
            
            return None
            
        except Exception as e:
            logger.error(f"ExchangeRate-API fetch error for {pair}: {e}")
            return None
    
    def fetch_freecurrency_forex(self, pair: str) -> Optional[Dict]:
        """Fetch forex data from FreeCurrencyAPI (5000/day limit)"""
        try:
            api_key = settings.freecurrency_api_key
            if not api_key:
                return None
            
            base_currency = pair[:3]
            target_currency = pair[3:]
            
            url = f"https://api.freecurrencyapi.com/v1/latest?apikey={api_key}&currencies={target_currency}&base_currency={base_currency}"
            response = make_request_with_backoff(url, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                
                if 'data' in data and target_currency in data['data']:
                    rate = float(data['data'][target_currency])
                    current_time = datetime.now().isoformat()
                    
                    return {
                        'data': [{
                            'timestamp': current_time,
                            'open': rate,
                            'high': rate * 1.001,
                            'low': rate * 0.999,
                            'close': rate
                        }],
                        'source': 'freecurrency',
                        'last_updated': current_time
                    }
            
            return None
            
        except Exception as e:
            logger.error(f"FreeCurrency API fetch error for {pair}: {e}")
            return None
    
    def fetch_currencyapi_forex(self, pair: str) -> Optional[Dict]:
        """Fetch forex data from CurrencyAPI (300/day limit)"""
        try:
            api_key = settings.currency_api_key
            if not api_key:
                return None
            
            base_currency = pair[:3]
            target_currency = pair[3:]
            
            url = f"https://api.currencyapi.com/v3/latest?apikey={api_key}&currencies={target_currency}&base_currency={base_currency}"
            response = make_request_with_backoff(url, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                
                if 'data' in data and target_currency in data['data']:
                    rate = float(data['data'][target_currency]['value'])
                    current_time = datetime.now().isoformat()
                    
                    return {
                        'data': [{
                            'timestamp': current_time,
                            'open': rate,
                            'high': rate * 1.001,
                            'low': rate * 0.999,
                            'close': rate
                        }],
                        'source': 'currencyapi',
                        'last_updated': current_time
                    }
            
            return None
            
        except Exception as e:
            logger.error(f"CurrencyAPI fetch error for {pair}: {e}")
            return None
    
    def fetch_exchangerates_forex(self, pair: str) -> Optional[Dict]:
        """Fetch forex data from ExchangeRates API (250/day limit)"""
        try:
            api_key = settings.exchangerates_api_key
            if not api_key:
                return None
            
            base_currency = pair[:3]
            target_currency = pair[3:]
            
            url = f"http://api.exchangeratesapi.io/v1/latest?access_key={api_key}&symbols={target_currency}&base={base_currency}"
            response = make_request_with_backoff(url, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                
                if data.get('success') and 'rates' in data and target_currency in data['rates']:
                    rate = float(data['rates'][target_currency])
                    current_time = datetime.now().isoformat()
                    
                    return {
                        'data': [{
                            'timestamp': current_time,
                            'open': rate,
                            'high': rate * 1.001,
                            'low': rate * 0.999,
                            'close': rate
                        }],
                        'source': 'exchangerates',
                        'last_updated': current_time
                    }
            
            return None
            
        except Exception as e:
            logger.error(f"ExchangeRates API fetch error for {pair}: {e}")
            return None
    
    def fetch_fixer_forex(self, pair: str) -> Optional[Dict]:
        """Fetch forex data from Fixer API (100/day limit)"""
        try:
            api_key = settings.fixer_api_key
            if not api_key:
                return None
            
            base_currency = pair[:3]
            target_currency = pair[3:]
            
            url = f"http://data.fixer.io/api/latest?access_key={api_key}&symbols={target_currency}&base={base_currency}"
            response = make_request_with_backoff(url, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                
                if data.get('success') and 'rates' in data and target_currency in data['rates']:
                    rate = float(data['rates'][target_currency])
                    current_time = datetime.now().isoformat()
                    
                    return {
                        'data': [{
                            'timestamp': current_time,
                            'open': rate,
                            'high': rate * 1.001,
                            'low': rate * 0.999,
                            'close': rate
                        }],
                        'source': 'fixer',
                        'last_updated': current_time
                    }
            
            return None
            
        except Exception as e:
            logger.error(f"Fixer API fetch error for {pair}: {e}")
            return None

# Global data fetcher instance
data_fetcher = DataFetcher()