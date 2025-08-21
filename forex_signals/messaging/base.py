"""
Base messaging interface and common utilities
"""

import asyncio
from abc import ABC, abstractmethod
from datetime import datetime
from enum import Enum
from typing import Optional, Dict, Any
from dataclasses import dataclass, field

from ..core.exceptions import MessagingError


class MessageType(str, Enum):
    """Type of message being sent"""
    TEXT = "text"
    FOREX_SIGNALS = "forex_signals"
    ALERT = "alert"
    REPORT = "report"
    IMAGE = "image"
    DOCUMENT = "document"


class MessageStatus(str, Enum):
    """Status of message delivery"""
    SUCCESS = "success"
    FAILED = "failed" 
    PENDING = "pending"
    PARTIAL = "partial"
    RETRYING = "retrying"


@dataclass
class MessageResult:
    """Result of a message delivery attempt"""
    status: MessageStatus
    platform: str
    message_id: Optional[str] = None
    error: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)
    retry_count: int = 0
    
    @property
    def success(self) -> bool:
        """Check if message was successful"""
        return self.status == MessageStatus.SUCCESS


class BaseMessenger(ABC):
    """
    Abstract base class for all messaging platforms
    Defines the interface that all messengers must implement
    """
    
    def __init__(self, platform_name: str, config: Dict[str, Any]):
        """
        Initialize messenger
        
        Args:
            platform_name: Name of the messaging platform
            config: Platform-specific configuration
        """
        self.platform_name = platform_name
        self.config = config
        self.enabled = config.get('enabled', True)
    
    @abstractmethod
    async def send_message(
        self,
        message: str,
        recipient: Optional[str] = None,
        message_type: MessageType = MessageType.TEXT,
        **kwargs
    ) -> MessageResult:
        """
        Send a message via this platform
        
        Args:
            message: Message text to send
            recipient: Recipient ID/address (platform-specific)
            message_type: Type of message being sent
            **kwargs: Additional platform-specific arguments
            
        Returns:
            MessageResult indicating success/failure
        """
        pass
    
    @abstractmethod
    async def test_connection(self) -> bool:
        """
        Test connection to the messaging platform
        
        Returns:
            True if connection is successful, False otherwise
        """
        pass
    
    def is_enabled(self) -> bool:
        """Check if messenger is enabled"""
        return self.enabled
    
    async def send_with_retry(
        self,
        message: str,
        recipient: Optional[str] = None,
        message_type: MessageType = MessageType.TEXT,
        max_retries: int = 3,
        retry_delay: float = 5.0,
        **kwargs
    ) -> MessageResult:
        """
        Send message with retry logic
        
        Args:
            message: Message text to send
            recipient: Recipient ID/address
            message_type: Type of message
            max_retries: Maximum number of retry attempts
            retry_delay: Delay between retries in seconds
            **kwargs: Additional arguments
            
        Returns:
            MessageResult with retry information
        """
        last_error = None
        
        for attempt in range(max_retries + 1):
            try:
                result = await self.send_message(
                    message=message,
                    recipient=recipient,
                    message_type=message_type,
                    **kwargs
                )
                
                result.retry_count = attempt
                
                if result.success:
                    return result
                    
                last_error = result.error
                
            except Exception as e:
                last_error = str(e)
            
            # Don't sleep after the last attempt
            if attempt < max_retries:
                await asyncio.sleep(retry_delay)
        
        # All retries failed
        return MessageResult(
            status=MessageStatus.FAILED,
            platform=self.platform_name,
            error=f"Failed after {max_retries} retries. Last error: {last_error}",
            retry_count=max_retries
        )
    
    def __str__(self) -> str:
        return f"{self.__class__.__name__}({self.platform_name})"
    
    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(platform_name='{self.platform_name}', enabled={self.enabled})"