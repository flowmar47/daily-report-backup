#!/usr/bin/env python3
"""
Unified Messenger System
Consolidates all messaging platforms into a single, well-architected system
Eliminates duplicate messenger implementations and provides consistent interface
"""

import asyncio
import logging
import os
import json
import httpx
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Optional, Dict, Any, List, Union
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

# Environment configuration
import sys
sys.path.append(str(Path(__file__).parent.parent.parent / 'utils'))
from env_config import EnvironmentConfig
from enhanced_error_handler import (
    resilient_operation, ErrorCategory, ErrorSeverity, RetryStrategy,
    circuit_breaker_protection
)

logger = logging.getLogger(__name__)

class MessageStatus(str, Enum):
    """Status of message delivery"""
    SUCCESS = "success"
    FAILED = "failed"
    PENDING = "pending"
    PARTIAL = "partial"
    RETRYING = "retrying"

class MessageType(str, Enum):
    """Type of message being sent"""
    TEXT = "text"
    IMAGE = "image"
    DOCUMENT = "document"
    STRUCTURED_REPORT = "structured_report"

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
        return self.status == MessageStatus.SUCCESS

@dataclass
class AttachmentData:
    """Data for message attachments"""
    file_path: Path
    caption: Optional[str] = None
    filename: Optional[str] = None
    content_type: Optional[str] = None

class MessagingError(Exception):
    """Base exception for messaging operations"""
    pass

class PlatformError(MessagingError):
    """Platform-specific messaging error"""
    pass

class RateLimitError(MessagingError):
    """Rate limiting error"""
    pass

class UnifiedBaseMessenger(ABC):
    """
    Unified base messenger that all platform implementations inherit from
    Provides standardized error handling, retry logic, and message formatting
    """
    
    def __init__(self, platform_name: str, env_config: EnvironmentConfig):
        """
        Initialize unified base messenger
        
        Args:
            platform_name: Name of the messaging platform
            env_config: Environment configuration instance
        """
        self.platform_name = platform_name
        self.env_config = env_config
        self.credentials = env_config.get_all_vars()
        
        # Platform configuration
        self.config = self._get_platform_config()
        self.client = None
        
        # Rate limiting
        self.last_message_time = {}
        self.rate_limit_delay = self.config.get('rate_limit_delay', 1.0)
        
        logger.info(f"🚀 {self.__class__.__name__} initialized for {platform_name}")
    
    @abstractmethod
    def _get_platform_config(self) -> Dict[str, Any]:
        """Get platform-specific configuration"""
        pass
    
    @abstractmethod
    async def _initialize_client(self):
        """Initialize platform-specific client"""
        pass
    
    @abstractmethod
    async def _send_text_message(self, message: str, **kwargs) -> MessageResult:
        """Send text message implementation"""
        pass
    
    @abstractmethod
    async def _send_attachment(self, attachment: AttachmentData, **kwargs) -> MessageResult:
        """Send attachment implementation"""
        pass
    
    async def _apply_rate_limiting(self, chat_id: str):
        """Apply rate limiting to prevent spam"""
        last_time = self.last_message_time.get(chat_id, 0)
        current_time = datetime.now().timestamp()
        
        if current_time - last_time < self.rate_limit_delay:
            delay = self.rate_limit_delay - (current_time - last_time)
            logger.info(f"Rate limiting: waiting {delay:.1f}s")
            await asyncio.sleep(delay)
        
        self.last_message_time[chat_id] = datetime.now().timestamp()
    
    @circuit_breaker_protection("messaging_platform")
    async def send_message(self, message: str, chat_id: Optional[str] = None, **kwargs) -> MessageResult:
        """
        Send text message with retry logic
        
        Args:
            message: Message text
            chat_id: Optional chat/group ID override
            **kwargs: Platform-specific parameters
            
        Returns:
            MessageResult with delivery status
        """
        try:
            if not self.client:
                await self._initialize_client()
            
            # Apply rate limiting
            target_chat = chat_id or self._get_default_chat_id()
            await self._apply_rate_limiting(target_chat)
            
            # Send message
            result = await self._send_text_message(message, chat_id=chat_id, **kwargs)
            
            if result.success:
                logger.info(f"✅ Message sent via {self.platform_name}: {result.message_id}")
            else:
                logger.error(f"❌ Failed to send message via {self.platform_name}: {result.error}")
            
            return result
            
        except Exception as e:
            logger.error(f"Message send error on {self.platform_name}: {e}")
            return MessageResult(
                status=MessageStatus.FAILED,
                platform=self.platform_name,
                error=str(e)
            )
    
    async def send_attachment(self, attachment: AttachmentData, chat_id: Optional[str] = None, **kwargs) -> MessageResult:
        """
        Send attachment with retry logic
        
        Args:
            attachment: Attachment data
            chat_id: Optional chat/group ID override
            **kwargs: Platform-specific parameters
            
        Returns:
            MessageResult with delivery status
        """
        try:
            if not self.client:
                await self._initialize_client()
            
            # Apply rate limiting
            target_chat = chat_id or self._get_default_chat_id()
            await self._apply_rate_limiting(target_chat)
            
            # Send attachment
            result = await self._send_attachment(attachment, chat_id=chat_id, **kwargs)
            
            if result.success:
                logger.info(f"✅ Attachment sent via {self.platform_name}: {attachment.file_path.name}")
            else:
                logger.error(f"❌ Failed to send attachment via {self.platform_name}: {result.error}")
            
            return result
            
        except Exception as e:
            logger.error(f"Attachment send error on {self.platform_name}: {e}")
            return MessageResult(
                status=MessageStatus.FAILED,
                platform=self.platform_name,
                error=str(e)
            )
    
    async def send_structured_financial_data(self, structured_data: str, **kwargs) -> MessageResult:
        """
        Send structured financial report
        
        Args:
            structured_data: Structured financial data text
            **kwargs: Platform-specific parameters
            
        Returns:
            MessageResult with delivery status
        """
        try:
            # Format for financial data
            formatted_message = self._format_financial_message(structured_data)
            
            # Split message if too long
            if len(formatted_message) > self._get_max_message_length():
                return await self._send_long_message(formatted_message, **kwargs)
            else:
                return await self.send_message(formatted_message, **kwargs)
                
        except Exception as e:
            logger.error(f"Structured data send error on {self.platform_name}: {e}")
            return MessageResult(
                status=MessageStatus.FAILED,
                platform=self.platform_name,
                error=str(e)
            )
    
    def _format_financial_data(self, data: str) -> str:
        """Format financial data for platform"""
        # Default formatting - can be overridden by subclasses
        return data
    
    def _get_max_message_length(self) -> int:
        """Get maximum message length for platform"""
        return self.config.get('max_message_length', 2000)
    
    async def _send_long_message(self, message: str, **kwargs) -> MessageResult:
        """Send long message by splitting into chunks"""
        max_length = self._get_max_message_length()
        chunks = []
        current_chunk = ""
        
        for line in message.split('\n'):
            if len(current_chunk + line + '\n') > max_length:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                current_chunk = line + '\n'
            else:
                current_chunk += line + '\n'
        
        if current_chunk:
            chunks.append(current_chunk.strip())
        
        results = []
        for i, chunk in enumerate(chunks):
            prefix = f"[Part {i+1}/{len(chunks)}]\n" if len(chunks) > 1 else ""
            result = await self.send_message(prefix + chunk, **kwargs)
            results.append(result)
            
            # Brief delay between chunks
            if i < len(chunks) - 1:
                await asyncio.sleep(1)
        
        # Return overall result
        success_count = sum(1 for r in results if r.success)
        if success_count == len(results):
            return MessageResult(status=MessageStatus.SUCCESS, platform=self.platform_name)
        elif success_count > 0:
            return MessageResult(status=MessageStatus.PARTIAL, platform=self.platform_name)
        else:
            return MessageResult(status=MessageStatus.FAILED, platform=self.platform_name)
    
    @abstractmethod
    def _get_default_chat_id(self) -> str:
        """Get default chat/group ID"""
        pass
    
    async def send_structured_financial_data(self, structured_data: str, **kwargs) -> MessageResult:
        """Send structured financial data with platform-specific formatting"""
        formatted_data = self._format_financial_data(structured_data)
        return await self.send_message(formatted_data, **kwargs)
    
    async def cleanup(self):
        """Clean up client resources"""
        if self.client:
            try:
                if hasattr(self.client, 'close'):
                    await self.client.close()
                self.client = None
            except Exception as e:
                logger.error(f"Error during {self.platform_name} cleanup: {e}")

class UnifiedTelegramMessenger(UnifiedBaseMessenger):
    """Unified Telegram messenger implementation"""
    
    def __init__(self, env_config: EnvironmentConfig):
        super().__init__('telegram', env_config)
    
    def _get_platform_config(self) -> Dict[str, Any]:
        return {
            'bot_token': self.credentials['TELEGRAM_BOT_TOKEN'],
            'group_id': self.credentials['TELEGRAM_GROUP_ID'],
            'thread_id': self.credentials.get('TELEGRAM_THREAD_ID'),
            'max_message_length': 4096,
            'rate_limit_delay': 1.0,
            'api_url': 'https://api.telegram.org'
        }
    
    async def _initialize_client(self):
        """Initialize Telegram HTTP client"""
        self.client = httpx.AsyncClient(
            base_url=f"{self.config['api_url']}/bot{self.config['bot_token']}",
            timeout=30.0
        )
    
    async def _send_text_message(self, message: str, chat_id: Optional[str] = None, **kwargs) -> MessageResult:
        """Send text message via Telegram API"""
        try:
            target_chat = chat_id or self.config['group_id']
            
            payload = {
                'chat_id': target_chat,
                'text': message,
                'parse_mode': kwargs.get('parse_mode', 'Markdown'),
                'disable_notification': kwargs.get('disable_notification', False)
            }
            
            if self.config.get('thread_id'):
                payload['message_thread_id'] = self.config['thread_id']
            
            response = await self.client.post('/sendMessage', json=payload)
            response.raise_for_status()
            
            result_data = response.json()
            if result_data.get('ok'):
                return MessageResult(
                    status=MessageStatus.SUCCESS,
                    platform=self.platform_name,
                    message_id=str(result_data['result']['message_id']),
                    metadata={'chat_id': target_chat}
                )
            else:
                return MessageResult(
                    status=MessageStatus.FAILED,
                    platform=self.platform_name,
                    error=result_data.get('description', 'Unknown error')
                )
                
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 429:  # Rate limited
                raise RateLimitError(f"Telegram rate limit: {e}")
            return MessageResult(
                status=MessageStatus.FAILED,
                platform=self.platform_name,
                error=f"HTTP error: {e}"
            )
        except Exception as e:
            return MessageResult(
                status=MessageStatus.FAILED,
                platform=self.platform_name,
                error=str(e)
            )
    
    async def _send_attachment(self, attachment: AttachmentData, chat_id: Optional[str] = None, **kwargs) -> MessageResult:
        """Send attachment via Telegram API"""
        try:
            target_chat = chat_id or self.config['group_id']
            
            with open(attachment.file_path, 'rb') as f:
                files = {'photo': f}
                data = {
                    'chat_id': target_chat,
                    'caption': attachment.caption or ''
                }
                
                if self.config.get('thread_id'):
                    data['message_thread_id'] = self.config['thread_id']
                
                response = await self.client.post('/sendPhoto', data=data, files=files)
                response.raise_for_status()
                
                result_data = response.json()
                if result_data.get('ok'):
                    return MessageResult(
                        status=MessageStatus.SUCCESS,
                        platform=self.platform_name,
                        message_id=str(result_data['result']['message_id'])
                    )
                else:
                    return MessageResult(
                        status=MessageStatus.FAILED,
                        platform=self.platform_name,
                        error=result_data.get('description', 'Unknown error')
                    )
                    
        except Exception as e:
            return MessageResult(
                status=MessageStatus.FAILED,
                platform=self.platform_name,
                error=str(e)
            )
    
    def _get_default_chat_id(self) -> str:
        return self.config['group_id']
    
    def _format_financial_data(self, data: str) -> str:
        """Format financial data for Telegram"""
        return self._format_financial_message(data)
    
    def _format_financial_message(self, data: str) -> str:
        """Format financial data for Telegram - clean Unicode characters that cause 400 errors"""
        import re
        
        if not data:
            return data
        
        # Clean problematic Unicode characters that cause Telegram 400 errors
        # Based on analysis of actual error logs
        text = data
        
        # Replace problematic Unicode characters
        text = text.replace('\u202f', ' ')    # narrow no-break space -> regular space
        text = text.replace('\u200b', '')     # zero-width space -> nothing
        text = text.replace('\u2013', '-')    # en dash -> hyphen
        text = text.replace('\u2014', '-')    # em dash -> hyphen
        text = text.replace('\u2009', ' ')    # thin space -> regular space
        text = text.replace('\u00a0', ' ')    # non-breaking space -> regular space
        text = text.replace('\u2060', '')     # word joiner -> nothing
        text = text.replace('\u200d', '')     # zero-width joiner -> nothing
        text = text.replace('\u200c', '')     # zero-width non-joiner -> nothing
        
        # Replace smart quotes with regular quotes
        text = text.replace('\u201c', '"')    # left double quotation mark
        text = text.replace('\u201d', '"')    # right double quotation mark
        text = text.replace('\u2018', "'")    # left single quotation mark
        text = text.replace('\u2019', "'")    # right single quotation mark
        
        # Remove other control characters except newlines and tabs
        text = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F-\x9F]', '', text)
        
        # Normalize multiple spaces to single spaces
        text = re.sub(r' +', ' ', text)
        
        # Clean up any trailing/leading whitespace on lines
        lines = text.split('\n')
        lines = [line.strip() for line in lines]
        text = '\n'.join(lines)
        
        return text

class UnifiedWhatsAppMessenger(UnifiedBaseMessenger):
    """WhatsApp messenger implementation using Selenium"""
    
    def __init__(self, env_config):
        self.platform = "whatsapp"
        self.env_config = env_config
        self.phone_number = os.getenv('WHATSAPP_PHONE_NUMBER')
        self.group_names = os.getenv('WHATSAPP_GROUP_NAMES', '').split(',')
        
        if not self.phone_number or not self.group_names:
            raise ValueError("WhatsApp phone number and group names required")
        
        super().__init__(self.platform, env_config)
        
        # Import Selenium components
        try:
            # Try to use Playwright WhatsApp messenger instead of Selenium
            from src.messengers.whatsapp_playwright_messenger import WhatsAppPlaywrightMessenger
            self.playwright_available = True
            self.WhatsAppPlaywrightMessenger = WhatsAppPlaywrightMessenger
            
            # Also keep Selenium as fallback
            try:
                from selenium import webdriver
                from selenium.webdriver.common.by import By
                from selenium.webdriver.common.keys import Keys
                from selenium.webdriver.support.ui import WebDriverWait
                from selenium.webdriver.support import expected_conditions as EC
                from selenium.webdriver.chrome.options import Options
                import time
                
                self.selenium_available = True
                self.webdriver = webdriver
                self.By = By
                self.Keys = Keys
                self.WebDriverWait = WebDriverWait
                self.EC = EC
                self.Options = Options
                self.time = time
            except ImportError:
                self.selenium_available = False
                
        except ImportError:
            logger.warning("Neither Playwright nor Selenium available for WhatsApp")
            self.playwright_available = False
            self.selenium_available = False
    
    def _get_platform_config(self) -> Dict[str, Any]:
        """Get WhatsApp platform configuration"""
        return {
            'phone_number': self.phone_number,
            'group_names': self.group_names,
            'max_message_length': 4096,
            'rate_limit_delay': 2.0
        }
    
    async def _initialize_client(self):
        """Initialize WhatsApp client (no-op for Selenium)"""
        self.client = True  # Dummy client for compatibility
    
    async def _send_text_message(self, message: str, **kwargs) -> MessageResult:
        """Send text message via WhatsApp Web"""
        # Try Playwright first
        if self.playwright_available:
            try:
                playwright_messenger = self.WhatsAppPlaywrightMessenger(self.env_config)
                return await playwright_messenger.send_message(message, **kwargs)
            except Exception as e:
                logger.warning(f"Playwright WhatsApp failed, falling back to Selenium: {e}")
        
        # Fallback to Selenium
        if not self.selenium_available:
            return MessageResult(
                status=MessageStatus.FAILED,
                platform=self.platform,
                error="Neither Playwright nor Selenium available for WhatsApp"
            )
        
        try:
            # Use existing session if available
            session_path = Path(__file__).parent.parent.parent / 'browser_sessions' / 'whatsapp_session'
            session_path.mkdir(parents=True, exist_ok=True)
            
            chrome_options = self.Options()
            chrome_options.add_argument(f"user-data-dir={session_path}")
            chrome_options.add_argument("--headless")
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            
            # Use webdriver-manager to automatically handle Chrome driver
            try:
                from webdriver_manager.chrome import ChromeDriverManager
                from selenium.webdriver.chrome.service import Service
                
                service = Service(ChromeDriverManager().install())
                driver = self.webdriver.Chrome(service=service, options=chrome_options)
            except ImportError:
                # Fallback to default Chrome driver
                driver = self.webdriver.Chrome(options=chrome_options)
            driver.get("https://web.whatsapp.com")
            
            # Wait for WhatsApp to load
            wait = self.WebDriverWait(driver, 30)
            
            # Send to each group
            for group_name in self.group_names:
                if not group_name.strip():
                    continue
                    
                try:
                    # Search for group
                    search_box = wait.until(
                        self.EC.presence_of_element_located((self.By.XPATH, '//div[@contenteditable="true"][@data-tab="3"]'))
                    )
                    search_box.clear()
                    search_box.send_keys(group_name.strip())
                    self.time.sleep(2)
                    
                    # Click on group
                    group = wait.until(
                        self.EC.element_to_be_clickable((self.By.XPATH, f'//span[@title="{group_name.strip()}"]'))
                    )
                    group.click()
                    
                    # Find message input box
                    message_box = wait.until(
                        self.EC.presence_of_element_located((self.By.XPATH, '//div[@contenteditable="true"][@data-tab="10"]'))
                    )
                    
                    # Send message
                    for line in message.split('\n'):
                        message_box.send_keys(line)
                        message_box.send_keys(self.Keys.SHIFT + self.Keys.ENTER)
                    message_box.send_keys(self.Keys.ENTER)
                    
                    self.time.sleep(1)
                    
                except Exception as e:
                    logger.error(f"Failed to send to group {group_name}: {e}")
            
            driver.quit()
            
            return MessageResult(
                status=MessageStatus.SUCCESS,
                platform=self.platform,
                message_id=f"whatsapp_{datetime.now().timestamp()}",
                timestamp=datetime.now()
            )
            
        except Exception as e:
            logger.error(f"WhatsApp send failed: {e}")
            return MessageResult(
                status=MessageStatus.FAILED,
                platform=self.platform,
                error=str(e)
            )
    
    async def _send_attachment(self, attachment: AttachmentData, **kwargs) -> MessageResult:
        """Send attachment via WhatsApp (placeholder)"""
        # For now, just send filename as text
        return await self._send_text_message(f"[Attachment: {attachment.filename or attachment.file_path.name}]", **kwargs)
    
    def _get_default_chat_id(self) -> str:
        """Get default chat ID (first group name)"""
        return self.group_names[0] if self.group_names else ""
    
    def _format_financial_data(self, data: str) -> str:
        """Format financial data for WhatsApp"""
        return data

class UnifiedSignalMessenger(UnifiedBaseMessenger):
    """Unified Signal messenger implementation"""
    
    def __init__(self, env_config: EnvironmentConfig):
        super().__init__('signal', env_config)
    
    def _get_platform_config(self) -> Dict[str, Any]:
        return {
            'phone_number': self.credentials['SIGNAL_PHONE_NUMBER'],
            'group_id': self.credentials['SIGNAL_GROUP_ID'],
            'api_url': self.credentials.get('SIGNAL_API_URL', 'http://localhost:8080'),
            'max_message_length': 2000,  # Conservative limit
            'rate_limit_delay': 2.0
        }
    
    async def _initialize_client(self):
        """Initialize Signal HTTP client"""
        self.client = httpx.AsyncClient(
            base_url=self.config['api_url'],
            timeout=30.0
        )
    
    async def _send_text_message(self, message: str, chat_id: Optional[str] = None, **kwargs) -> MessageResult:
        """Send text message via Signal CLI API"""
        try:
            target_group = chat_id or self.config['group_id']
            
            # Check group membership status before sending
            await self._check_and_fix_group_membership(target_group)
            
            # Ensure proper JSON formatting for v2 API
            payload = {
                "number": str(self.config['phone_number']).strip('"\''),
                "recipients": [str(target_group).strip('"\'')],
                "message": str(message)
            }
            
            logger.info(f"Sending Signal message to group {target_group} from {self.config['phone_number']}")
            response = await self.client.post('/v2/send', json=payload)
            
            if response.status_code == 201:
                result_data = response.json()
                logger.info(f"Signal message sent successfully: {result_data.get('timestamp')}")
                return MessageResult(
                    status=MessageStatus.SUCCESS,
                    platform=self.platform_name,
                    message_id=f"signal_{result_data.get('timestamp', datetime.now().timestamp())}",
                    metadata={'group_id': target_group}
                )
            elif response.status_code == 400 and "Untrusted Identity" in response.text:
                # Handle untrusted identity error
                logger.warning(f"Untrusted identity detected in Signal response: {response.text}")
                
                # Try to trust the identity and resend
                if await self._handle_untrusted_identity(response.text):
                    # Retry sending after trusting identity
                    logger.info("Retrying Signal message after trusting identity...")
                    retry_response = await self.client.post('/v2/send', json=payload)
                    
                    if retry_response.status_code == 201:
                        result_data = retry_response.json()
                        return MessageResult(
                            status=MessageStatus.SUCCESS,
                            platform=self.platform_name,
                            message_id=f"signal_{result_data.get('timestamp', datetime.now().timestamp())}",
                            metadata={'group_id': target_group, 'identity_trusted': True}
                        )
                    else:
                        return MessageResult(
                            status=MessageStatus.FAILED,
                            platform=self.platform_name,
                            error=f"Failed after trusting identity: HTTP {retry_response.status_code}: {retry_response.text}"
                        )
                else:
                    return MessageResult(
                        status=MessageStatus.FAILED,
                        platform=self.platform_name,
                        error=f"Untrusted identity could not be resolved: {response.text}"
                    )
            else:
                logger.error(f"Signal message failed with status {response.status_code}: {response.text[:200]}")
                return MessageResult(
                    status=MessageStatus.FAILED,
                    platform=self.platform_name,
                    error=f"HTTP {response.status_code}: {response.text[:200]}"
                )
            
        except httpx.HTTPStatusError as e:
            return MessageResult(
                status=MessageStatus.FAILED,
                platform=self.platform_name,
                error=f"Signal API error: {e}"
            )
        except Exception as e:
            return MessageResult(
                status=MessageStatus.FAILED,
                platform=self.platform_name,
                error=str(e)
            )
    
    async def _send_attachment(self, attachment: AttachmentData, chat_id: Optional[str] = None, **kwargs) -> MessageResult:
        """Send attachment via Signal CLI API"""
        try:
            target_group = chat_id or self.config['group_id']
            
            with open(attachment.file_path, 'rb') as f:
                files = {'attachment': f}
                data = {
                    'number': self.config['phone_number'],
                    'recipients': [target_group],
                    'message': attachment.caption or ''
                }
                
                response = await self.client.post('/v2/send', data=data, files=files)
                
                if response.status_code in [200, 201]:
                    return MessageResult(
                        status=MessageStatus.SUCCESS,
                        platform=self.platform_name,
                        message_id=f"signal_attachment_{datetime.now().timestamp()}"
                    )
                elif response.status_code == 400 and "Untrusted Identity" in response.text:
                    # Handle untrusted identity error
                    logger.warning(f"Untrusted identity detected in Signal attachment response: {response.text}")
                    
                    if await self._handle_untrusted_identity(response.text):
                        # Retry sending after trusting identity
                        logger.info("Retrying Signal attachment after trusting identity...")
                        with open(attachment.file_path, 'rb') as f:
                            files = {'attachment': f}
                            retry_response = await self.client.post('/v2/send', data=data, files=files)
                            
                            if retry_response.status_code in [200, 201]:
                                return MessageResult(
                                    status=MessageStatus.SUCCESS,
                                    platform=self.platform_name,
                                    message_id=f"signal_attachment_{datetime.now().timestamp()}",
                                    metadata={'identity_trusted': True}
                                )
                            else:
                                return MessageResult(
                                    status=MessageStatus.FAILED,
                                    platform=self.platform_name,
                                    error=f"Failed after trusting identity: HTTP {retry_response.status_code}: {retry_response.text}"
                                )
                    else:
                        return MessageResult(
                            status=MessageStatus.FAILED,
                            platform=self.platform_name,
                            error=f"Untrusted identity could not be resolved: {response.text}"
                        )
                else:
                    response.raise_for_status()
                    return MessageResult(
                        status=MessageStatus.FAILED,
                        platform=self.platform_name,
                        error=f"HTTP {response.status_code}: {response.text}"
                    )
                
        except Exception as e:
            return MessageResult(
                status=MessageStatus.FAILED,
                platform=self.platform_name,
                error=str(e)
            )
    
    def _get_default_chat_id(self) -> str:
        return self.config['group_id']
    
    def _format_financial_data(self, data: str) -> str:
        """Format financial data for Signal"""
        return data
    
    async def _check_and_fix_group_membership(self, group_id: str) -> bool:
        """Check if sender is properly in the group and fix if needed"""
        try:
            # Get group information
            response = await self.client.get(f"/v1/groups/{self.config['phone_number']}")
            if response.status_code != 200:
                logger.warning(f"Could not get group info: {response.status_code}")
                return False
            
            groups = response.json()
            for group in groups:
                if group.get('id') == group_id:
                    # Check if our number is in pending_requests
                    if self.config['phone_number'] in group.get('pending_requests', []):
                        logger.warning(f"Signal number {self.config['phone_number']} has pending request in group {group_id}")
                        logger.info("Note: Group admin needs to accept the pending request manually in Signal app")
                        # We can't auto-accept our own request, but we can still try sending
                        return True
                    
                    # Check if we're a proper member
                    members = group.get('members', [])
                    if self.config['phone_number'] in members or any(self.config['phone_number'] in str(m) for m in members):
                        logger.debug(f"Signal number {self.config['phone_number']} is a member of group {group_id}")
                        return True
                    
                    # Check if we're an admin
                    if self.config['phone_number'] in group.get('admins', []):
                        logger.debug(f"Signal number {self.config['phone_number']} is an admin of group {group_id}")
                        return True
                    
                    logger.warning(f"Signal number {self.config['phone_number']} is not properly in group {group_id}")
                    return False
            
            logger.warning(f"Group {group_id} not found")
            return False
            
        except Exception as e:
            logger.error(f"Error checking group membership: {e}")
            # Continue anyway
            return True
    
    async def _handle_untrusted_identity(self, error_text: str) -> bool:
        """Handle untrusted identity error by attempting to trust the identity"""
        try:
            # Extract UUID from error message
            import re
            uuid_match = re.search(r'"([a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12})"', error_text)
            
            if not uuid_match:
                logger.error("Could not extract UUID from untrusted identity error")
                return False
            
            uuid = uuid_match.group(1)
            logger.info(f"Attempting to trust identity UUID: {uuid}")
            
            # Try different trust endpoint formats
            trust_endpoints = [
                f"/v1/identities/{self.config['phone_number']}/trust/{uuid}",
                f"/v1/identities/{self.config['phone_number']}/trust",
                f"/v2/identities/{self.config['phone_number']}/trust/{uuid}",
            ]
            
            for endpoint in trust_endpoints:
                try:
                    # Try PUT request
                    response = await self.client.put(endpoint)
                    if response.status_code in [200, 201, 204]:
                        logger.info(f"Successfully trusted identity via PUT {endpoint}")
                        return True
                    
                    # Try POST request with JSON body
                    response = await self.client.post(
                        endpoint,
                        json={"trust_all_known_keys": True, "verified_safety_number": uuid}
                    )
                    if response.status_code in [200, 201, 204]:
                        logger.info(f"Successfully trusted identity via POST {endpoint}")
                        return True
                except Exception as e:
                    logger.debug(f"Trust attempt failed for {endpoint}: {e}")
                    continue
            
            # If API trust fails, log for manual intervention
            logger.error(f"Could not automatically trust identity {uuid}. Manual intervention may be required.")
            logger.info("To manually trust this identity, run:")
            logger.info(f"docker exec signal-api signal-cli trust {self.config['phone_number']} -a {uuid}")
            
            return False
            
        except Exception as e:
            logger.error(f"Error handling untrusted identity: {e}")
            return False

class UnifiedMultiMessenger:
    """
    Multi-platform messenger that sends to all configured platforms
    Consolidates the functionality of multiple messenger implementations
    """
    
    def __init__(self, platforms: Optional[List[str]] = None):
        """
        Initialize multi-messenger
        
        Args:
            platforms: List of platforms to use ('telegram', 'signal', 'whatsapp')
        """
        self.env_config = EnvironmentConfig('daily_report')
        self.platforms = platforms or ['telegram', 'signal']  # WhatsApp optional
        self.messengers = {}
        
        # Initialize messengers for each platform
        for platform in self.platforms:
            try:
                if platform == 'telegram':
                    self.messengers[platform] = UnifiedTelegramMessenger(self.env_config)
                elif platform == 'signal':
                    self.messengers[platform] = UnifiedSignalMessenger(self.env_config)
                elif platform == 'whatsapp':
                    # Use Playwright implementation with group ID support
                    from .whatsapp_playwright_messenger import WhatsAppPlaywrightMessenger
                    self.messengers[platform] = WhatsAppPlaywrightMessenger(self.env_config)
                else:
                    logger.warning(f"Unknown platform: {platform}")
            except Exception as e:
                logger.error(f"Failed to initialize {platform} messenger: {e}")
        
        logger.info(f"🚀 MultiMessenger initialized with platforms: {list(self.messengers.keys())}")
    
    async def send_to_all(self, message: str, **kwargs) -> Dict[str, MessageResult]:
        """Send message to all configured platforms"""
        results = {}
        
        # Send to all platforms concurrently
        tasks = [
            self._send_to_platform(platform, messenger, message, **kwargs)
            for platform, messenger in self.messengers.items()
        ]
        
        platform_results = await asyncio.gather(*tasks, return_exceptions=True)
        
        for (platform, _), result in zip(self.messengers.items(), platform_results):
            if isinstance(result, Exception):
                results[platform] = MessageResult(
                    status=MessageStatus.FAILED,
                    platform=platform,
                    error=str(result)
                )
            else:
                results[platform] = result
        
        # Log summary
        success_count = sum(1 for r in results.values() if r.success)
        logger.info(f"📊 Message delivery: {success_count}/{len(results)} platforms successful")
        
        return results
    
    async def _send_to_platform(self, platform: str, messenger: UnifiedBaseMessenger, message: str, **kwargs) -> MessageResult:
        """Send message to specific platform"""
        try:
            return await messenger.send_message(message, **kwargs)
        except Exception as e:
            logger.error(f"Failed to send to {platform}: {e}")
            return MessageResult(
                status=MessageStatus.FAILED,
                platform=platform,
                error=str(e)
            )
    
    async def send_structured_financial_data(self, structured_data: str, **kwargs) -> Dict[str, MessageResult]:
        """Send structured financial data to all platforms"""
        results = {}
        
        tasks = [
            messenger.send_structured_financial_data(structured_data, **kwargs)
            for messenger in self.messengers.values()
        ]
        
        platform_results = await asyncio.gather(*tasks, return_exceptions=True)
        
        for (platform, _), result in zip(self.messengers.items(), platform_results):
            if isinstance(result, Exception):
                results[platform] = MessageResult(
                    status=MessageStatus.FAILED,
                    platform=platform,
                    error=str(result)
                )
            else:
                results[platform] = result
        
        return results
    
    async def send_attachment(self, file_path: str, caption: Optional[str] = None, **kwargs) -> Dict[str, MessageResult]:
        """Send single attachment to all platforms"""
        attachment = AttachmentData(
            file_path=Path(file_path),
            caption=caption
        )
        
        results = {}
        
        for platform, messenger in self.messengers.items():
            try:
                result = await messenger.send_attachment(attachment, **kwargs)
                results[platform] = result
            except Exception as e:
                results[platform] = MessageResult(
                    status=MessageStatus.FAILED,
                    platform=platform,
                    error=str(e)
                )
        
        return results
    
    async def send_attachments(self, attachments: List[AttachmentData], **kwargs) -> Dict[str, List[MessageResult]]:
        """Send attachments to all platforms"""
        results = {}
        
        for platform, messenger in self.messengers.items():
            platform_results = []
            for attachment in attachments:
                result = await messenger.send_attachment(attachment, **kwargs)
                platform_results.append(result)
            results[platform] = platform_results
        
        return results
    
    async def cleanup(self):
        """Clean up all messenger resources"""
        for messenger in self.messengers.values():
            await messenger.cleanup()

# Convenience functions for backwards compatibility
async def send_structured_financial_data(structured_data: str, **kwargs) -> Dict[str, MessageResult]:
    """Convenience function to send structured financial data"""
    multi_messenger = UnifiedMultiMessenger()
    try:
        return await multi_messenger.send_structured_financial_data(structured_data, **kwargs)
    finally:
        await multi_messenger.cleanup()

async def send_to_both_messengers(message: str, **kwargs) -> Dict[str, MessageResult]:
    """Convenience function for backwards compatibility"""
    multi_messenger = UnifiedMultiMessenger()
    try:
        return await multi_messenger.send_to_all(message, **kwargs)
    finally:
        await multi_messenger.cleanup()

if __name__ == "__main__":
    async def main():
        """Test the unified messenger system"""
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
        
        try:
            # Test multi-messenger
            multi_messenger = UnifiedMultiMessenger()
            
            test_message = "🧪 Testing unified messenger system"
            results = await multi_messenger.send_to_all(test_message)
            
            for platform, result in results.items():
                status = "✅ SUCCESS" if result.success else "❌ FAILED"
                print(f"{platform}: {status}")
                if result.error:
                    print(f"  Error: {result.error}")
            
            await multi_messenger.cleanup()
            
        except Exception as e:
            print(f"❌ Test error: {e}")
    
    asyncio.run(main())