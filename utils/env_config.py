#!/usr/bin/env python3
"""
Standardized Environment Configuration Manager
Centralized handling of environment variables across all components
"""

import os
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

class EnvironmentConfig:
    """Centralized environment variable management with validation"""
    
    REQUIRED_VARS = {
        'daily_report': [
            'MYMAMA_USERNAME',
            'MYMAMA_PASSWORD',
            'TELEGRAM_BOT_TOKEN',
            'TELEGRAM_GROUP_ID',
            'SIGNAL_PHONE_NUMBER',
            'SIGNAL_GROUP_ID'
        ],
        'currency_rates': [
            'FRED_API_KEY',
            'ALPHA_VANTAGE_KEY'
        ],
        'heatmaps': [
            'FRED_API_KEY'
        ]
    }
    
    OPTIONAL_VARS = {
        'daily_report': [
            'MYMAMA_GUEST_PASSWORD',
            'TELEGRAM_THREAD_ID',
            'SIGNAL_API_URL',
            'SIGNAL_CLI_PATH',
            'CHROME_BINARY_PATH',
            'WHATSAPP_PHONE_NUMBER',
            'WHATSAPP_GROUP_NAME',
            'WHATSAPP_GROUP_NAMES',
            'WHATSAPP_GROUP_ID',
            'WHATSAPP_GROUP_IDS',
            'WHATSAPP_HEADLESS',
            'WHATSAPP_CHROME_PATH',
            'WHATSAPP_SESSION_PATH'
        ],
        'currency_rates': [
            'SMTP_SERVER',
            'SMTP_PORT',
            'SENDER_EMAIL',
            'SENDER_PASSWORD'
        ]
    }
    
    DEFAULT_VALUES = {
        'SIGNAL_API_URL': 'http://localhost:8080',
        'SMTP_PORT': '587',
        'SMTP_SERVER': 'smtp.gmail.com',
        'WHATSAPP_HEADLESS': 'true',
        'WHATSAPP_SESSION_PATH': 'browser_sessions/whatsapp'
    }
    
    def __init__(self, component: str = 'daily_report', env_file: Optional[str] = None):
        """
        Initialize environment config for specific component
        
        Args:
            component: Component name ('daily_report', 'currency_rates', 'heatmaps')
            env_file: Optional path to .env file (auto-detected if None)
        """
        self.component = component
        self.env_file = env_file or self._find_env_file()
        self._load_environment()
        
    def _find_env_file(self) -> Optional[str]:
        """Auto-detect .env file location"""
        possible_paths = [
            Path.cwd() / '.env',
            Path(__file__).parent / '.env',
            Path(__file__).parent.parent / '.env',
            Path(__file__).parent.parent / 'daily-report' / '.env'
        ]
        
        for path in possible_paths:
            if path.exists():
                logger.info(f"Found .env file: {path}")
                return str(path)
        
        logger.warning("No .env file found - using system environment variables only")
        return None
    
    def _load_environment(self):
        """Load environment variables from file and system"""
        if self.env_file:
            try:
                load_dotenv(self.env_file)
                logger.info(f"Loaded environment from: {self.env_file}")
            except Exception as e:
                logger.warning(f"Failed to load .env file {self.env_file}: {e}")
    
    def get_required_vars(self) -> Dict[str, str]:
        """Get all required environment variables for component"""
        required = self.REQUIRED_VARS.get(self.component, [])
        result = {}
        missing = []
        
        for var in required:
            value = os.getenv(var)
            if value:
                result[var] = value
            else:
                missing.append(var)
        
        if missing:
            raise ValueError(f"Missing required environment variables for {self.component}: {missing}")
        
        return result
    
    def get_optional_vars(self) -> Dict[str, Optional[str]]:
        """Get all optional environment variables for component"""
        optional = self.OPTIONAL_VARS.get(self.component, [])
        result = {}
        
        for var in optional:
            result[var] = os.getenv(var) or self.DEFAULT_VALUES.get(var)
        
        return result
    
    def get_all_vars(self) -> Dict[str, Any]:
        """Get all environment variables for component"""
        result = {}
        result.update(self.get_required_vars())
        result.update(self.get_optional_vars())
        return result
    
    def validate_credentials(self) -> bool:
        """Validate that all required credentials are present and non-empty"""
        try:
            required = self.get_required_vars()
            
            # Check for empty or placeholder values
            invalid = []
            for key, value in required.items():
                if not value or value.startswith('your_') or value == 'placeholder':
                    invalid.append(key)
            
            if invalid:
                logger.error(f"Invalid credential values for {self.component}: {invalid}")
                return False
            
            logger.info(f"All credentials validated for {self.component}")
            return True
            
        except ValueError as e:
            logger.error(f"Credential validation failed: {e}")
            return False
    
    def get_credential(self, key: str, required: bool = True) -> Optional[str]:
        """Get a specific credential with validation"""
        value = os.getenv(key)
        
        if not value and required:
            raise ValueError(f"Required credential missing: {key}")
        
        if value and (value.startswith('your_') or value == 'placeholder'):
            if required:
                raise ValueError(f"Invalid credential value for {key}: appears to be placeholder")
            return None
        
        return value
    
    def create_env_template(self, output_path: str = None) -> str:
        """Create .env template file for component"""
        output_path = output_path or f".env.{self.component}.template"
        
        template_lines = [
            f"# Environment variables for {self.component} component",
            "",
            "# Required Variables"
        ]
        
        required = self.REQUIRED_VARS.get(self.component, [])
        for var in required:
            template_lines.append(f"{var}=your_{var.lower()}")
        
        template_lines.extend(["", "# Optional Variables"])
        
        optional = self.OPTIONAL_VARS.get(self.component, [])
        for var in optional:
            default = self.DEFAULT_VALUES.get(var, f"your_{var.lower()}")
            template_lines.append(f"# {var}={default}")
        
        template_content = "\n".join(template_lines)
        
        with open(output_path, 'w') as f:
            f.write(template_content)
        
        logger.info(f"Created environment template: {output_path}")
        return output_path
    
    @classmethod
    def validate_all_components(cls) -> Dict[str, bool]:
        """Validate credentials for all components"""
        results = {}
        
        for component in cls.REQUIRED_VARS.keys():
            try:
                config = cls(component)
                results[component] = config.validate_credentials()
            except Exception as e:
                logger.error(f"Failed to validate {component}: {e}")
                results[component] = False
        
        return results

def get_daily_report_config() -> EnvironmentConfig:
    """Convenience function for daily report configuration"""
    return EnvironmentConfig('daily_report')

def get_currency_rates_config() -> EnvironmentConfig:
    """Convenience function for currency rates configuration"""
    return EnvironmentConfig('currency_rates')

def get_heatmaps_config() -> EnvironmentConfig:
    """Convenience function for heatmaps configuration"""
    return EnvironmentConfig('heatmaps')

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Environment Configuration Manager")
    parser.add_argument('--component', choices=['daily_report', 'currency_rates', 'heatmaps'], 
                       default='daily_report', help="Component to configure")
    parser.add_argument('--validate', action='store_true', help="Validate credentials")
    parser.add_argument('--template', action='store_true', help="Create .env template")
    parser.add_argument('--validate-all', action='store_true', help="Validate all components")
    
    args = parser.parse_args()
    
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    
    if args.validate_all:
        results = EnvironmentConfig.validate_all_components()
        for component, valid in results.items():
            status = "✅ VALID" if valid else "❌ INVALID"
            print(f"{component}: {status}")
    
    elif args.validate:
        config = EnvironmentConfig(args.component)
        if config.validate_credentials():
            print(f"✅ {args.component} credentials are valid")
        else:
            print(f"❌ {args.component} credentials are invalid")
    
    elif args.template:
        config = EnvironmentConfig(args.component)
        template_path = config.create_env_template()
        print(f"✅ Created template: {template_path}")
    
    else:
        config = EnvironmentConfig(args.component)
        vars_info = config.get_all_vars()
        print(f"\n{args.component} Environment Variables:")
        for key, value in vars_info.items():
            masked_value = "***" if value and ('password' in key.lower() or 'token' in key.lower() or 'key' in key.lower()) else value
            print(f"  {key}: {masked_value}")