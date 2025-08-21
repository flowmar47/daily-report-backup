"""
Unified data fetching for all API sources
Handles Alpha Vantage, Twelve Data, FRED, Finnhub, News API, Reddit, and more
"""
import json
import logging
import pandas as pd
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union
import feedparser
from urllib.parse import urlencode

from src.core.config import settings
from .cache_manager import cache_manager, price_data_cache, economic_data_cache
from .rate_limiter import (
    alpha_vantage_rate_limit, twelve_data_rate_limit, fred_rate_limit,
    finnhub_rate_limit, news_api_rate_limit, reddit_rate_limit,
    make_request_with_backoff, api_manager
)

logger = logging.getLogger(__name__)

class DataFetcher:
    """Unified data fetching with intelligent API management"""
    
    def __init__(self):
        self.alpha_vantage_calls_today = 0
        self.twelve_data_calls_today = 0
        
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
                'symbol': symbol,
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
    
    def fetch_forex_data(self, pair: str, interval: str = '4hour') -> Optional[Dict]:
        """
        Intelligent forex data fetching with fallback strategy
        Supports multiple intervals: 30min, 1hour, 4hour, daily
        Prioritizes Alpha Vantage for 4H data, falls back to Twelve Data
        """
        # Convert pair format for different APIs
        if len(pair) == 6:  # e.g., EURUSD
            from_symbol = pair[:3]
            to_symbol = pair[3:]
        else:
            logger.error(f"Invalid currency pair format: {pair}")
            return None
        
        # Try Alpha Vantage first for 4H data
        if interval in ['4hour', '4h'] and api_manager._is_api_available('alpha_vantage'):
            logger.info(f"Fetching {pair} from Alpha Vantage")
            data = self.fetch_alpha_vantage_forex(from_symbol, to_symbol, '4hour')
            if data:
                return data
        
        # Fallback to Twelve Data with interval mapping
        if api_manager._is_api_available('twelve_data'):
            logger.info(f"Fetching {pair} ({interval}) from Twelve Data (fallback)")
            twelve_symbol = f"{from_symbol}/{to_symbol}"
            data = self.fetch_twelve_data_forex(twelve_symbol, interval)
            if data:
                return data
        
        logger.error(f"Failed to fetch forex data for {pair}")
        return None
    
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
        Get current exchange rate for a currency pair
        """
        # Try Alpha Vantage first
        if api_manager._is_api_available('alpha_vantage'):
            try:
                from_symbol = pair[:3]
                to_symbol = pair[3:]
                
                params = {
                    'function': 'CURRENCY_EXCHANGE_RATE',
                    'from_currency': from_symbol,
                    'to_currency': to_symbol,
                    'apikey': settings.alpha_vantage_api_key
                }
                
                url = f"https://www.alphavantage.co/query?{urlencode(params)}"
                response = make_request_with_backoff(url, timeout=15)
                
                if response.status_code == 200:
                    data = response.json()
                    
                    rate_key = 'Realtime Currency Exchange Rate'
                    if rate_key in data:
                        rate = data[rate_key]['5. Exchange Rate']
                        return float(rate)
                        
            except Exception as e:
                logger.error(f"Failed to get current price for {pair}: {e}")
        
        return None
    
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

# Global data fetcher instance
data_fetcher = DataFetcher()