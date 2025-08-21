"""
Unit tests for data fetching functionality
"""
import pytest
import json
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.data_fetcher import DataFetcher, data_fetcher

class TestDataFetcher:
    """Test data fetching functionality"""
    
    def setup_method(self):
        """Setup test environment"""
        self.fetcher = DataFetcher()
    
    def test_initialization(self):
        """Test DataFetcher initialization"""
        assert self.fetcher.alpha_vantage_calls_today == 0
        assert self.fetcher.twelve_data_calls_today == 0
    
    @patch('src.data_fetcher.make_request_with_backoff')
    def test_fetch_alpha_vantage_forex_success(self, mock_request):
        """Test successful Alpha Vantage forex data fetch"""
        # Mock successful response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'Time Series FX (4hour)': {
                '2024-01-01 16:00:00': {
                    '1. open': '1.1000',
                    '2. high': '1.1050',
                    '3. low': '1.0950',
                    '4. close': '1.1025'
                },
                '2024-01-01 12:00:00': {
                    '1. open': '1.0975',
                    '2. high': '1.1000',
                    '3. low': '1.0925',
                    '4. close': '1.0995'
                }
            }
        }
        mock_request.return_value = mock_response
        
        result = self.fetcher.fetch_alpha_vantage_forex('EUR', 'USD', '4hour')
        
        assert result is not None
        assert result['source'] == 'alpha_vantage'
        assert len(result['data']) == 2
        assert result['data'][0]['close'] == 1.1025
        assert self.fetcher.alpha_vantage_calls_today == 1
    
    @patch('src.data_fetcher.make_request_with_backoff')
    def test_fetch_alpha_vantage_rate_limit(self, mock_request):
        """Test Alpha Vantage rate limit handling"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'Note': 'Thank you for using Alpha Vantage! Please visit https://www.alphavantage.co/premium/ if you would like to target a higher API call frequency.'
        }
        mock_request.return_value = mock_response
        
        result = self.fetcher.fetch_alpha_vantage_forex('EUR', 'USD', '4hour')
        
        assert result is None
    
    @patch('src.data_fetcher.make_request_with_backoff')
    def test_fetch_twelve_data_forex_success(self, mock_request):
        """Test successful Twelve Data forex fetch"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'meta': {'symbol': 'EUR/USD'},
            'values': [
                {
                    'datetime': '2024-01-01 16:00:00',
                    'open': '1.1000',
                    'high': '1.1050',
                    'low': '1.0950',
                    'close': '1.1025'
                }
            ]
        }
        mock_request.return_value = mock_response
        
        result = self.fetcher.fetch_twelve_data_forex('EUR/USD', '4h')
        
        assert result is not None
        assert result['source'] == 'twelve_data'
        assert len(result['data']) == 1
        assert result['data'][0]['close'] == 1.1025
    
    @patch('src.data_fetcher.make_request_with_backoff')
    def test_fetch_fred_data_success(self, mock_request):
        """Test successful FRED data fetch"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'observations': [
                {'date': '2024-01-01', 'value': '5.25'},
                {'date': '2023-12-01', 'value': '5.00'}
            ]
        }
        mock_request.return_value = mock_response
        
        result = self.fetcher.fetch_fred_data('DFF')
        
        assert result is not None
        assert result['series_id'] == 'DFF'
        assert len(result['data']) == 2
        assert result['data'][0]['value'] == 5.25
    
    @patch('src.data_fetcher.make_request_with_backoff')
    def test_fetch_finnhub_economic_calendar(self, mock_request):
        """Test Finnhub economic calendar fetch"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'economicCalendar': [
                {
                    'time': '2024-01-01T14:00:00Z',
                    'country': 'US',
                    'event': 'Non-Farm Payrolls',
                    'importance': 3,
                    'estimate': '200K',
                    'previous': '190K'
                },
                {
                    'time': '2024-01-01T15:00:00Z',
                    'country': 'EU',
                    'event': 'GDP Growth',
                    'importance': 2,
                    'estimate': '0.5%',
                    'previous': '0.3%'
                }
            ]
        }
        mock_request.return_value = mock_response
        
        result = self.fetcher.fetch_finnhub_economic_calendar()
        
        assert result is not None
        assert len(result) == 1  # Only high importance events
        assert result[0]['event'] == 'Non-Farm Payrolls'
        assert result[0]['impact'] == 'high'
    
    @patch('src.data_fetcher.make_request_with_backoff')
    def test_fetch_news_sentiment_success(self, mock_request):
        """Test successful news sentiment fetch"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'status': 'ok',
            'articles': [
                {
                    'title': 'USD Strengthens Against EUR',
                    'description': 'Dollar gains amid Fed policy expectations',
                    'content': 'Full article content here...',
                    'source': {'name': 'Reuters'},
                    'publishedAt': '2024-01-01T10:00:00Z',
                    'url': 'https://example.com/article1'
                }
            ]
        }
        mock_request.return_value = mock_response
        
        result = self.fetcher.fetch_news_sentiment('USD EUR forex')
        
        assert result is not None
        assert len(result) == 1
        assert result[0]['title'] == 'USD Strengthens Against EUR'
        assert result[0]['source'] == 'Reuters'
    
    @patch('feedparser.parse')
    def test_fetch_central_bank_feeds(self, mock_feedparser):
        """Test central bank RSS feed parsing"""
        mock_entry = Mock()
        mock_entry.get.side_effect = lambda key, default='': {
            'title': 'Fed Announces Interest Rate Decision',
            'summary': 'Federal Reserve maintains current rates',
            'link': 'https://fed.gov/announcement',
            'published': '2024-01-01T14:00:00Z'
        }.get(key, default)
        
        mock_feed = Mock()
        mock_feed.entries = [mock_entry]
        mock_feedparser.return_value = mock_feed
        
        result = self.fetcher.fetch_central_bank_feeds('USD')
        
        assert result is not None
        assert len(result) == 1
        assert result[0]['title'] == 'Fed Announces Interest Rate Decision'
        assert result[0]['bank'] == 'FED'
    
    @patch('src.data_fetcher.make_request_with_backoff')
    def test_fetch_gdelt_events(self, mock_request):
        """Test GDELT geopolitical events fetch"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'articles': [
                {
                    'title': 'Federal Reserve Policy Impact on Markets',
                    'url': 'https://example.com/article',
                    'seendate': '2024-01-01T12:00:00Z',
                    'tone': 2.5
                },
                {
                    'title': 'Sports News - Not Relevant',
                    'url': 'https://example.com/sports',
                    'seendate': '2024-01-01T11:00:00Z',
                    'tone': 0.0
                }
            ]
        }
        mock_request.return_value = mock_response
        
        result = self.fetcher.fetch_gdelt_events(['USD', 'EUR'])
        
        assert result is not None
        assert len(result) == 1  # Only market-relevant events
        assert 'Federal Reserve' in result[0]['title']
    
    @patch('src.data_fetcher.make_request_with_backoff')
    def test_get_current_price(self, mock_request):
        """Test current exchange rate fetch"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'Realtime Currency Exchange Rate': {
                '5. Exchange Rate': '1.1025'
            }
        }
        mock_request.return_value = mock_response
        
        result = self.fetcher.get_current_price('EURUSD')
        
        assert result == 1.1025
    
    def test_process_alpha_vantage_forex(self):
        """Test Alpha Vantage data processing"""
        time_series = {
            '2024-01-01 16:00:00': {
                '1. open': '1.1000',
                '2. high': '1.1050',
                '3. low': '1.0950',
                '4. close': '1.1025'
            },
            '2024-01-01 12:00:00': {
                '1. open': '1.0975',
                '2. high': '1.1000',
                '3. low': '1.0925',
                '4. close': '1.0995'
            }
        }
        
        result = self.fetcher._process_alpha_vantage_forex(time_series)
        
        assert len(result['data']) == 2
        # Should be sorted with most recent first
        assert result['data'][0]['timestamp'] == '2024-01-01 16:00:00'
        assert result['data'][0]['close'] == 1.1025
    
    def test_process_fred_data(self):
        """Test FRED data processing"""
        observations = [
            {'date': '2024-01-01', 'value': '5.25'},
            {'date': '2023-12-01', 'value': '.'},  # Missing value
            {'date': '2023-11-01', 'value': '5.00'}
        ]
        
        result = self.fetcher._process_fred_data(observations, 'DFF')
        
        assert result['series_id'] == 'DFF'
        assert len(result['data']) == 2  # Missing value filtered out
        assert result['data'][0]['value'] == 5.25
    
    @patch.object(DataFetcher, 'fetch_alpha_vantage_forex')
    @patch.object(DataFetcher, 'fetch_twelve_data_forex')
    @patch('src.data_fetcher.api_manager')
    def test_fetch_forex_data_fallback(self, mock_api_manager, mock_twelve, mock_alpha):
        """Test forex data fetch with fallback logic"""
        # Alpha Vantage unavailable, Twelve Data available
        mock_api_manager._is_api_available.side_effect = [False, True]
        mock_twelve.return_value = {'data': 'twelve_data_result'}
        
        result = self.fetcher.fetch_forex_data('EURUSD', '4hour')
        
        assert result == {'data': 'twelve_data_result'}
        mock_twelve.assert_called_once_with('EUR/USD', '4hour')
        mock_alpha.assert_not_called()
    
    @patch.object(DataFetcher, 'fetch_forex_data')
    @patch.object(DataFetcher, 'fetch_fred_data')
    @patch.object(DataFetcher, 'get_current_price')
    def test_get_comprehensive_data(self, mock_price, mock_fred, mock_forex):
        """Test comprehensive data collection"""
        # Mock successful data fetches
        mock_forex.return_value = {'data': 'forex_data'}
        mock_fred.return_value = {'data': 'fred_data'}
        mock_price.return_value = 1.1025
        
        pairs = ['EURUSD', 'GBPUSD']
        result = self.fetcher.get_comprehensive_data(pairs)
        
        assert 'forex_data' in result
        assert 'economic_indicators' in result
        assert 'current_prices' in result
        assert 'data_freshness' in result
        
        # Should fetch forex data for all pairs
        assert mock_forex.call_count == len(pairs)
        
        # Should fetch current prices for all pairs
        assert mock_price.call_count == len(pairs)

class TestDataFetcherIntegration:
    """Integration tests for data fetcher"""
    
    def test_invalid_currency_pair_format(self):
        """Test handling of invalid currency pair format"""
        fetcher = DataFetcher()
        result = fetcher.fetch_forex_data('INVALID', '4hour')
        assert result is None
    
    def test_fetch_central_bank_feeds_invalid_currency(self):
        """Test central bank feed fetch with invalid currency"""
        fetcher = DataFetcher()
        result = fetcher.fetch_central_bank_feeds('XXX')
        assert result is None
    
    @patch('src.data_fetcher.make_request_with_backoff')
    def test_api_error_handling(self, mock_request):
        """Test API error handling"""
        # Mock network error
        mock_request.side_effect = Exception("Network error")
        
        fetcher = DataFetcher()
        result = fetcher.fetch_alpha_vantage_forex('EUR', 'USD', '4hour')
        
        assert result is None
    
    def test_empty_gdelt_events_processing(self):
        """Test GDELT events processing with no relevant events"""
        fetcher = DataFetcher()
        articles = [
            {
                'title': 'Sports News',
                'url': 'https://example.com/sports',
                'seendate': '2024-01-01T12:00:00Z',
                'tone': 0.0
            }
        ]
        
        result = fetcher._process_gdelt_events(articles)
        
        assert result == []  # No market-relevant events
    
    def test_finnhub_calendar_filtering(self):
        """Test Finnhub calendar event filtering"""
        fetcher = DataFetcher()
        events = [
            {
                'time': '2024-01-01T14:00:00Z',
                'country': 'US',
                'event': 'High Impact Event',
                'importance': 3,
                'estimate': '200K',
                'previous': '190K'
            },
            {
                'time': '2024-01-01T15:00:00Z',
                'country': 'FR',  # Not in our currency list
                'event': 'Low Impact Event',
                'importance': 1,
                'estimate': '0.5%',
                'previous': '0.3%'
            }
        ]
        
        result = fetcher._process_finnhub_calendar(events)
        
        assert len(result) == 1
        assert result[0]['country'] == 'US'
        assert result[0]['impact'] == 'high'

class TestGlobalDataFetcher:
    """Test global data fetcher instance"""
    
    def test_global_instance_exists(self):
        """Test that global data fetcher instance exists"""
        assert data_fetcher is not None
        assert isinstance(data_fetcher, DataFetcher)
    
    def test_global_instance_initialization(self):
        """Test global instance is properly initialized"""
        assert data_fetcher.alpha_vantage_calls_today == 0
        assert data_fetcher.twelve_data_calls_today == 0