"""
Messaging manager that coordinates all messaging platforms
"""

import asyncio
from typing import Dict, List, Optional, Any, Type

from ..core.config import get_settings
from ..core.logging import get_logger
from ..core.exceptions import MessagingError, ConfigurationError
from .base import BaseMessenger, MessageResult, MessageType, MessageStatus
from .telegram import TelegramMessenger
from .signal import SignalMessenger

logger = get_logger(__name__)


class MessagingManager:
    """
    Manages all messaging platforms and coordinates message delivery
    """
    
    def __init__(self):
        """Initialize messaging manager with configured platforms"""
        self.settings = get_settings()
        self.messengers: Dict[str, BaseMessenger] = {}
        self._setup_messengers()
    
    def _setup_messengers(self):
        """Setup all configured messaging platforms"""
        messaging_config = self.settings.get_messaging_config()
        
        # Setup Telegram messenger
        if messaging_config.get('telegram'):
            try:
                self.messengers['telegram'] = TelegramMessenger(
                    config=messaging_config['telegram']
                )
                logger.info("Telegram messenger initialized")
            except Exception as e:
                logger.error(f"Failed to initialize Telegram messenger: {e}")
        
        # Setup Signal messenger
        if messaging_config.get('signal'):
            try:
                self.messengers['signal'] = SignalMessenger(
                    config=messaging_config['signal']
                )
                logger.info("Signal messenger initialized")
            except Exception as e:
                logger.error(f"Failed to initialize Signal messenger: {e}")
        
        if not self.messengers:
            logger.warning("No messaging platforms configured")
    
    async def send_message(
        self,
        message: str,
        platforms: Optional[List[str]] = None,
        message_type: MessageType = MessageType.TEXT,
        **kwargs
    ) -> Dict[str, MessageResult]:
        """
        Send message to specified platforms
        
        Args:
            message: Message text to send
            platforms: List of platform names, or None for all enabled
            message_type: Type of message being sent
            **kwargs: Additional arguments passed to messengers
            
        Returns:
            Dictionary mapping platform names to MessageResult objects
        """
        if not message:
            raise MessagingError("Message text is required")
        
        # Determine which platforms to use
        if platforms is None:
            platforms = list(self.messengers.keys())
        
        # Filter to only enabled messengers that exist
        active_messengers = {
            name: messenger for name, messenger in self.messengers.items()
            if name in platforms and messenger.is_enabled()
        }
        
        if not active_messengers:
            logger.warning("No active messengers available")
            return {}
        
        logger.info(f"Sending message to {len(active_messengers)} platforms: {', '.join(active_messengers.keys())}")
        
        # Send messages concurrently to all platforms
        tasks = {}
        for name, messenger in active_messengers.items():
            task = asyncio.create_task(
                self._send_with_error_handling(messenger, message, message_type, **kwargs),
                name=f"send_{name}"
            )
            tasks[name] = task
        
        # Wait for all tasks to complete
        results = {}
        for name, task in tasks.items():
            try:
                results[name] = await task
            except Exception as e:
                logger.error(f"Unexpected error sending to {name}: {e}")
                results[name] = MessageResult(
                    status=MessageStatus.FAILED,
                    platform=name,
                    error=f"Unexpected error: {str(e)}"
                )
        
        # Log summary
        successful = [name for name, result in results.items() if result.success]
        failed = [name for name, result in results.items() if not result.success]
        
        if successful:
            logger.info(f"Successfully sent to: {', '.join(successful)}")
        
        if failed:
            logger.error(f"Failed to send to: {', '.join(failed)}")
            for name in failed:
                logger.error(f"   {name}: {results[name].error}")
        
        return results
    
    async def _send_with_error_handling(
        self,
        messenger: BaseMessenger,
        message: str,
        message_type: MessageType,
        **kwargs
    ) -> MessageResult:
        """
        Send message with comprehensive error handling
        
        Args:
            messenger: Messenger instance to use
            message: Message text
            message_type: Message type
            **kwargs: Additional arguments
            
        Returns:
            MessageResult
        """
        try:
            # Use retry mechanism from base messenger
            result = await messenger.send_with_retry(
                message=message,
                message_type=message_type,
                max_retries=self.settings.message_retry_attempts,
                retry_delay=self.settings.message_retry_delay,
                **kwargs
            )
            return result
            
        except MessagingError as e:
            logger.error(f"Messaging error on {messenger.platform_name}: {e}")
            return MessageResult(
                status=MessageStatus.FAILED,
                platform=messenger.platform_name,
                error=str(e)
            )
        except Exception as e:
            logger.error(f"Unexpected error on {messenger.platform_name}: {e}")
            return MessageResult(
                status=MessageStatus.FAILED,
                platform=messenger.platform_name,
                error=f"Unexpected error: {str(e)}"
            )
    
    async def test_all_platforms(self) -> Dict[str, bool]:
        """
        Test connectivity to all configured platforms
        
        Returns:
            Dictionary mapping platform names to test results
        """
        logger.info("Testing connectivity to all messaging platforms...")
        
        results = {}
        for name, messenger in self.messengers.items():
            if not messenger.is_enabled():
                logger.info(f"⏭️ Skipping disabled platform: {name}")
                results[name] = False
                continue
            
            try:
                logger.info(f"Testing {name}...")
                result = await messenger.test_connection()
                results[name] = result
                
                if result:
                    logger.info(f"{name}: Connection successful")
                else:
                    logger.warning(f"{name}: Connection failed")
                    
            except Exception as e:
                logger.error(f"{name}: Test error - {e}")
                results[name] = False
        
        successful = sum(results.values())
        total = len(results)
        logger.info(f"Platform tests completed: {successful}/{total} successful")
        
        return results
    
    def get_available_platforms(self) -> List[str]:
        """Get list of available (enabled) platforms"""
        return [
            name for name, messenger in self.messengers.items()
            if messenger.is_enabled()
        ]
    
    def get_platform_info(self) -> Dict[str, Dict[str, Any]]:
        """Get information about all platforms"""
        info = {}
        for name, messenger in self.messengers.items():
            info[name] = {
                'platform': messenger.platform_name,
                'enabled': messenger.is_enabled(),
                'class': messenger.__class__.__name__,
                'config_keys': list(messenger.config.keys())
            }
        return info
    
    async def send_test_message(
        self,
        platforms: Optional[List[str]] = None
    ) -> Dict[str, MessageResult]:
        """
        Send a test message to verify messaging functionality
        WARNING: This will actually send a message - use carefully!
        
        Args:
            platforms: Platforms to test, or None for all
            
        Returns:
            Dictionary of results
        """
        test_message = f"Forex Signals Test Message\nTimestamp: {asyncio.get_event_loop().time()}\n\nThis is a test message from the Enhanced Forex Signals System V2.0."
        
        logger.warning("Sending actual test message to messaging platforms")
        
        return await self.send_message(
            message=test_message,
            platforms=platforms,
            message_type=MessageType.TEXT
        )
    
    def __len__(self) -> int:
        """Number of configured messengers"""
        return len(self.messengers)
    
    def __contains__(self, platform_name: str) -> bool:
        """Check if platform is configured"""
        return platform_name in self.messengers
    
    def __getitem__(self, platform_name: str) -> BaseMessenger:
        """Get messenger by platform name"""
        if platform_name not in self.messengers:
            raise KeyError(f"Platform '{platform_name}' not configured")
        return self.messengers[platform_name]