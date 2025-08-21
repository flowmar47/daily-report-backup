"""
Signal messenger wrapper for backward compatibility
"""
import asyncio
import logging
import os
from pathlib import Path
from messenger_compatibility import SignalMessenger

logger = logging.getLogger(__name__)

def send_to_signal_sync(message: str) -> bool:
    """Send message to Signal synchronously"""
    try:
        return asyncio.run(send_to_signal_async(message))
    except Exception as e:
        logger.error(f"Signal sync send failed: {e}")
        return False

def send_attachment_to_signal_sync(file_path: str, caption: str = "") -> bool:
    """Send attachment to Signal synchronously"""
    try:
        return asyncio.run(send_attachment_to_signal_async(file_path, caption))
    except Exception as e:
        logger.error(f"Signal attachment sync send failed: {e}")
        return False

async def send_to_signal_async(message: str) -> bool:
    """Send message to Signal asynchronously"""
    try:
        # Get Signal configuration from environment
        config = {
            'api_url': os.getenv('SIGNAL_API_URL', 'http://localhost:8080'),
            'phone_number': os.getenv('SIGNAL_PHONE_NUMBER'),
            'group_id': os.getenv('SIGNAL_GROUP_ID')
        }
        
        if not config['phone_number'] or not config['group_id']:
            logger.warning("Signal configuration missing")
            return False
        
        messenger = SignalMessenger(config)
        result = await messenger.send_message(message)
        
        return result.status == "success"
        
    except Exception as e:
        logger.error(f"Signal async send failed: {e}")
        return False

async def send_attachment_to_signal_async(file_path: str, caption: str = "") -> bool:
    """Send attachment to Signal asynchronously"""
    try:
        # Get Signal configuration from environment
        config = {
            'api_url': os.getenv('SIGNAL_API_URL', 'http://localhost:8080'),
            'phone_number': os.getenv('SIGNAL_PHONE_NUMBER'),
            'group_id': os.getenv('SIGNAL_GROUP_ID')
        }
        
        if not config['phone_number'] or not config['group_id']:
            logger.warning("Signal configuration missing")
            return False
        
        messenger = SignalMessenger(config)
        result = await messenger.send_attachment(file_path, caption)
        
        return result.status == "success"
        
    except Exception as e:
        logger.error(f"Signal attachment async send failed: {e}")
        return False