"""Configuration management for stock alerts system"""

import os
from typing import List, Optional, Dict, Any
from functools import lru_cache
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class StockAlertSettings(BaseSettings):
    """Stock alert system settings with environment variable support"""

    # Application Settings
    app_name: str = Field(default="stock-volume-alerts", description="Application name")
    app_env: str = Field(default="production", description="Application environment")

    # Logging
    log_dir: str = Field(default="logs", description="Log directory path")
    log_level: str = Field(default="INFO", description="Logging level")

    # API Keys (from existing forex system - reuse where applicable)
    alpha_vantage_api_key: Optional[str] = Field(default=None, description="Alpha Vantage API key")
    twelve_data_api_key: Optional[str] = Field(default=None, description="Twelve Data API key")
    finnhub_api_key: Optional[str] = Field(default=None, description="Finnhub API key")
    polygon_api_key: Optional[str] = Field(default=None, description="Polygon.io API key")

    # Rate Limits
    alpha_vantage_rate_limit: int = Field(default=500, description="Alpha Vantage daily limit")
    twelve_data_rate_limit: int = Field(default=800, description="Twelve Data daily limit")
    finnhub_rate_limit: int = Field(default=60, description="Finnhub per minute limit")
    polygon_rate_limit: int = Field(default=5, description="Polygon per minute limit")

    # Watchlist - Default stocks to monitor
    default_watchlist: List[str] = Field(
        default=[
            # Mega-cap Tech
            "AAPL", "MSFT", "GOOGL", "AMZN", "META", "NVDA", "TSLA",
            # Popular Trading Stocks
            "SPY", "QQQ", "AMD", "INTC", "NFLX", "DIS", "BA",
            # Financial
            "JPM", "BAC", "GS", "V", "MA",
            # Healthcare/Pharma
            "JNJ", "PFE", "UNH", "MRNA",
            # Energy
            "XOM", "CVX", "OXY",
            # Retail
            "WMT", "TGT", "COST", "HD",
            # Meme/High Volatility
            "GME", "AMC", "BBBY", "PLTR", "SOFI",
        ],
        description="Default stock watchlist"
    )

    # Volume Detection Thresholds
    unusual_volume_threshold: float = Field(
        default=2.0, ge=1.5, le=10.0,
        description="Multiplier over average volume to trigger alert (2.0 = 200% of avg)"
    )
    extreme_volume_threshold: float = Field(
        default=5.0, ge=3.0, le=20.0,
        description="Multiplier for extreme volume alert (5.0 = 500% of avg)"
    )
    volume_lookback_days: int = Field(
        default=20, ge=5, le=60,
        description="Days to look back for average volume calculation"
    )
    min_volume_for_alert: int = Field(
        default=100000, ge=10000,
        description="Minimum absolute volume to trigger alert"
    )

    # Extended Hours Settings
    premarket_start_hour: int = Field(default=4, ge=4, le=9, description="Pre-market start hour (ET)")
    premarket_end_hour: int = Field(default=9, description="Pre-market end hour (ET)")
    afterhours_start_hour: int = Field(default=16, description="After-hours start hour (ET)")
    afterhours_end_hour: int = Field(default=20, le=20, description="After-hours end hour (ET)")

    # Extended Hours Alert Thresholds
    extended_hours_price_change_threshold: float = Field(
        default=2.0, ge=0.5, le=10.0,
        description="Percentage price change to trigger extended hours alert"
    )
    extended_hours_volume_threshold: int = Field(
        default=50000, ge=10000,
        description="Minimum extended hours volume to be significant"
    )

    # Alert Formatting
    include_technical_context: bool = Field(
        default=True,
        description="Include RSI, price levels in alerts"
    )
    max_alerts_per_message: int = Field(
        default=10, ge=1, le=50,
        description="Maximum alerts per message batch"
    )

    # Caching
    cache_ttl_quote: int = Field(default=60, description="Quote cache TTL in seconds")
    cache_ttl_historical: int = Field(default=3600, description="Historical data cache TTL")

    # Messaging (reuse from forex system)
    telegram_bot_token: Optional[str] = Field(default=None, description="Telegram bot token")
    telegram_group_id: Optional[str] = Field(default=None, description="Telegram group ID")
    signal_phone_number: Optional[str] = Field(default=None, description="Signal phone number")
    signal_group_id: Optional[str] = Field(default=None, description="Signal group ID")
    signal_cli_url: str = Field(default="http://localhost:8080", description="Signal CLI URL")

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )

    @field_validator('log_level')
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        """Validate log level"""
        valid_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
        v = v.upper()
        if v not in valid_levels:
            raise ValueError(f"Log level must be one of: {valid_levels}")
        return v

    @field_validator('default_watchlist')
    @classmethod
    def validate_watchlist(cls, v: List[str]) -> List[str]:
        """Validate and normalize stock symbols"""
        return [symbol.upper().strip() for symbol in v if symbol.strip()]

    def get_api_keys(self) -> Dict[str, Optional[str]]:
        """Get all API keys"""
        return {
            'alpha_vantage': self.alpha_vantage_api_key,
            'twelve_data': self.twelve_data_api_key,
            'finnhub': self.finnhub_api_key,
            'polygon': self.polygon_api_key,
        }

    def get_rate_limits(self) -> Dict[str, int]:
        """Get rate limits for all APIs"""
        return {
            'alpha_vantage': self.alpha_vantage_rate_limit,
            'twelve_data': self.twelve_data_rate_limit,
            'finnhub': self.finnhub_rate_limit,
            'polygon': self.polygon_rate_limit,
        }

    def get_messaging_config(self) -> Dict[str, Any]:
        """Get messaging configuration"""
        config = {}

        if self.telegram_bot_token and self.telegram_group_id:
            config['telegram'] = {
                'bot_token': self.telegram_bot_token,
                'group_id': self.telegram_group_id,
                'enabled': True
            }

        if self.signal_phone_number and self.signal_group_id:
            config['signal'] = {
                'phone_number': self.signal_phone_number,
                'group_id': self.signal_group_id,
                'cli_url': self.signal_cli_url,
                'enabled': True
            }

        return config

    def is_api_configured(self, api_name: str) -> bool:
        """Check if an API is configured"""
        keys = self.get_api_keys()
        return keys.get(api_name) is not None and len(keys.get(api_name, '')) > 0


@lru_cache()
def get_stock_settings() -> StockAlertSettings:
    """Get cached settings instance"""
    return StockAlertSettings()


def validate_stock_environment() -> bool:
    """Validate that required environment variables are set"""
    settings = get_stock_settings()
    api_keys = settings.get_api_keys()

    # Check if at least one API is configured
    configured_apis = [k for k, v in api_keys.items() if v]

    if not configured_apis:
        raise ValueError(
            "No stock data API keys configured. "
            "Set at least one of: ALPHA_VANTAGE_API_KEY, TWELVE_DATA_API_KEY, "
            "FINNHUB_API_KEY, or POLYGON_API_KEY"
        )

    return True
