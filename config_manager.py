"""
Enhanced Configuration Management with Validation
"""

import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime
import os

logger = logging.getLogger(__name__)

class ConfigValidator:
    """Validate configuration values and structure"""
    
    REQUIRED_SECTIONS = [
        'mymama', 'telegram', 'scraping', 'monitoring', 'security'
    ]
    
    REQUIRED_MYMAMA_FIELDS = [
        'base_url', 'essentials_path', 'selectors'
    ]
    
    REQUIRED_TELEGRAM_FIELDS = [
        'bot_token', 'group_id'
    ]
    
    @classmethod
    def validate_config(cls, config: Dict[str, Any]) -> tuple[bool, List[str]]:
        """Validate configuration structure and values"""
        errors = []
        
        # Check required sections
        for section in cls.REQUIRED_SECTIONS:
            if section not in config:
                errors.append(f"Missing required section: {section}")
        
        # Validate MyMama config
        if 'mymama' in config:
            mymama_config = config['mymama']
            for field in cls.REQUIRED_MYMAMA_FIELDS:
                if field not in mymama_config:
                    errors.append(f"Missing required field in mymama: {field}")
            
            # Validate selectors
            if 'selectors' in mymama_config:
                selectors = mymama_config['selectors']
                required_selectors = ['username', 'password', 'submit', 'content']
                for selector in required_selectors:
                    if selector not in selectors:
                        errors.append(f"Missing selector: {selector}")
        
        # Validate Telegram config
        if 'telegram' in config:
            telegram_config = config['telegram']
            for field in cls.REQUIRED_TELEGRAM_FIELDS:
                if field not in telegram_config:
                    errors.append(f"Missing required field in telegram: {field}")
        
        # Validate scraping timeouts
        if 'scraping' in config and 'timeouts' in config['scraping']:
            timeouts = config['scraping']['timeouts']
            for timeout_type, value in timeouts.items():
                if not isinstance(value, (int, float)) or value <= 0:
                    errors.append(f"Invalid timeout value for {timeout_type}: {value}")
        
        return len(errors) == 0, errors

class ConfigManager:
    """Enhanced configuration management with validation and fallbacks"""
    
    def __init__(self, config_path: str = 'config.json'):
        self.config_path = Path(config_path)
        self.config = {}
        self.fallback_config = self._get_fallback_config()
        self.load_config()
    
    def load_config(self) -> bool:
        """Load and validate configuration"""
        try:
            if not self.config_path.exists():
                logger.error(f"Configuration file not found: {self.config_path}")
                self.config = self.fallback_config.copy()
                return False
            
            with open(self.config_path, 'r') as f:
                self.config = json.load(f)
            
            # Validate configuration
            is_valid, errors = ConfigValidator.validate_config(self.config)
            
            if not is_valid:
                logger.error("Configuration validation failed:")
                for error in errors:
                    logger.error(f"  - {error}")
                
                # Merge with fallback for missing values
                self._merge_with_fallback()
                logger.warning("Using fallback values for missing configuration")
            
            logger.info("Configuration loaded successfully")
            return True
            
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in config file: {e}")
            self.config = self.fallback_config.copy()
            return False
        except Exception as e:
            logger.error(f"Error loading configuration: {e}")
            self.config = self.fallback_config.copy()
            return False
    
    def get(self, key_path: str, default: Any = None) -> Any:
        """Get configuration value using dot notation (e.g., 'mymama.base_url')"""
        keys = key_path.split('.')
        value = self.config
        
        try:
            for key in keys:
                value = value[key]
            return value
        except (KeyError, TypeError):
            logger.debug(f"Configuration key not found: {key_path}, using default: {default}")
            return default
    
    def set(self, key_path: str, value: Any) -> bool:
        """Set configuration value using dot notation"""
        keys = key_path.split('.')
        config_ref = self.config
        
        try:
            for key in keys[:-1]:
                if key not in config_ref:
                    config_ref[key] = {}
                config_ref = config_ref[key]
            
            config_ref[keys[-1]] = value
            logger.debug(f"Configuration updated: {key_path} = {value}")
            return True
            
        except Exception as e:
            logger.error(f"Error setting configuration {key_path}: {e}")
            return False
    
    def save_config(self) -> bool:
        """Save current configuration to file"""
        try:
            with open(self.config_path, 'w') as f:
                json.dump(self.config, f, indent=2)
            logger.info(f"Configuration saved to {self.config_path}")
            return True
        except Exception as e:
            logger.error(f"Error saving configuration: {e}")
            return False
    
    def _merge_with_fallback(self):
        """Merge current config with fallback for missing values"""
        def deep_merge(base: dict, fallback: dict):
            for key, value in fallback.items():
                if key not in base:
                    base[key] = value
                elif isinstance(value, dict) and isinstance(base[key], dict):
                    deep_merge(base[key], value)
        
        deep_merge(self.config, self.fallback_config)
    
    def _get_fallback_config(self) -> Dict[str, Any]:
        """Get fallback configuration values"""
        return {
            "mymama": {
                "base_url": "https://www.mymama.uk",
                "essentials_path": "/copy-of-alerts-essentials-1",
                "selectors": {
                    "username": "input[type='email']",
                    "password": "input[type='password']",
                    "submit": "button[type='submit']",
                    "content": ".main-content"
                }
            },
            "telegram": {
                "bot_token": "",
                "group_id": "",
                "message_format": "markdown"
            },
            "scraping": {
                "timeouts": {
                    "page_load": 30,
                    "element_wait": 10,
                    "navigation": 15
                },
                "request_throttling": {
                    "min_delay": 3.0,
                    "max_delay": 10.0
                },
                "retry_attempts": {
                    "max_retries": 3,
                    "backoff_factor": 2
                }
            },
            "monitoring": {
                "log_level": "INFO",
                "health_check_interval": 15,
                "success_rate_threshold": 0.8
            },
            "security": {
                "encrypt_credentials": True,
                "anonymize_logs": True,
                "respect_robots_txt": True
            }
        }
    
    def get_environment_overrides(self) -> Dict[str, str]:
        """Get configuration overrides from environment variables"""
        overrides = {}
        
        # Map environment variables to config paths
        env_mappings = {
            'MYMAMA_USERNAME': 'mymama.credentials.username',
            'MYMAMA_PASSWORD': 'mymama.credentials.password',
            'TELEGRAM_BOT_TOKEN': 'telegram.bot_token',
            'TELEGRAM_GROUP_ID': 'telegram.group_id',
            'LOG_LEVEL': 'monitoring.log_level'
        }
        
        for env_var, config_path in env_mappings.items():
            env_value = os.getenv(env_var)
            if env_value:
                overrides[config_path] = env_value
        
        return overrides
    
    def apply_environment_overrides(self):
        """Apply environment variable overrides to configuration"""
        overrides = self.get_environment_overrides()
        
        for config_path, value in overrides.items():
            self.set(config_path, value)
            logger.debug(f"Applied environment override: {config_path}")

# Global configuration manager instance
config_manager = ConfigManager()