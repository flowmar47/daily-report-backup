"""
Centralized configuration management for the financial alerts system.
"""

import os
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List
from dotenv import load_dotenv

logger = logging.getLogger(__name__)


class Settings:
    """Centralized settings manager."""
    
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
            logger.info(f"✅ Loaded environment from {self.env_path}")
        else:
            logger.warning(f"⚠️ Environment file not found: {self.env_path}")
        
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
                logger.info(f"✅ Loaded configuration from {self.config_path}")
                return config
            else:
                logger.warning(f"⚠️ Config file not found: {self.config_path}, using defaults")
                return self._get_default_config()
        except Exception as e:
            logger.error(f"❌ Error loading config: {e}")
            return self._get_default_config()

    def _get_default_config(self) -> Dict[str, Any]:
        """Get default configuration."""
        return {
            "app_settings": {
                "report_time": "06:00",
                "timezone": "America/Los_Angeles",
                "report_days": ["monday", "tuesday", "wednesday", "thursday", "friday"],
                "max_retries": 3,
                "retry_delay": 300,
                "debug_mode": False
            },
            "scraping": {
                "timeout": 60000,
                "wait_for_network_idle": True,
                "screenshot_on_error": True,
                "user_agent": "Mozilla/5.0 (X11; Linux aarch64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
                "viewport": {"width": 1920, "height": 1080},
                "session_persistence": {
                    "enabled": True,
                    "directory": "browser_sessions",
                    "clear_on_error": False,
                    "rotation_threshold": 10
                },
                "anti_detection": {
                    "enabled": True,
                    "randomize_headers": True,
                    "avoid_honeypots": True,
                    "human_typing_delay": True,
                    "fingerprint_protection": True
                },
                "request_throttling": {
                    "min_delay": 3,
                    "max_delay": 7,
                    "exponential_backoff": True
                }
            },
            "mymama": {
                "base_url": "https://MyMama.uk",
                "alerts_path": "/copy-of-alerts-essentials-1",
                "check_robots_txt": True
            },
            "telegram": {
                "parse_mode": "Markdown",
                "disable_notification": False,
                "rate_limit_delay": 1,
                "retry_on_flood": True
            },
            "data_retention": {
                "keep_reports_days": 30,
                "keep_logs_days": 7,
                "keep_screenshots_days": 3
            },
            "monitoring": {
                "log_level": "INFO",
                "track_success_rate": True
            }
        }

    def _validate_settings(self) -> None:
        """Validate required settings and environment variables."""
        required_env_vars = [
            'MYMAMA_USERNAME',
            'MYMAMA_PASSWORD', 
            'TELEGRAM_BOT_TOKEN',
            'TELEGRAM_GROUP_ID'
        ]
        
        missing_vars = []
        for var in required_env_vars:
            if not os.getenv(var):
                missing_vars.append(var)
        
        if missing_vars:
            logger.warning(f"⚠️ Missing environment variables: {', '.join(missing_vars)}")
        else:
            logger.info("✅ All required environment variables found")

    # Environment variable getters
    @property
    def mymama_username(self) -> Optional[str]:
        """Get MyMama username."""
        return os.getenv('MYMAMA_USERNAME')

    @property
    def mymama_password(self) -> Optional[str]:
        """Get MyMama password."""
        return os.getenv('MYMAMA_PASSWORD')

    @property
    def mymama_guest_password(self) -> Optional[str]:
        """Get MyMama guest password."""
        return os.getenv('MYMAMA_GUEST_PASSWORD')

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

    def get_scraping_config(self) -> Dict[str, Any]:
        """Get scraping configuration."""
        return self.config.get('scraping', {})

    def get_mymama_config(self) -> Dict[str, Any]:
        """Get MyMama configuration."""
        config = self.config.get('mymama', {})
        # Add credentials
        config['username'] = self.mymama_username
        config['password'] = self.mymama_password
        config['guest_password'] = self.mymama_guest_password
        return config

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

    def create_env_template(self, output_path: Optional[str] = None) -> str:
        """
        Create a .env template file.
        
        Args:
            output_path: Optional path for template file
            
        Returns:
            Path to created template
        """
        template_path = output_path or (Path(__file__).parent.parent.parent / ".env.template")
        
        template_content = """# Financial Alerts System Environment Variables

# MyMama Credentials
MYMAMA_USERNAME=your_mymama_username
MYMAMA_PASSWORD=your_mymama_password
MYMAMA_GUEST_PASSWORD=your_guest_password_if_needed

# Telegram Configuration
TELEGRAM_BOT_TOKEN=your_telegram_bot_token
TELEGRAM_GROUP_ID=your_telegram_group_id
TELEGRAM_THREAD_ID=your_telegram_thread_id_if_needed

# Signal Configuration
SIGNAL_PHONE_NUMBER=+1234567890
SIGNAL_GROUP_ID=your_signal_group_id
SIGNAL_API_URL=http://localhost:8080

# Optional: Custom paths
# SIGNAL_CLI_PATH=/path/to/signal-cli
# CHROME_BINARY_PATH=/path/to/chrome
"""
        
        with open(template_path, 'w') as f:
            f.write(template_content)
        
        logger.info(f"✅ Created .env template at {template_path}")
        return str(template_path)

    def validate_credentials(self) -> Dict[str, bool]:
        """
        Validate all credentials.
        
        Returns:
            Dictionary with validation results
        """
        results = {
            'mymama': bool(self.mymama_username and self.mymama_password),
            'telegram': bool(self.telegram_bot_token and self.telegram_group_id),
            'signal': bool(self.signal_phone_number and self.signal_group_id),
        }
        
        logger.info(f"Credential validation: {results}")
        return results

    def get_target_url(self) -> str:
        """Get the target scraping URL."""
        base_url = self.get('mymama.base_url', 'https://MyMama.uk')
        alerts_path = self.get('mymama.alerts_path', '/copy-of-alerts-essentials-1')
        return f"{base_url}{alerts_path}"

    def setup_directories(self) -> None:
        """Setup required directories."""
        base_dir = Path(__file__).parent.parent.parent
        directories = [
            'logs',
            'reports', 
            'browser_sessions',
            'cache',
            'output',
            'real_alerts_only',
            'structured_alerts'
        ]
        
        for directory in directories:
            dir_path = base_dir / directory
            dir_path.mkdir(exist_ok=True)
        
        logger.info(f"✅ Setup directories: {', '.join(directories)}")


# Global settings instance
settings = Settings()