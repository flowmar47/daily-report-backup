#!/usr/bin/env python3
"""
Messenger Compatibility Wrapper
Provides backwards compatibility for old messenger imports
"""

import logging
import asyncio
import sys
from typing import Dict, Any, Optional, List
from pathlib import Path

# Add current directory to path to ensure imports work
current_dir = Path(__file__).parent
if str(current_dir) not in sys.path:
    sys.path.insert(0, str(current_dir))

from src.messengers.unified_messenger import (
    UnifiedMultiMessenger, 
    UnifiedTelegramMessenger, 
    UnifiedSignalMessenger,
    send_structured_financial_data as unified_send_structured,
    send_to_both_messengers as unified_send_both,
    AttachmentData,
    MessageResult
)

logger = logging.getLogger(__name__)

# Backwards compatibility for TelegramMessenger
class TelegramMessenger:
    """Compatibility wrapper for old TelegramMessenger"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        logger.warning("TelegramMessenger is deprecated. Use UnifiedTelegramMessenger instead.")
        try:
            from utils.env_config import EnvironmentConfig
        except ImportError:
            # Fallback to environment variables directly
            import os
            from dotenv import load_dotenv
            load_dotenv()
            # Create a simple config object that mimics EnvironmentConfig
            class SimpleConfig:
                def __init__(self):
                    self.telegram_bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
                    self.telegram_group_id = os.getenv('TELEGRAM_GROUP_ID')
                    self.telegram_thread_id = os.getenv('TELEGRAM_THREAD_ID')
                
                def get_all_vars(self) -> Dict[str, Any]:
                    """Mimic EnvironmentConfig.get_all_vars method"""
                    return {
                        'TELEGRAM_BOT_TOKEN': self.telegram_bot_token,
                        'TELEGRAM_GROUP_ID': self.telegram_group_id,
                        'TELEGRAM_THREAD_ID': self.telegram_thread_id,
                        'rate_limit_delay': 1.0,
                        'max_message_length': 4096,
                        'parse_mode': 'Markdown'
                    }
            config_obj = SimpleConfig()
            self.messenger = UnifiedTelegramMessenger(config_obj)
        else:
            self.messenger = UnifiedTelegramMessenger(EnvironmentConfig('daily_report'))
    
    async def send_message(self, message: str, **kwargs: Any) -> bool:
        """Compatibility method for old send_message"""
        result = await self.messenger.send_message(message, **kwargs)
        return bool(result.success)
    
    async def send_structured_financial_data(self, data: str, **kwargs: Any) -> bool:
        """Compatibility method for structured data"""
        result = await self.messenger.send_structured_financial_data(data, **kwargs)
        return bool(result.success)
    
    async def send_attachment(self, file_path: str, caption: str = "", **kwargs: Any) -> bool:
        """Compatibility method for attachments"""
        attachment = AttachmentData(file_path=Path(file_path), caption=caption)
        result = await self.messenger.send_attachment(attachment, **kwargs)
        return bool(result.success)

# Backwards compatibility for SignalMessenger
class SignalMessenger:
    """Compatibility wrapper for old SignalMessenger"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        logger.warning("SignalMessenger is deprecated. Use UnifiedSignalMessenger instead.")
        try:
            from utils.env_config import EnvironmentConfig
        except ImportError:
            # Fallback to environment variables directly
            import os
            from dotenv import load_dotenv
            load_dotenv()
            # Create a simple config object that mimics EnvironmentConfig
            class SimpleConfig:
                def __init__(self):
                    self.signal_phone_number = os.getenv('SIGNAL_PHONE_NUMBER')
                    self.signal_group_id = os.getenv('SIGNAL_GROUP_ID')
                    self.signal_api_url = os.getenv('SIGNAL_API_URL', 'http://localhost:8080')
                
                def get_all_vars(self) -> Dict[str, Any]:
                    """Mimic EnvironmentConfig.get_all_vars method"""
                    return {
                        'SIGNAL_PHONE_NUMBER': self.signal_phone_number,
                        'SIGNAL_GROUP_ID': self.signal_group_id,
                        'SIGNAL_API_URL': self.signal_api_url,
                        'rate_limit_delay': 1.0,
                        'max_message_length': 2000
                    }
            config_obj = SimpleConfig()
            self.messenger = UnifiedSignalMessenger(config_obj)
        else:
            self.messenger = UnifiedSignalMessenger(EnvironmentConfig('daily_report'))
    
    async def send_message(self, message: str, **kwargs: Any) -> bool:
        """Compatibility method for old send_message"""
        result = await self.messenger.send_message(message, **kwargs)
        return bool(result.success)
    
    async def send_structured_financial_data(self, data: str, **kwargs: Any) -> bool:
        """Compatibility method for structured data"""
        result = await self.messenger.send_structured_financial_data(data, **kwargs)
        return bool(result.success)

# Backwards compatibility for MultiMessenger
class MultiMessenger:
    """Compatibility wrapper for old MultiMessenger"""
    
    def __init__(self, platforms: Optional[List[str]] = None):
        logger.warning("MultiMessenger is deprecated. Use UnifiedMultiMessenger instead.")
        self.messenger = UnifiedMultiMessenger(platforms)
    
    async def send_to_all(self, message: str, **kwargs: Any) -> Dict[str, bool]:
        """Compatibility method for send_to_all"""
        results = await self.messenger.send_to_all(message, **kwargs)
        return {platform: bool(result.success) for platform, result in results.items()}
    
    async def send_structured_financial_data(self, data: str, **kwargs: Any) -> Dict[str, bool]:
        """Compatibility method for structured data"""
        results = await self.messenger.send_structured_financial_data(data, **kwargs)
        return {platform: bool(result.success) for platform, result in results.items()}
    
    async def cleanup(self) -> None:
        """Cleanup compatibility method"""
        await self.messenger.cleanup()

# Backwards compatibility functions
async def send_structured_financial_data(data: str, **kwargs: Any) -> Dict[str, bool]:
    """Compatibility function for sending structured data"""
    results = await unified_send_structured(data, **kwargs)
    return {platform: bool(result.success) for platform, result in results.items()}

async def send_to_both_messengers(message: str, **kwargs: Any) -> Dict[str, bool]:
    """Compatibility function for sending to both messengers"""
    results = await unified_send_both(message, **kwargs)
    return {platform: bool(result.success) for platform, result in results.items()}

# Export compatibility classes
__all__ = [
    'TelegramMessenger',
    'SignalMessenger',
    'MultiMessenger',
    'send_structured_financial_data',
    'send_to_both_messengers'
]
