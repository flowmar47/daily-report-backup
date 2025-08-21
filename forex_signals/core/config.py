"""
Centralized configuration management for forex signals system
Consolidates all settings with Pydantic validation and environment support
"""

import os
from pathlib import Path
from typing import List, Optional, Dict, Any
from functools import lru_cache

from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from .exceptions import ConfigurationError


class Settings(BaseSettings):
    """
    Centralized application settings with validation
    All configuration is loaded from environment variables with sensible defaults
    """
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )
    
    # Application Settings
    app_name: str = Field(default="forex-signals", description="Application name")
    app_env: str = Field(default="production", description="Application environment")
    app_version: str = Field(default="2.0.0", description="Application version")
    debug: bool = Field(default=False, description="Enable debug mode")
    
    # Logging Configuration
    log_dir: str = Field(default="logs", description="Log directory path")
    log_level: str = Field(default="INFO", description="Logging level")
    log_retention_days: int = Field(default=30, ge=1, le=365, description="Log retention in days")
    enable_json_logging: bool = Field(default=True, description="Enable JSON structured logging")
    
    # Database/Cache Configuration
    redis_url: str = Field(default="redis://localhost:6379/0", description="Redis connection URL")
    redis_timeout: int = Field(default=5, ge=1, le=60, description="Redis timeout in seconds")
    redis_max_connections: int = Field(default=10, ge=1, le=100, description="Redis max connections")
    
    # Cache TTL Settings (in seconds)
    cache_ttl_price_data: int = Field(default=3600, ge=60, le=86400, description="Price data cache TTL")
    cache_ttl_economic_data: int = Field(default=14400, ge=300, le=86400, description="Economic data cache TTL")
    cache_ttl_news_data: int = Field(default=1800, ge=60, le=7200, description="News data cache TTL")
    cache_ttl_sentiment_data: int = Field(default=3600, ge=300, le=14400, description="Sentiment data cache TTL")
    
    # Primary API Keys (required for core functionality)
    alpha_vantage_api_key: str = Field(..., min_length=8, description="Alpha Vantage API key")
    twelve_data_api_key: str = Field(..., min_length=8, description="Twelve Data API key")
    fred_api_key: str = Field(..., min_length=8, description="FRED API key")
    finnhub_api_key: str = Field(..., min_length=8, description="Finnhub API key")
    
    # Fallback API Keys (optional but recommended for redundancy)
    polygon_api_key: Optional[str] = Field(default=None, description="Polygon.io API key")
    marketstack_api_key: Optional[str] = Field(default=None, description="MarketStack API key")
    exchangerate_api_key: Optional[str] = Field(default=None, description="ExchangeRate-API key")
    fixer_api_key: Optional[str] = Field(default=None, description="Fixer.io API key")
    currency_api_key: Optional[str] = Field(default=None, description="CurrencyAPI key")
    freecurrency_api_key: Optional[str] = Field(default=None, description="FreeCurrencyAPI key")
    exchangerates_api_key: Optional[str] = Field(default=None, description="ExchangeRatesAPI key")
    
    # Messaging API Keys (required for notifications)
    telegram_bot_token: str = Field(..., min_length=10, description="Telegram bot token")
    telegram_group_id: str = Field(..., description="Telegram group/chat ID")
    signal_phone_number: str = Field(..., description="Signal CLI phone number")
    signal_group_id: str = Field(..., description="Signal group ID")
    
    # Optional/Deprecated API Keys
    news_api_key: Optional[str] = Field(default=None, description="News API key")
    reddit_client_id: Optional[str] = Field(default=None, description="Reddit API client ID")
    reddit_client_secret: Optional[str] = Field(default=None, description="Reddit API client secret")
    twitter_bearer_token: Optional[str] = Field(default=None, description="Twitter API bearer token")
    
    # Rate Limits (requests per period)
    alpha_vantage_rate_limit: int = Field(default=500, ge=1, le=10000, description="Alpha Vantage daily limit")
    twelve_data_rate_limit: int = Field(default=800, ge=1, le=10000, description="Twelve Data daily limit")
    fred_rate_limit: int = Field(default=120, ge=1, le=1000, description="FRED per minute limit")
    finnhub_rate_limit: int = Field(default=60, ge=1, le=1000, description="Finnhub per minute limit")
    
    # Fallback API Rate Limits
    polygon_rate_limit: int = Field(default=5, ge=1, le=100, description="Polygon per minute limit")
    marketstack_rate_limit: int = Field(default=100, ge=1, le=1000, description="MarketStack per hour limit")
    exchangerate_rate_limit: int = Field(default=1000, ge=1, le=10000, description="ExchangeRate-API per month")
    fixer_rate_limit: int = Field(default=100, ge=1, le=1000, description="Fixer.io per month limit")
    currency_api_rate_limit: int = Field(default=300, ge=1, le=1000, description="CurrencyAPI per month limit")
    freecurrency_rate_limit: int = Field(default=5000, ge=1, le=10000, description="FreeCurrencyAPI per month")
    exchangerates_rate_limit: int = Field(default=1000, ge=1, le=10000, description="ExchangeRatesAPI per month")
    
    # Signal Analysis Configuration
    analysis_weights: Dict[str, float] = Field(
        default={
            'technical': 0.75,    # Technical analysis weight (75%)
            'economic': 0.20,     # Economic analysis weight (20%)
            'geopolitical': 0.05  # Geopolitical analysis weight (5%)
        },
        description="Analysis component weights"
    )
    
    # Trading Signal Thresholds
    strong_signal_threshold: float = Field(default=0.7, ge=0.5, le=1.0, description="Strong signal threshold")
    medium_signal_threshold: float = Field(default=0.5, ge=0.3, le=0.8, description="Medium signal threshold")
    weak_signal_threshold: float = Field(default=0.3, ge=0.1, le=0.6, description="Weak signal threshold")
    
    # Risk Management Parameters
    max_stop_loss_pips: int = Field(default=200, ge=10, le=500, description="Maximum stop loss in pips")
    min_target_pips: int = Field(default=100, ge=5, le=200, description="Minimum target in pips")
    default_target_pips: int = Field(default=150, ge=10, le=500, description="Default target in pips")
    strong_signal_target_pips: int = Field(default=200, ge=50, le=300, description="Target pips for strong signals")
    medium_signal_target_pips: int = Field(default=150, ge=30, le=200, description="Target pips for medium signals")
    weak_signal_target_pips: int = Field(default=100, ge=20, le=150, description="Target pips for weak signals")
    risk_reward_ratio: float = Field(default=2.0, ge=1.0, le=5.0, description="Risk to reward ratio")
    max_daily_signals: int = Field(default=10, ge=1, le=50, description="Maximum signals per day")
    
    # Currency Pairs Configuration
    primary_currency_pairs: List[str] = Field(
        default=[
            "EURUSD", "GBPUSD", "USDJPY", "USDCHF", "USDCAD", "AUDUSD"
        ],
        description="Primary currency pairs for signal generation (6 major pairs)"
    )
    
    all_currency_pairs: List[str] = Field(
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
        description="All supported currency pairs"
    )
    
    # Messaging Configuration
    message_timeout: int = Field(default=30, ge=5, le=120, description="Message send timeout in seconds")
    message_retry_attempts: int = Field(default=3, ge=1, le=10, description="Message retry attempts")
    message_retry_delay: int = Field(default=5, ge=1, le=60, description="Message retry delay in seconds")
    
    # Signal CLI Configuration
    signal_cli_url: str = Field(default="http://localhost:8080", description="Signal CLI API URL")
    signal_cli_timeout: int = Field(default=30, ge=5, le=120, description="Signal CLI timeout")
    
    # Output Configuration
    output_dir: str = Field(default="LiveSignals", description="Output directory for live signals")
    enable_file_output: bool = Field(default=True, description="Enable file output for signals")
    
    # Validation Configuration
    enable_price_validation: bool = Field(default=True, description="Enable price validation")
    price_validation_sources: int = Field(default=3, ge=2, le=5, description="Number of sources for price validation")
    price_variance_threshold: float = Field(default=0.01, ge=0.001, le=0.1, description="Price variance threshold")
    
    # Development Configuration
    enable_mock_apis: bool = Field(default=False, description="Enable mock APIs for testing")
    mock_response_delay: float = Field(default=0.1, ge=0.0, le=5.0, description="Mock API response delay")
    
    @field_validator('log_level')
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        """Validate log level"""
        valid_levels = {'DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'}
        if v.upper() not in valid_levels:
            raise ValueError(f"Log level must be one of: {valid_levels}")
        return v.upper()
    
    @field_validator('app_env')
    @classmethod
    def validate_environment(cls, v: str) -> str:
        """Validate application environment"""
        valid_envs = {'development', 'testing', 'staging', 'production'}
        if v.lower() not in valid_envs:
            raise ValueError(f"Environment must be one of: {valid_envs}")
        return v.lower()
    
    @field_validator('analysis_weights')
    @classmethod
    def validate_analysis_weights(cls, v: Dict[str, float]) -> Dict[str, float]:
        """Validate analysis weights sum to 1.0"""
        total = sum(v.values())
        if not (0.95 <= total <= 1.05):  # Allow small floating point variance
            raise ValueError(f"Analysis weights must sum to 1.0, got {total}")
        return v
    
    @field_validator('primary_currency_pairs', 'all_currency_pairs')
    @classmethod
    def validate_currency_pairs(cls, v: List[str]) -> List[str]:
        """Validate currency pair format"""
        import re
        pattern = re.compile(r'^[A-Z]{6}$')  # USDCAD format
        
        for pair in v:
            if not pattern.match(pair):
                raise ValueError(f"Invalid currency pair format: {pair}. Expected format: USDCAD")
        return v
    
    @model_validator(mode='after')
    def validate_primary_pairs_subset(self) -> 'Settings':
        """Validate primary pairs are subset of all pairs"""
        for pair in self.primary_currency_pairs:
            if pair not in self.all_currency_pairs:
                raise ValueError(f"Primary pair {pair} not in all_currency_pairs list")
        return self
    
    def get_api_keys(self) -> Dict[str, str]:
        """Get all configured API keys"""
        keys = {}
        
        # Primary APIs
        keys['alpha_vantage'] = self.alpha_vantage_api_key
        keys['twelve_data'] = self.twelve_data_api_key
        keys['fred'] = self.fred_api_key
        keys['finnhub'] = self.finnhub_api_key
        
        # Fallback APIs (only if configured)
        if self.polygon_api_key:
            keys['polygon'] = self.polygon_api_key
        if self.marketstack_api_key:
            keys['marketstack'] = self.marketstack_api_key
        if self.exchangerate_api_key:
            keys['exchangerate'] = self.exchangerate_api_key
        if self.fixer_api_key:
            keys['fixer'] = self.fixer_api_key
        if self.currency_api_key:
            keys['currency_api'] = self.currency_api_key
        if self.freecurrency_api_key:
            keys['freecurrency'] = self.freecurrency_api_key
        if self.exchangerates_api_key:
            keys['exchangerates'] = self.exchangerates_api_key
        
        # Optional APIs
        if self.news_api_key:
            keys['news_api'] = self.news_api_key
        
        return keys
    
    def get_messaging_config(self) -> Dict[str, Any]:
        """Get messaging configuration"""
        return {
            'telegram': {
                'bot_token': self.telegram_bot_token,
                'group_id': self.telegram_group_id,
                'timeout': self.message_timeout
            },
            'signal': {
                'phone_number': self.signal_phone_number,
                'group_id': self.signal_group_id,
                'cli_url': self.signal_cli_url,
                'timeout': self.signal_cli_timeout
            },
            'retry': {
                'attempts': self.message_retry_attempts,
                'delay': self.message_retry_delay
            }
        }
    
    def get_risk_config(self) -> Dict[str, Any]:
        """Get risk management configuration"""
        return {
            'max_stop_loss_pips': self.max_stop_loss_pips,
            'min_target_pips': self.min_target_pips,
            'default_target_pips': self.default_target_pips,
            'risk_reward_ratio': self.risk_reward_ratio,
            'max_daily_signals': self.max_daily_signals,
            'thresholds': {
                'strong': self.strong_signal_threshold,
                'medium': self.medium_signal_threshold,
                'weak': self.weak_signal_threshold
            },
            'target_pips': {
                'strong': self.strong_signal_target_pips,
                'medium': self.medium_signal_target_pips,
                'weak': self.weak_signal_target_pips
            }
        }


@lru_cache()
def get_settings() -> Settings:
    """
    Get cached settings instance
    Uses LRU cache to ensure settings are loaded only once
    """
    try:
        return Settings()
    except Exception as e:
        raise ConfigurationError(
            f"Failed to load configuration: {str(e)}",
            error_code="CONFIG_LOAD_FAILED"
        ) from e


def validate_required_environment() -> None:
    """
    Validate that all required environment variables are set
    Raises ConfigurationError if any required variables are missing
    """
    settings = get_settings()
    
    required_fields = [
        'alpha_vantage_api_key',
        'twelve_data_api_key', 
        'fred_api_key',
        'finnhub_api_key',
        'telegram_bot_token',
        'telegram_group_id',
        'signal_phone_number',
        'signal_group_id'
    ]
    
    missing_fields = []
    for field in required_fields:
        if not getattr(settings, field, None):
            missing_fields.append(field.upper())
    
    if missing_fields:
        raise ConfigurationError(
            f"Missing required environment variables: {', '.join(missing_fields)}",
            error_code="MISSING_ENV_VARS",
            details={"missing_fields": missing_fields}
        )