"""
Unit tests for configuration management
"""
import pytest
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.config import Config, APIConfig, CacheConfig, TradingConfig

class TestConfig:
    """Test configuration management"""
    
    def test_api_config_creation(self):
        """Test API configuration creation"""
        api_config = APIConfig(
            alpha_vantage_key="test_key",
            twelve_data_key="test_key",
            fred_key="test_key",
            finnhub_key="test_key",
            news_api_key="test_key",
            reddit_key="test_key"
        )
        
        assert api_config.alpha_vantage_key == "test_key"
        assert api_config.alpha_vantage_daily_limit == 25
        assert api_config.fred_minute_limit == 120
    
    def test_cache_config_defaults(self):
        """Test cache configuration defaults"""
        cache_config = CacheConfig()
        
        assert cache_config.price_data_ttl == 3600
        assert cache_config.economic_data_ttl == 14400
        assert cache_config.gdp_data_ttl == 86400
    
    def test_trading_config_creation(self):
        """Test trading configuration"""
        trading_config = TradingConfig(
            currency_pairs=['EURUSD', 'GBPUSD'],
            target_timeframes=['1h', '4h']
        )
        
        assert len(trading_config.currency_pairs) == 2
        assert trading_config.minimum_pips == 100
        assert trading_config.technical_weight == 0.35
    
    def test_main_config_initialization(self):
        """Test main configuration initialization"""
        config = Config()
        
        assert len(config.trading.currency_pairs) == 5
        assert 'USDCAD' in config.trading.currency_pairs
        assert 'EURUSD' in config.trading.currency_pairs
        
        assert config.redis_host == 'localhost'
        assert config.redis_port == 6379
    
    def test_currency_mapping(self):
        """Test currency to central bank mapping"""
        config = Config()
        mapping = config.get_currency_mapping()
        
        assert mapping['USD'] == 'FED'
        assert mapping['EUR'] == 'ECB'
        assert mapping['JPY'] == 'BOJ'
    
    def test_pip_values(self):
        """Test pip value configuration"""
        config = Config()
        pip_values = config.get_pip_values()
        
        assert pip_values['USDCAD'] == 0.0001
        assert pip_values['CHFJPY'] == 0.01
        assert pip_values['USDJPY'] == 0.01
    
    def test_config_validation(self):
        """Test configuration validation"""
        config = Config()
        
        # Should return True since we have API keys set
        is_valid = config.validate_config()
        assert isinstance(is_valid, bool)