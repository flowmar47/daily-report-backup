"""
Centralized configuration management for the API-based forex signal system.

This module manages configuration for:
- Multiple financial API integrations (Alpha Vantage, Twelve Data, FRED, Finnhub, etc.)
- Messaging platforms (Telegram, Signal)
- Application settings and scheduling
"""

import os
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List
from dotenv import load_dotenv

logger = logging.getLogger(__name__)


class Settings:
    """Centralized settings manager for API-based signal generation system."""

    def __init__(self, config_path: Optional[str] = None, env_path: Optional[str] = None):
        """
        Initialize settings.

        Args:
            config_path: Path to config.json file
            env_path: Path to .env file
        """
        # Determine paths
        base_dir = Path(__file__).parent.parent.parent
        self.config_path = config_path or (base_dir / "config.json")
        self.env_path = env_path or (base_dir / ".env")

        # Load environment variables
        if self.env_path.exists():
            load_dotenv(self.env_path)
            logger.info(f"Loaded environment from {self.env_path}")
        else:
            logger.warning(f"Environment file not found: {self.env_path}")

        # Load JSON config
        self.config = self._load_config()

        # Validate required settings
        self._validate_settings()

    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from JSON file."""
        try:
            if self.config_path.exists():
                with open(self.config_path, 'r') as f:
                    config = json.load(f)
                logger.info(f"Loaded configuration from {self.config_path}")
                return config
            else:
                logger.warning(f"Config file not found: {self.config_path}, using defaults")
                return self._get_default_config()
        except Exception as e:
            logger.error(f"Error loading config: {e}")
            return self._get_default_config()

    def _get_default_config(self) -> Dict[str, Any]:
        """Get default configuration for API-based signal system."""
        return {
            "app_settings": {
                "report_time": "06:00",
                "timezone": "America/Los_Angeles",
                "report_days": ["monday", "tuesday", "wednesday", "thursday", "friday"],
                "max_retries": 3,
                "retry_delay": 300,
                "debug_mode": False
            },
            "api_settings": {
                "timeout": 30,
                "retry_on_error": True,
                "max_retries": 3,
                "rate_limit_protection": True
            },
            "analysis": {
                "technical_weight": 0.75,
                "economic_weight": 0.20,
                "geopolitical_weight": 0.05,
                "strong_signal_threshold": 0.7,
                "medium_signal_threshold": 0.5,
                "min_confidence_for_transmission": 0.6
            },
            "price_validation": {
                "min_sources": 3,
                "max_variance_percent": 0.5,
                "require_real_data": True
            },
            "telegram": {
                "parse_mode": "Markdown",
                "disable_notification": False,
                "rate_limit_delay": 1,
                "retry_on_flood": True
            },
            "signal_messenger": {
                "rate_limit_delay": 2,
                "retry_on_error": True
            },
            "data_retention": {
                "keep_reports_days": 30,
                "keep_logs_days": 7
            },
            "monitoring": {
                "log_level": "INFO",
                "track_success_rate": True
            }
        }

    def _validate_settings(self) -> None:
        """Validate required settings and environment variables."""
        # Primary API keys - at least one should be configured
        primary_api_vars = [
            'ALPHA_VANTAGE_API_KEY',
            'TWELVE_DATA_API_KEY',
            'FRED_API_KEY',
            'FINNHUB_API_KEY'
        ]

        # Messaging - required for delivery
        messaging_vars = [
            'TELEGRAM_BOT_TOKEN',
            'TELEGRAM_GROUP_ID'
        ]

        # Check primary APIs
        api_configured = any(os.getenv(var) for var in primary_api_vars)
        if not api_configured:
            logger.warning(f"No primary API keys configured. At least one of {primary_api_vars} should be set.")
        else:
            configured_apis = [var for var in primary_api_vars if os.getenv(var)]
            logger.info(f"Primary APIs configured: {configured_apis}")

        # Check messaging
        missing_messaging = [var for var in messaging_vars if not os.getenv(var)]
        if missing_messaging:
            logger.warning(f"Missing messaging variables: {', '.join(missing_messaging)}")
        else:
            logger.info("All required messaging variables found")

    # API Key Properties (Primary)
    @property
    def alpha_vantage_api_key(self) -> Optional[str]:
        """Get Alpha Vantage API key."""
        return os.getenv('ALPHA_VANTAGE_API_KEY')

    @property
    def twelve_data_api_key(self) -> Optional[str]:
        """Get Twelve Data API key."""
        return os.getenv('TWELVE_DATA_API_KEY')

    @property
    def fred_api_key(self) -> Optional[str]:
        """Get FRED API key."""
        return os.getenv('FRED_API_KEY')

    @property
    def finnhub_api_key(self) -> Optional[str]:
        """Get Finnhub API key."""
        return os.getenv('FINNHUB_API_KEY')

    # API Key Properties (Fallback)
    @property
    def polygon_api_key(self) -> Optional[str]:
        """Get Polygon.io API key."""
        return os.getenv('POLYGON_API_KEY')

    @property
    def marketstack_api_key(self) -> Optional[str]:
        """Get MarketStack API key."""
        return os.getenv('MARKETSTACK_API_KEY')

    @property
    def exchangerate_api_key(self) -> Optional[str]:
        """Get ExchangeRate-API key."""
        return os.getenv('EXCHANGERATE_API_KEY')

    @property
    def fixer_api_key(self) -> Optional[str]:
        """Get Fixer.io API key."""
        return os.getenv('FIXER_API_KEY')

    @property
    def currency_api_key(self) -> Optional[str]:
        """Get CurrencyAPI key."""
        return os.getenv('CURRENCY_API_KEY')

    @property
    def freecurrency_api_key(self) -> Optional[str]:
        """Get FreeCurrencyAPI key."""
        return os.getenv('FREECURRENCY_API_KEY')

    # Messaging Properties
    @property
    def telegram_bot_token(self) -> Optional[str]:
        """Get Telegram bot token."""
        return os.getenv('TELEGRAM_BOT_TOKEN')

    @property
    def telegram_group_id(self) -> Optional[str]:
        """Get Telegram group ID."""
        return os.getenv('TELEGRAM_GROUP_ID')

    @property
    def telegram_thread_id(self) -> Optional[str]:
        """Get Telegram thread ID."""
        return os.getenv('TELEGRAM_THREAD_ID')

    @property
    def signal_phone_number(self) -> Optional[str]:
        """Get Signal phone number."""
        return os.getenv('SIGNAL_PHONE_NUMBER', '+16572463906')

    @property
    def signal_group_id(self) -> Optional[str]:
        """Get Signal group ID."""
        return os.getenv('SIGNAL_GROUP_ID')

    @property
    def signal_api_url(self) -> str:
        """Get Signal API URL."""
        return os.getenv('SIGNAL_API_URL', 'http://localhost:8080')

    # Configuration getters
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value by key."""
        keys = key.split('.')
        value = self.config

        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default

        return value

    def get_api_config(self) -> Dict[str, Any]:
        """Get API configuration."""
        return self.config.get('api_settings', {})

    def get_analysis_config(self) -> Dict[str, Any]:
        """Get analysis configuration."""
        return self.config.get('analysis', {})

    def get_price_validation_config(self) -> Dict[str, Any]:
        """Get price validation configuration."""
        return self.config.get('price_validation', {})

    def get_telegram_config(self) -> Dict[str, Any]:
        """Get Telegram configuration."""
        config = self.config.get('telegram', {})
        # Add credentials
        config['bot_token'] = self.telegram_bot_token
        config['chat_id'] = self.telegram_group_id
        config['thread_id'] = self.telegram_thread_id
        return config

    def get_signal_config(self) -> Dict[str, Any]:
        """Get Signal configuration."""
        return {
            'phone_number': self.signal_phone_number,
            'group_id': self.signal_group_id,
            'api_url': self.signal_api_url,
            'signal_cli_path': 'signal-cli'
        }

    def get_app_settings(self) -> Dict[str, Any]:
        """Get application settings."""
        return self.config.get('app_settings', {})

    def get_data_retention_config(self) -> Dict[str, Any]:
        """Get data retention configuration."""
        return self.config.get('data_retention', {})

    def get_monitoring_config(self) -> Dict[str, Any]:
        """Get monitoring configuration."""
        return self.config.get('monitoring', {})

    def get_all_api_keys(self) -> Dict[str, Optional[str]]:
        """Get all configured API keys."""
        return {
            'alpha_vantage': self.alpha_vantage_api_key,
            'twelve_data': self.twelve_data_api_key,
            'fred': self.fred_api_key,
            'finnhub': self.finnhub_api_key,
            'polygon': self.polygon_api_key,
            'marketstack': self.marketstack_api_key,
            'exchangerate': self.exchangerate_api_key,
            'fixer': self.fixer_api_key,
            'currency_api': self.currency_api_key,
            'freecurrency': self.freecurrency_api_key,
        }

    def create_env_template(self, output_path: Optional[str] = None) -> str:
        """
        Create a .env template file.

        Args:
            output_path: Optional path for template file

        Returns:
            Path to created template
        """
        template_path = output_path or (Path(__file__).parent.parent.parent / ".env.template")

        template_content = """# API-Based Forex Signal System Environment Variables

# Primary API Keys (at least one required)
ALPHA_VANTAGE_API_KEY=your_alpha_vantage_key
TWELVE_DATA_API_KEY=your_twelve_data_key
FRED_API_KEY=your_fred_key
FINNHUB_API_KEY=your_finnhub_key

# Fallback API Keys (recommended for reliability)
POLYGON_API_KEY=your_polygon_key
MARKETSTACK_API_KEY=your_marketstack_key
EXCHANGERATE_API_KEY=your_exchangerate_key
FIXER_API_KEY=your_fixer_key
CURRENCY_API_KEY=your_currency_api_key
FREECURRENCY_API_KEY=your_freecurrency_key
EXCHANGERATES_API_KEY=your_exchangerates_key

# Telegram Configuration (required for message delivery)
TELEGRAM_BOT_TOKEN=your_telegram_bot_token
TELEGRAM_GROUP_ID=your_telegram_group_id
TELEGRAM_THREAD_ID=your_telegram_thread_id_if_needed

# Signal Configuration (required for message delivery)
SIGNAL_PHONE_NUMBER=+1234567890
SIGNAL_GROUP_ID=your_signal_group_id
SIGNAL_API_URL=http://localhost:8080
"""

        with open(template_path, 'w') as f:
            f.write(template_content)

        logger.info(f"Created .env template at {template_path}")
        return str(template_path)

    def validate_credentials(self) -> Dict[str, bool]:
        """
        Validate all credentials.

        Returns:
            Dictionary with validation results
        """
        api_keys = self.get_all_api_keys()
        primary_apis_configured = any([
            api_keys['alpha_vantage'],
            api_keys['twelve_data'],
            api_keys['fred'],
            api_keys['finnhub']
        ])

        results = {
            'primary_apis': primary_apis_configured,
            'fallback_apis': any([
                api_keys['polygon'],
                api_keys['marketstack'],
                api_keys['exchangerate'],
                api_keys['fixer']
            ]),
            'telegram': bool(self.telegram_bot_token and self.telegram_group_id),
            'signal': bool(self.signal_phone_number and self.signal_group_id),
        }

        logger.info(f"Credential validation: {results}")
        return results

    def setup_directories(self) -> None:
        """Setup required directories."""
        base_dir = Path(__file__).parent.parent.parent
        directories = [
            'logs',
            'reports',
            'cache',
            'output',
        ]

        for directory in directories:
            dir_path = base_dir / directory
            dir_path.mkdir(exist_ok=True)

        logger.info(f"Setup directories: {', '.join(directories)}")


# Global settings instance
settings = Settings()
