"""Enhanced configuration management with validation and environment handling."""

import os
from typing import List, Optional, Dict, Any
from pathlib import Path
from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from .exceptions import InvalidConfigurationError, MissingConfigurationError


class Settings(BaseSettings):
    """Application settings with validation and environment variable support."""
    
    # Application Settings
    app_name: str = Field(default="forex-signal-generator", description="Application name")
    app_env: str = Field(default="development", description="Application environment")
    app_version: str = Field(default="1.0.0", description="Application version")
    
    # Logging Configuration
    log_dir: str = Field(default="logs", description="Log directory path")
    log_level: str = Field(default="INFO", description="Logging level")
    log_retention_days: int = Field(default=30, ge=1, le=365, description="Log retention in days")
    enable_json_logging: bool = Field(default=True, description="Enable JSON structured logging")
    
    # Redis Configuration
    redis_url: str = Field(default="redis://localhost:6379/0", description="Redis connection URL")
    redis_timeout: int = Field(default=5, ge=1, le=60, description="Redis timeout in seconds")
    redis_max_connections: int = Field(default=10, ge=1, le=100, description="Redis max connections")
    
    # Cache TTL Settings (in seconds)
    cache_ttl_price_data: int = Field(default=3600, ge=60, le=86400, description="Price data cache TTL")
    cache_ttl_economic_data: int = Field(default=14400, ge=300, le=86400, description="Economic data cache TTL")
    cache_ttl_news_data: int = Field(default=1800, ge=60, le=7200, description="News data cache TTL")
    cache_ttl_sentiment_data: int = Field(default=3600, ge=300, le=14400, description="Sentiment data cache TTL")
    
    # API Keys (required)
    alpha_vantage_api_key: str = Field(..., min_length=8, description="Alpha Vantage API key")
    twelve_data_api_key: str = Field(..., min_length=8, description="Twelve Data API key")
    fred_api_key: str = Field(..., min_length=8, description="FRED API key")
    finnhub_api_key: str = Field(..., min_length=8, description="Finnhub API key")
    news_api_key: str = Field(..., min_length=8, description="News API key")
    
    # Fallback API Keys (for enhanced data fetching)
    polygon_api_key: Optional[str] = Field(default=None, description="Polygon.io API key")
    marketstack_api_key: Optional[str] = Field(default=None, description="MarketStack API key")
    exchangerate_api_key: Optional[str] = Field(default=None, description="ExchangeRate-API key")
    fixer_api_key: Optional[str] = Field(default=None, description="Fixer.io API key")
    currency_api_key: Optional[str] = Field(default=None, description="CurrencyAPI key")
    freecurrency_api_key: Optional[str] = Field(default=None, description="FreeCurrencyAPI key")
    exchangerates_api_key: Optional[str] = Field(default=None, description="ExchangeRatesAPI key")
    
    # Optional API Keys (deprecated/unused)
    reddit_client_id: Optional[str] = Field(default=None, description="Reddit API client ID")
    reddit_client_secret: Optional[str] = Field(default=None, description="Reddit API client secret")
    twitter_bearer_token: Optional[str] = Field(default=None, description="Twitter API bearer token")
    
    # Rate Limits (requests per day/minute)
    alpha_vantage_rate_limit: int = Field(default=500, ge=1, le=10000, description="Alpha Vantage daily limit")
    twelve_data_rate_limit: int = Field(default=800, ge=1, le=10000, description="Twelve Data daily limit")
    fred_rate_limit: int = Field(default=120, ge=1, le=1000, description="FRED per minute limit")
    finnhub_rate_limit: int = Field(default=60, ge=1, le=1000, description="Finnhub per minute limit")
    news_api_rate_limit: int = Field(default=1000, ge=1, le=10000, description="News API daily limit")
    
    # Fallback API Rate Limits
    polygon_rate_limit: int = Field(default=5, ge=1, le=100, description="Polygon per minute limit")
    marketstack_rate_limit: int = Field(default=100, ge=1, le=1000, description="MarketStack per hour limit")
    exchangerate_rate_limit: int = Field(default=1000, ge=1, le=10000, description="ExchangeRate-API per month limit")
    fixer_rate_limit: int = Field(default=100, ge=1, le=1000, description="Fixer.io per month limit")
    currency_api_rate_limit: int = Field(default=300, ge=1, le=1000, description="CurrencyAPI per month limit")
    freecurrency_rate_limit: int = Field(default=5000, ge=1, le=10000, description="FreeCurrencyAPI per month limit")
    exchangerates_rate_limit: int = Field(default=1000, ge=1, le=10000, description="ExchangeRatesAPI per month limit")
    
    # Deprecated rate limits
    reddit_rate_limit: int = Field(default=60, ge=1, le=600, description="Reddit per minute limit")
    
    # Trading Signal Thresholds
    strong_signal_threshold: float = Field(default=0.7, ge=0.5, le=1.0, description="Strong signal threshold")
    medium_signal_threshold: float = Field(default=0.5, ge=0.3, le=0.8, description="Medium signal threshold")
    weak_signal_threshold: float = Field(default=0.3, ge=0.1, le=0.6, description="Weak signal threshold")
    
    # Risk Management
    max_stop_loss_pips: int = Field(default=100, ge=10, le=500, description="Maximum stop loss in pips")
    min_target_pips: int = Field(default=20, ge=5, le=200, description="Minimum target in pips")
    default_target_pips: int = Field(default=50, ge=10, le=500, description="Default target in pips")
    strong_signal_target_pips: int = Field(default=100, ge=50, le=300, description="Target pips for strong signals")
    medium_signal_target_pips: int = Field(default=75, ge=30, le=200, description="Target pips for medium signals")
    weak_signal_target_pips: int = Field(default=50, ge=20, le=150, description="Target pips for weak signals")
    risk_reward_ratio: float = Field(default=2.0, ge=1.0, le=5.0, description="Risk to reward ratio")
    max_daily_signals: int = Field(default=10, ge=1, le=50, description="Maximum signals per day")
    
    # Currency Pairs
    default_currency_pairs: List[str] = Field(
        default=[
            # Major Pairs (USD base/quote)
            "EURUSD", "GBPUSD", "USDJPY", "USDCHF", "AUDUSD", "USDCAD", "NZDUSD",
            # Cross Pairs (EUR base)
            "EURGBP", "EURJPY", "EURCHF", "EURAUD", "EURCAD", "EURNZD",
            # Cross Pairs (GBP base)
            "GBPJPY", "GBPCHF", "GBPAUD", "GBPCAD", "GBPNZD",
            # Cross Pairs (JPY quote)
            "CHFJPY", "AUDJPY", "CADJPY", "NZDJPY",
            # Other Cross Pairs
            "AUDCHF", "AUDCAD", "AUDNZD", "CADCHF", "NZDCHF", "NZDCAD"
        ],
        description="Default currency pairs to analyze - all major and cross pairs"
    )
    
    # Timeframes
    default_timeframes: List[str] = Field(
        default=["30min", "1hour", "4hour", "daily"],
        description="Default timeframes for analysis"
    )
    
    # Analysis Weights (sentiment analysis removed)
    technical_analysis_weight: float = Field(default=0.75, ge=0.0, le=1.0, description="Technical analysis weight")
    economic_analysis_weight: float = Field(default=0.20, ge=0.0, le=1.0, description="Economic analysis weight")
    sentiment_analysis_weight: float = Field(default=0.0, ge=0.0, le=0.0, description="Sentiment analysis weight (disabled)")
    geopolitical_analysis_weight: float = Field(default=0.05, ge=0.0, le=1.0, description="Geopolitical analysis weight")
    pattern_analysis_weight: float = Field(default=0.0, ge=0.0, le=0.0, description="Pattern analysis weight (included in technical)")
    
    # System Settings
    timezone: str = Field(default="UTC", description="System timezone")
    debug_mode: bool = Field(default=False, description="Enable debug mode")
    use_mock_data: bool = Field(default=False, description="Use mock data for testing")
    save_raw_responses: bool = Field(default=False, description="Save raw API responses")
    enable_backtesting: bool = Field(default=False, description="Enable backtesting features")
    
    # Performance Settings
    max_concurrent_requests: int = Field(default=5, ge=1, le=20, description="Max concurrent API requests")
    request_timeout: int = Field(default=30, ge=5, le=120, description="API request timeout in seconds")
    retry_attempts: int = Field(default=3, ge=1, le=10, description="Number of retry attempts")
    retry_delay: float = Field(default=1.0, ge=0.1, le=10.0, description="Retry delay in seconds")
    
    # File Paths
    data_dir: str = Field(default="data", description="Data directory path")
    reports_dir: str = Field(default="reports", description="Reports directory path")
    cache_dir: str = Field(default="cache", description="Cache directory path")
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        env_prefix="FOREX_",
        extra="ignore"
    )
    
    @field_validator('log_level')
    @classmethod
    def validate_log_level(cls, v):
        """Validate log level."""
        valid_levels = {'DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'}
        if v.upper() not in valid_levels:
            raise InvalidConfigurationError('log_level', f'must be one of {valid_levels}')
        return v.upper()
    
    @field_validator('app_env')
    @classmethod
    def validate_app_env(cls, v):
        """Validate application environment."""
        valid_envs = {'development', 'staging', 'production', 'testing'}
        if v.lower() not in valid_envs:
            raise InvalidConfigurationError('app_env', f'must be one of {valid_envs}')
        return v.lower()
    
    @field_validator('timezone')
    @classmethod
    def validate_timezone(cls, v):
        """Validate timezone."""
        try:
            import pytz
            pytz.timezone(v)
        except Exception:
            raise InvalidConfigurationError('timezone', 'must be a valid timezone')
        return v
    
    @field_validator('default_currency_pairs')
    @classmethod
    def validate_currency_pairs(cls, v):
        """Validate currency pairs format."""
        # Skip validation if validators module is not available (during import)
        try:
            from .validators import CurrencyPairValidator
            
            validated_pairs = []
            for pair in v:
                try:
                    validated_pairs.append(CurrencyPairValidator.validate_currency_pair(pair))
                except Exception as e:
                    raise InvalidConfigurationError('default_currency_pairs', f'invalid pair {pair}: {e}')
            
            return validated_pairs
        except ImportError:
            return v
    
    @field_validator('default_timeframes')
    @classmethod
    def validate_timeframes(cls, v):
        """Validate timeframes."""
        # Skip validation if validators module is not available (during import)
        try:
            from .validators import TimeframeValidator
            
            validated_timeframes = []
            for timeframe in v:
                try:
                    validated_timeframes.append(TimeframeValidator.validate_timeframe(timeframe))
                except Exception as e:
                    raise InvalidConfigurationError('default_timeframes', f'invalid timeframe {timeframe}: {e}')
            
            return validated_timeframes
        except ImportError:
            return v
    
    @model_validator(mode='after')
    def validate_analysis_weights(self):
        """Validate that analysis weights sum to 1.0."""
        total_weight = (
            self.technical_analysis_weight +
            self.economic_analysis_weight + 
            self.sentiment_analysis_weight +
            self.geopolitical_analysis_weight +
            self.pattern_analysis_weight
        )
        
        if abs(total_weight - 1.0) > 0.01:  # Allow small floating point errors
            raise InvalidConfigurationError(
                'analysis_weights', 
                f'weights must sum to 1.0, got {total_weight}'
            )
        
        return self
    
    @model_validator(mode='after')
    def validate_signal_thresholds(self):
        """Validate signal threshold ordering."""
        if not (self.weak_signal_threshold < self.medium_signal_threshold < self.strong_signal_threshold):
            raise InvalidConfigurationError(
                'signal_thresholds',
                'thresholds must be ordered: weak < medium < strong'
            )
        
        return self
    
    def create_directories(self) -> None:
        """Create necessary directories."""
        directories = [self.log_dir, self.data_dir, self.reports_dir, self.cache_dir]
        
        for directory in directories:
            Path(directory).mkdir(parents=True, exist_ok=True)
    
    def get_api_keys(self) -> Dict[str, str]:
        """Get all API keys as a dictionary."""
        return {
            'alpha_vantage': self.alpha_vantage_api_key,
            'twelve_data': self.twelve_data_api_key,
            'fred': self.fred_api_key,
            'finnhub': self.finnhub_api_key,
            'news_api': self.news_api_key,
            'polygon': self.polygon_api_key,
            'marketstack': self.marketstack_api_key,
            'exchangerate_api': self.exchangerate_api_key,
            'fixer': self.fixer_api_key,
            'currency_api': self.currency_api_key,
            'freecurrency': self.freecurrency_api_key,
            'exchangerates_api': self.exchangerates_api_key,
            'reddit_client_id': self.reddit_client_id,
            'reddit_client_secret': self.reddit_client_secret,
            'twitter_bearer_token': self.twitter_bearer_token
        }
    
    def get_rate_limits(self) -> Dict[str, int]:
        """Get all rate limits as a dictionary."""
        return {
            'alpha_vantage': self.alpha_vantage_rate_limit,
            'twelve_data': self.twelve_data_rate_limit,
            'fred': self.fred_rate_limit,
            'finnhub': self.finnhub_rate_limit,
            'news_api': self.news_api_rate_limit,
            'polygon': self.polygon_rate_limit,
            'marketstack': self.marketstack_rate_limit,
            'exchangerate_api': self.exchangerate_rate_limit,
            'fixer': self.fixer_rate_limit,
            'currency_api': self.currency_api_rate_limit,
            'freecurrency': self.freecurrency_rate_limit,
            'exchangerates_api': self.exchangerates_rate_limit,
            'reddit': self.reddit_rate_limit
        }
    
    def get_cache_ttls(self) -> Dict[str, int]:
        """Get all cache TTLs as a dictionary."""
        return {
            'price_data': self.cache_ttl_price_data,
            'economic_data': self.cache_ttl_economic_data,
            'news_data': self.cache_ttl_news_data,
            'sentiment_data': self.cache_ttl_sentiment_data
        }
    
    def get_analysis_weights(self) -> Dict[str, float]:
        """Get analysis weights as a dictionary."""
        return {
            'technical': self.technical_analysis_weight,
            'economic': self.economic_analysis_weight,
            'sentiment': self.sentiment_analysis_weight,
            'geopolitical': self.geopolitical_analysis_weight,
            'pattern': self.pattern_analysis_weight
        }
    
    def is_production(self) -> bool:
        """Check if running in production environment."""
        return self.app_env == 'production'
    
    def is_development(self) -> bool:
        """Check if running in development environment."""
        return self.app_env == 'development'


# Global settings instance
settings = Settings()

# Create necessary directories on import
settings.create_directories()