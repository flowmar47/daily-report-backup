"""
Telegram messenger implementation
"""

import asyncio
from typing import Optional, Dict, Any
import httpx

from ..core.logging import get_logger
from ..core.exceptions import MessagingError, NetworkError
from .base import BaseMessenger, MessageResult, MessageType, MessageStatus

logger = get_logger(__name__)


class TelegramMessenger(BaseMessenger):
    """
    Telegram Bot API messenger implementation
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize Telegram messenger
        
        Args:
            config: Configuration dict with bot_token and group_id
        """
        super().__init__("telegram", config)
        
        self.bot_token = config.get('bot_token')
        self.group_id = config.get('group_id')
        self.timeout = config.get('timeout', 30)
        
        if not self.bot_token:
            raise MessagingError(
                "Telegram bot token is required",
                platform="telegram"
            )
        
        if not self.group_id:
            raise MessagingError(
                "Telegram group ID is required", 
                platform="telegram"
            )
        
        self.api_base_url = f"https://api.telegram.org/bot{self.bot_token}"
    
    async def send_message(
        self,
        message: str,
        recipient: Optional[str] = None,
        message_type: MessageType = MessageType.TEXT,
        **kwargs
    ) -> MessageResult:
        """
        Send message via Telegram Bot API
        
        Args:
            message: Message text to send
            recipient: Recipient chat ID (uses default if None)
            message_type: Type of message
            **kwargs: Additional Telegram-specific options
            
        Returns:
            MessageResult indicating success/failure
        """
        try:
            # Use recipient or default group ID
            chat_id = recipient or self.group_id
            
            # Prepare request data
            request_data = {
                'chat_id': chat_id,
                'text': message,
                'parse_mode': kwargs.get('parse_mode', 'HTML'),
                'disable_web_page_preview': kwargs.get('disable_preview', True),
                'disable_notification': kwargs.get('silent', False)
            }
            
            # Make API request
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.api_base_url}/sendMessage",
                    json=request_data
                )
            
            # Handle response
            if response.status_code == 200:
                response_data = response.json()
                
                if response_data.get('ok'):
                    message_id = response_data.get('result', {}).get('message_id')
                    logger.info(f"✅ Telegram: Message sent successfully (ID: {message_id})")
                    
                    return MessageResult(
                        status=MessageStatus.SUCCESS,
                        platform=self.platform_name,
                        message_id=str(message_id) if message_id else None,
                        metadata={
                            'chat_id': chat_id,
                            'response': response_data
                        }
                    )
                else:
                    error_description = response_data.get('description', 'Unknown error')
                    logger.error(f"❌ Telegram API error: {error_description}")
                    
                    return MessageResult(
                        status=MessageStatus.FAILED,
                        platform=self.platform_name,
                        error=f"Telegram API error: {error_description}"
                    )
            else:
                error_msg = f"HTTP {response.status_code}: {response.text}"
                logger.error(f"❌ Telegram HTTP error: {error_msg}")
                
                return MessageResult(
                    status=MessageStatus.FAILED,
                    platform=self.platform_name,
                    error=error_msg
                )
                
        except httpx.TimeoutException:
            error_msg = f"Request timeout after {self.timeout}s"
            logger.error(f"❌ Telegram timeout: {error_msg}")
            
            return MessageResult(
                status=MessageStatus.FAILED,
                platform=self.platform_name,
                error=error_msg
            )
            
        except httpx.NetworkError as e:
            error_msg = f"Network error: {str(e)}"
            logger.error(f"❌ Telegram network error: {error_msg}")
            
            return MessageResult(
                status=MessageStatus.FAILED,
                platform=self.platform_name,
                error=error_msg
            )
            
        except Exception as e:
            error_msg = f"Unexpected error: {str(e)}"
            logger.error(f"❌ Telegram unexpected error: {error_msg}")
            
            return MessageResult(
                status=MessageStatus.FAILED,
                platform=self.platform_name,
                error=error_msg
            )
    
    async def test_connection(self) -> bool:
        """
        Test connection to Telegram API
        
        Returns:
            True if connection successful, False otherwise
        """
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(f"{self.api_base_url}/getMe")
            
            if response.status_code == 200:
                data = response.json()
                if data.get('ok'):
                    bot_info = data.get('result', {})
                    logger.info(f"✅ Telegram connection test successful: @{bot_info.get('username', 'unknown')}")
                    return True
                else:
                    logger.error(f"❌ Telegram API error: {data.get('description', 'Unknown error')}")
                    return False
            else:
                logger.error(f"❌ Telegram HTTP error: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Telegram connection test failed: {e}")
            return False
    
    async def get_chat_info(self, chat_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        Get information about a chat
        
        Args:
            chat_id: Chat ID to get info for (uses default if None)
            
        Returns:
            Chat information dict or None if failed
        """
        try:
            target_chat = chat_id or self.group_id
            
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    f"{self.api_base_url}/getChat",
                    params={'chat_id': target_chat}
                )
            
            if response.status_code == 200:
                data = response.json()
                if data.get('ok'):
                    return data.get('result')
            
            return None
            
        except Exception as e:
            logger.error(f"❌ Error getting chat info: {e}")
            return None
    
    def format_message_for_telegram(self, message: str, message_type: MessageType) -> str:
        """
        Format message for Telegram (escape HTML entities, etc.)
        
        Args:
            message: Raw message text
            message_type: Type of message
            
        Returns:
            Formatted message for Telegram
        """
        # For forex signals, keep the format clean
        if message_type == MessageType.FOREX_SIGNALS:
            # Replace certain characters that might cause issues
            formatted = message.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
            
            # Add monospace formatting for structured data
            lines = formatted.split('\n')
            formatted_lines = []
            
            for line in lines:
                # Make pair names bold
                if line.startswith('Pair: '):
                    line = line.replace('Pair: ', '<b>Pair: </b>')
                # Make actions bold
                elif 'MT4 Action:' in line:
                    line = line.replace('MT4 Action:', '<b>MT4 Action:</b>')
                # Make headers bold
                elif line in ['FOREX PAIRS', 'FOREX TRADING SIGNALS', 'SIGNAL ANALYSIS SUMMARY']:
                    line = f'<b>{line}</b>'
                
                formatted_lines.append(line)
            
            return '\n'.join(formatted_lines)
        
        # Default formatting
        return message.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
    
    def __str__(self) -> str:
        return f"TelegramMessenger(group_id={self.group_id})"