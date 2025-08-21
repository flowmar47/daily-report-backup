"""
Signal CLI messenger implementation
"""

import asyncio
from typing import Optional, Dict, Any
import httpx

from ..core.logging import get_logger
from ..core.exceptions import MessagingError, NetworkError
from .base import BaseMessenger, MessageResult, MessageType, MessageStatus

logger = get_logger(__name__)


class SignalMessenger(BaseMessenger):
    """
    Signal CLI Docker API messenger implementation
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize Signal messenger
        
        Args:
            config: Configuration dict with phone number, group ID, and CLI URL
        """
        super().__init__("signal", config)
        
        self.phone_number = config.get('phone_number')
        self.group_id = config.get('group_id')
        self.cli_url = config.get('cli_url', 'http://localhost:8080')
        self.timeout = config.get('timeout', 30)
        
        if not self.phone_number:
            raise MessagingError(
                "Signal phone number is required",
                platform="signal"
            )
        
        if not self.group_id:
            raise MessagingError(
                "Signal group ID is required",
                platform="signal"
            )
        
        # Ensure CLI URL doesn't end with slash
        self.cli_url = self.cli_url.rstrip('/')
    
    async def send_message(
        self,
        message: str,
        recipient: Optional[str] = None,
        message_type: MessageType = MessageType.TEXT,
        **kwargs
    ) -> MessageResult:
        """
        Send message via Signal CLI Docker API
        
        Args:
            message: Message text to send
            recipient: Recipient group ID (uses default if None)
            message_type: Type of message
            **kwargs: Additional Signal-specific options
            
        Returns:
            MessageResult indicating success/failure
        """
        try:
            # Use recipient or default group ID  
            target_group = recipient or self.group_id
            
            # Prepare request data for Signal CLI API
            request_data = {
                'number': self.phone_number,
                'recipients': [target_group],
                'message': message
            }
            
            # Add any additional options
            if kwargs.get('attachment'):
                request_data['attachments'] = kwargs['attachment']
            
            # Make API request to Signal CLI
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.cli_url}/v2/send",
                    json=request_data,
                    headers={'Content-Type': 'application/json'}
                )
            
            # Handle response
            if response.status_code == 201:
                # Signal CLI returns 201 on successful send
                logger.info("✅ Signal: Message sent successfully")
                
                # Try to extract response data
                try:
                    response_data = response.json()
                    message_id = response_data.get('timestamp')
                except:
                    response_data = {}
                    message_id = None
                
                return MessageResult(
                    status=MessageStatus.SUCCESS,
                    platform=self.platform_name,
                    message_id=str(message_id) if message_id else None,
                    metadata={
                        'group_id': target_group,
                        'phone_number': self.phone_number,
                        'response': response_data
                    }
                )
                
            elif response.status_code == 400:
                error_msg = f"Bad request: {response.text}"
                logger.error(f"❌ Signal API error: {error_msg}")
                
                return MessageResult(
                    status=MessageStatus.FAILED,
                    platform=self.platform_name,
                    error=error_msg
                )
                
            elif response.status_code == 500:
                error_msg = f"Signal CLI server error: {response.text}"
                logger.error(f"❌ Signal server error: {error_msg}")
                
                return MessageResult(
                    status=MessageStatus.FAILED,
                    platform=self.platform_name,
                    error=error_msg
                )
                
            else:
                error_msg = f"HTTP {response.status_code}: {response.text}"
                logger.error(f"❌ Signal HTTP error: {error_msg}")
                
                return MessageResult(
                    status=MessageStatus.FAILED,
                    platform=self.platform_name,
                    error=error_msg
                )
                
        except httpx.ConnectError as e:
            error_msg = f"Connection failed - is Signal CLI running at {self.cli_url}? Error: {str(e)}"
            logger.error(f"❌ Signal connection error: {error_msg}")
            
            return MessageResult(
                status=MessageStatus.FAILED,
                platform=self.platform_name,
                error=error_msg
            )
            
        except httpx.TimeoutException:
            error_msg = f"Request timeout after {self.timeout}s"
            logger.error(f"❌ Signal timeout: {error_msg}")
            
            return MessageResult(
                status=MessageStatus.FAILED,
                platform=self.platform_name,
                error=error_msg
            )
            
        except httpx.NetworkError as e:
            error_msg = f"Network error: {str(e)}"
            logger.error(f"❌ Signal network error: {error_msg}")
            
            return MessageResult(
                status=MessageStatus.FAILED,
                platform=self.platform_name,
                error=error_msg
            )
            
        except Exception as e:
            error_msg = f"Unexpected error: {str(e)}"
            logger.error(f"❌ Signal unexpected error: {error_msg}")
            
            return MessageResult(
                status=MessageStatus.FAILED,
                platform=self.platform_name,
                error=error_msg
            )
    
    async def test_connection(self) -> bool:
        """
        Test connection to Signal CLI API
        
        Returns:
            True if connection successful, False otherwise
        """
        try:
            # Test basic connectivity to Signal CLI
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(f"{self.cli_url}/v1/about")
            
            if response.status_code == 200:
                logger.info("✅ Signal CLI connection test successful")
                return True
            else:
                logger.error(f"❌ Signal CLI returned status {response.status_code}")
                return False
                
        except httpx.ConnectError as e:
            logger.error(f"❌ Signal CLI connection failed - is it running at {self.cli_url}? Error: {e}")
            return False
            
        except Exception as e:
            logger.error(f"❌ Signal connection test failed: {e}")
            return False
    
    async def list_groups(self) -> Optional[Dict[str, Any]]:
        """
        List Signal groups for the configured phone number
        
        Returns:
            Groups information or None if failed
        """
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    f"{self.cli_url}/v1/groups/{self.phone_number}"
                )
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"❌ Failed to list groups: HTTP {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"❌ Error listing Signal groups: {e}")
            return None
    
    async def get_group_info(self, group_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        Get information about a specific Signal group
        
        Args:
            group_id: Group ID to get info for (uses default if None)
            
        Returns:
            Group information or None if failed
        """
        try:
            target_group = group_id or self.group_id
            
            # List all groups and find the target
            groups_data = await self.list_groups()
            if not groups_data:
                return None
            
            # Find the specific group
            groups = groups_data.get('groups', [])
            for group in groups:
                if group.get('id') == target_group:
                    return group
            
            logger.warning(f"⚠️ Group {target_group} not found")
            return None
            
        except Exception as e:
            logger.error(f"❌ Error getting group info: {e}")
            return None
    
    def format_message_for_signal(self, message: str, message_type: MessageType) -> str:
        """
        Format message for Signal (plain text, no special formatting)
        
        Args:
            message: Raw message text
            message_type: Type of message
            
        Returns:
            Formatted message for Signal
        """
        # Signal supports plain text only, so no formatting needed
        # Just ensure proper line endings
        return message.replace('\r\n', '\n').replace('\r', '\n')
    
    def __str__(self) -> str:
        return f"SignalMessenger(phone={self.phone_number}, group={self.group_id})"