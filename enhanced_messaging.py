#!/usr/bin/env python3
"""
Enhanced Messaging System with Comprehensive Error Handling
Implements resilient messaging with fallback strategies, retry queues, and delivery confirmation
"""

import asyncio
import logging
import json
import time
import hashlib
from typing import Dict, Any, List, Optional, Union
from datetime import datetime, timedelta
from pathlib import Path
from dataclasses import dataclass, field
from enum import Enum
import aiohttp
import aiofiles

from enhanced_error_handler import (
    EnhancedErrorHandler, ErrorContext, ErrorCategory, ErrorSeverity,
    resilient_operation, MessageResult, MessageStatus
)

logger = logging.getLogger(__name__)


class MessagePriority(str, Enum):
    """Message priority levels"""
    CRITICAL = "CRITICAL"    # Financial alerts, system failures
    HIGH = "HIGH"           # Important updates, warnings
    MEDIUM = "MEDIUM"       # Regular reports, notifications
    LOW = "LOW"            # Debug info, status updates


class DeliveryMethod(str, Enum):
    """Available delivery methods"""
    SIGNAL = "SIGNAL"
    TELEGRAM = "TELEGRAM"
    EMAIL = "EMAIL"         # Fallback method
    SMS = "SMS"             # Emergency fallback
    WEBHOOK = "WEBHOOK"     # Alternative delivery


@dataclass
class QueuedMessage:
    """Message queued for delivery"""
    id: str
    content: str
    priority: MessagePriority
    delivery_methods: List[DeliveryMethod]
    created_at: datetime = field(default_factory=datetime.now)
    retry_count: int = 0
    max_retries: int = 5
    next_retry: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    financial_data: bool = False


@dataclass
class DeliveryAttempt:
    """Record of a delivery attempt"""
    message_id: str
    method: DeliveryMethod
    timestamp: datetime
    success: bool
    error_message: Optional[str] = None
    response_data: Optional[Dict[str, Any]] = None


class MessageQueue:
    """Persistent message queue with retry logic"""
    
    def __init__(self, queue_file: str = "logs/message_queue.json"):
        self.queue_file = Path(queue_file)
        self.queue_file.parent.mkdir(exist_ok=True)
        self.messages: Dict[str, QueuedMessage] = {}
        self.delivery_history: List[DeliveryAttempt] = []
        self._load_queue()
    
    def _load_queue(self):
        """Load queue from persistent storage"""
        try:
            if self.queue_file.exists():
                with open(self.queue_file, 'r') as f:
                    data = json.load(f)
                    
                # Reconstruct QueuedMessage objects
                for msg_id, msg_data in data.get('messages', {}).items():
                    msg_data['created_at'] = datetime.fromisoformat(msg_data['created_at'])
                    if msg_data.get('next_retry'):
                        msg_data['next_retry'] = datetime.fromisoformat(msg_data['next_retry'])
                    
                    self.messages[msg_id] = QueuedMessage(**msg_data)
                
                # Load delivery history
                for attempt_data in data.get('delivery_history', []):
                    attempt_data['timestamp'] = datetime.fromisoformat(attempt_data['timestamp'])
                    self.delivery_history.append(DeliveryAttempt(**attempt_data))
                
                logger.info(f"Loaded {len(self.messages)} queued messages")
        except Exception as e:
            logger.error(f"Failed to load message queue: {e}")
    
    def _save_queue(self):
        """Save queue to persistent storage"""
        try:
            data = {
                'messages': {},
                'delivery_history': []
            }
            
            # Convert QueuedMessage objects to dict
            for msg_id, msg in self.messages.items():
                msg_dict = {
                    'id': msg.id,
                    'content': msg.content,
                    'priority': msg.priority.value,
                    'delivery_methods': [m.value for m in msg.delivery_methods],
                    'created_at': msg.created_at.isoformat(),
                    'retry_count': msg.retry_count,
                    'max_retries': msg.max_retries,
                    'next_retry': msg.next_retry.isoformat() if msg.next_retry else None,
                    'metadata': msg.metadata,
                    'financial_data': msg.financial_data
                }
                data['messages'][msg_id] = msg_dict
            
            # Convert delivery history
            for attempt in self.delivery_history[-100:]:  # Keep last 100 attempts
                attempt_dict = {
                    'message_id': attempt.message_id,
                    'method': attempt.method.value,
                    'timestamp': attempt.timestamp.isoformat(),
                    'success': attempt.success,
                    'error_message': attempt.error_message,
                    'response_data': attempt.response_data
                }
                data['delivery_history'].append(attempt_dict)
            
            with open(self.queue_file, 'w') as f:
                json.dump(data, f, indent=2)
                
        except Exception as e:
            logger.error(f"Failed to save message queue: {e}")
    
    def add_message(self, content: str, priority: MessagePriority,
                   delivery_methods: List[DeliveryMethod],
                   financial_data: bool = False,
                   metadata: Optional[Dict[str, Any]] = None) -> str:
        """Add message to queue"""
        message_id = hashlib.md5(f"{content}{time.time()}".encode()).hexdigest()
        
        message = QueuedMessage(
            id=message_id,
            content=content,
            priority=priority,
            delivery_methods=delivery_methods,
            financial_data=financial_data,
            metadata=metadata or {}
        )
        
        self.messages[message_id] = message
        self._save_queue()
        
        logger.info(f"Added message to queue: {message_id} (priority: {priority.value})")
        return message_id
    
    def get_pending_messages(self) -> List[QueuedMessage]:
        """Get messages that are ready for delivery"""
        now = datetime.now()
        pending = []
        
        for message in self.messages.values():
            if message.retry_count < message.max_retries:
                if message.next_retry is None or message.next_retry <= now:
                    pending.append(message)
        
        # Sort by priority and creation time
        priority_order = {
            MessagePriority.CRITICAL: 0,
            MessagePriority.HIGH: 1,
            MessagePriority.MEDIUM: 2,
            MessagePriority.LOW: 3
        }
        
        pending.sort(key=lambda m: (priority_order[m.priority], m.created_at))
        return pending
    
    def mark_delivered(self, message_id: str, method: DeliveryMethod, success: bool,
                      error_message: Optional[str] = None,
                      response_data: Optional[Dict[str, Any]] = None):
        """Mark message delivery attempt"""
        attempt = DeliveryAttempt(
            message_id=message_id,
            method=method,
            timestamp=datetime.now(),
            success=success,
            error_message=error_message,
            response_data=response_data
        )
        
        self.delivery_history.append(attempt)
        
        if message_id in self.messages:
            message = self.messages[message_id]
            
            if success:
                # Remove from queue on successful delivery
                del self.messages[message_id]
                logger.info(f"Message {message_id} delivered successfully via {method.value}")
            else:
                # Schedule retry
                message.retry_count += 1
                if message.retry_count < message.max_retries:
                    # Exponential backoff
                    delay_minutes = 2 ** message.retry_count
                    message.next_retry = datetime.now() + timedelta(minutes=delay_minutes)
                    logger.warning(f"Message {message_id} failed via {method.value}, retry in {delay_minutes} minutes")
                else:
                    # Max retries exceeded
                    del self.messages[message_id]
                    logger.error(f"Message {message_id} failed permanently after {message.max_retries} attempts")
            
            self._save_queue()
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get queue statistics"""
        now = datetime.now()
        recent_attempts = [a for a in self.delivery_history 
                          if (now - a.timestamp).total_seconds() < 86400]  # Last 24 hours
        
        success_rate = (
            sum(1 for a in recent_attempts if a.success) / len(recent_attempts)
            if recent_attempts else 0
        )
        
        return {
            'queued_messages': len(self.messages),
            'pending_messages': len([m for m in self.messages.values() 
                                   if m.next_retry is None or m.next_retry <= now]),
            'failed_messages': len([m for m in self.messages.values() 
                                  if m.retry_count >= m.max_retries]),
            'recent_attempts': len(recent_attempts),
            'success_rate_24h': success_rate,
            'delivery_methods_used': list(set(a.method.value for a in recent_attempts))
        }


class EnhancedSignalMessenger:
    """Enhanced Signal messenger with comprehensive error handling"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.api_url = config.get('api_url', 'http://localhost:8080')
        self.phone_number = config.get('phone_number')
        self.group_id = config.get('group_id')
        self.send_timeout = config.get('send_timeout', 30)
        self.error_handler = EnhancedErrorHandler()
        
        # Connection health tracking
        self.last_health_check = None
        self.health_check_interval = 300  # 5 minutes
        self.is_healthy = True
    
    @resilient_operation(
        category=ErrorCategory.MESSAGING,
        severity=ErrorSeverity.HIGH,
        component="signal_messenger",
        financial_data=True
    )
    async def send_message(self, message: str, **kwargs) -> MessageResult:
        """Send message with enhanced error handling"""
        if not self._is_configured():
            return MessageResult(
                status=MessageStatus.FAILED,
                error="Signal not configured",
                platform="signal"
            )
        
        # Health check
        if not await self._ensure_service_health():
            return MessageResult(
                status=MessageStatus.FAILED,
                error="Signal service unhealthy",
                platform="signal"
            )
        
        try:
            # Prepare request
            url = f"{self.api_url}/v2/send"
            payload = {
                "number": self.phone_number,
                "message": message,
                "recipients": [self.group_id] if self.group_id else []
            }
            
            # Send with timeout and retry
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    url, 
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=self.send_timeout)
                ) as response:
                    
                    if response.status == 201:
                        response_data = await response.json()
                        return MessageResult(
                            status=MessageStatus.SUCCESS,
                            message_id=str(response_data.get('timestamp', '')),
                            platform="signal",
                            metadata={'response': response_data}
                        )
                    else:
                        error_text = await response.text()
                        return MessageResult(
                            status=MessageStatus.FAILED,
                            error=f"Signal API error {response.status}: {error_text}",
                            platform="signal"
                        )
        
        except asyncio.TimeoutError:
            self.is_healthy = False
            return MessageResult(
                status=MessageStatus.FAILED,
                error=f"Signal API timeout after {self.send_timeout}s",
                platform="signal"
            )
        
        except Exception as e:
            return MessageResult(
                status=MessageStatus.FAILED,
                error=f"Signal send error: {e}",
                platform="signal"
            )
    
    async def _ensure_service_health(self) -> bool:
        """Ensure Signal service is healthy"""
        now = datetime.now()
        
        # Check if health check is needed
        if (self.last_health_check is None or 
            (now - self.last_health_check).total_seconds() > self.health_check_interval):
            
            self.is_healthy = await self._health_check()
            self.last_health_check = now
        
        return self.is_healthy
    
    async def _health_check(self) -> bool:
        """Perform health check on Signal service"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.api_url}/v1/health",
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    return response.status in [200, 204]
        except Exception:
            return False
    
    def _is_configured(self) -> bool:
        """Check if properly configured"""
        return bool(self.phone_number and self.group_id)


class EnhancedTelegramMessenger:
    """Enhanced Telegram messenger with comprehensive error handling"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.bot_token = config.get('bot_token')
        self.chat_id = config.get('chat_id')
        self.error_handler = EnhancedErrorHandler()
        
        # Rate limiting
        self.last_request = 0
        self.min_interval = 1.0  # Minimum seconds between requests
    
    @resilient_operation(
        category=ErrorCategory.MESSAGING,
        severity=ErrorSeverity.HIGH,
        component="telegram_messenger",
        financial_data=True
    )
    async def send_message(self, message: str, **kwargs) -> MessageResult:
        """Send message with enhanced error handling"""
        if not self._is_configured():
            return MessageResult(
                status=MessageStatus.FAILED,
                error="Telegram not configured",
                platform="telegram"
            )
        
        # Rate limiting
        await self._respect_rate_limits()
        
        try:
            url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
            payload = {
                'chat_id': self.chat_id,
                'text': message,
                'parse_mode': kwargs.get('parse_mode', None),
                'disable_web_page_preview': True
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=payload) as response:
                    if response.status == 200:
                        response_data = await response.json()
                        return MessageResult(
                            status=MessageStatus.SUCCESS,
                            message_id=str(response_data['result']['message_id']),
                            platform="telegram",
                            metadata={'response': response_data}
                        )
                    else:
                        error_text = await response.text()
                        
                        # Handle rate limiting
                        if response.status == 429:
                            retry_after = response.headers.get('Retry-After', 60)
                            return MessageResult(
                                status=MessageStatus.FAILED,
                                error=f"Rate limited, retry after {retry_after}s",
                                platform="telegram"
                            )
                        
                        return MessageResult(
                            status=MessageStatus.FAILED,
                            error=f"Telegram API error {response.status}: {error_text}",
                            platform="telegram"
                        )
        
        except Exception as e:
            return MessageResult(
                status=MessageStatus.FAILED,
                error=f"Telegram send error: {e}",
                platform="telegram"
            )
    
    async def _respect_rate_limits(self):
        """Respect Telegram rate limits"""
        now = time.time()
        elapsed = now - self.last_request
        
        if elapsed < self.min_interval:
            wait_time = self.min_interval - elapsed
            await asyncio.sleep(wait_time)
        
        self.last_request = time.time()
    
    def _is_configured(self) -> bool:
        """Check if properly configured"""
        return bool(self.bot_token and self.chat_id)


class EnhancedMessagingSystem:
    """Enhanced messaging system with queue, fallbacks, and delivery confirmation"""
    
    def __init__(self, config_file: str = "config.json"):
        self.config = self._load_config(config_file)
        self.message_queue = MessageQueue()
        self.error_handler = EnhancedErrorHandler()
        
        # Initialize messengers
        self.messengers = {}
        self._initialize_messengers()
        
        # Background task for processing queue
        self._queue_processor_task = None
        self._running = False
        
        logger.info("Enhanced messaging system initialized")
    
    def _load_config(self, config_file: str) -> Dict[str, Any]:
        """Load configuration"""
        try:
            with open(config_file, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load config: {e}")
            return {}
    
    def _initialize_messengers(self):
        """Initialize available messengers"""
        try:
            # Signal messenger
            signal_config = self.config.get('signal', {})
            if signal_config.get('enabled', True):
                self.messengers[DeliveryMethod.SIGNAL] = EnhancedSignalMessenger(signal_config)
                logger.info("Signal messenger initialized")
        except Exception as e:
            logger.error(f"Failed to initialize Signal messenger: {e}")
        
        try:
            # Telegram messenger
            telegram_config = self.config.get('telegram', {})
            if telegram_config.get('enabled', True):
                self.messengers[DeliveryMethod.TELEGRAM] = EnhancedTelegramMessenger(telegram_config)
                logger.info("Telegram messenger initialized")
        except Exception as e:
            logger.error(f"Failed to initialize Telegram messenger: {e}")
    
    async def send_financial_alert(self, message: str, 
                                 priority: MessagePriority = MessagePriority.HIGH,
                                 immediate: bool = True) -> str:
        """
        Send financial alert with high priority
        
        Args:
            message: Alert message content
            priority: Message priority level
            immediate: Whether to send immediately or queue
            
        Returns:
            Message ID
        """
        delivery_methods = [DeliveryMethod.SIGNAL, DeliveryMethod.TELEGRAM]
        
        message_id = self.message_queue.add_message(
            content=message,
            priority=priority,
            delivery_methods=delivery_methods,
            financial_data=True,
            metadata={'type': 'financial_alert', 'urgent': immediate}
        )
        
        if immediate:
            await self._process_message_immediately(message_id)
        
        return message_id
    
    async def send_heatmap_images(self, categorical_path: str, forex_path: str) -> List[str]:
        """Send heatmap images via available messengers"""
        message_ids = []
        
        # Send categorical heatmap
        cat_message_id = self.message_queue.add_message(
            content="📊 Global Interest Rates - Categorical Analysis",
            priority=MessagePriority.MEDIUM,
            delivery_methods=[DeliveryMethod.SIGNAL, DeliveryMethod.TELEGRAM],
            metadata={'type': 'heatmap', 'file_path': categorical_path}
        )
        message_ids.append(cat_message_id)
        
        # Send forex heatmap
        forex_message_id = self.message_queue.add_message(
            content="🌍 Forex Pairs Differential Matrix",
            priority=MessagePriority.MEDIUM,
            delivery_methods=[DeliveryMethod.SIGNAL, DeliveryMethod.TELEGRAM],
            metadata={'type': 'heatmap', 'file_path': forex_path}
        )
        message_ids.append(forex_message_id)
        
        # Process immediately
        for msg_id in message_ids:
            await self._process_message_immediately(msg_id)
        
        return message_ids
    
    async def _process_message_immediately(self, message_id: str):
        """Process a specific message immediately"""
        if message_id not in self.message_queue.messages:
            logger.error(f"Message {message_id} not found in queue")
            return
        
        message = self.message_queue.messages[message_id]
        
        # Try each delivery method
        for method in message.delivery_methods:
            if method in self.messengers:
                try:
                    result = await self._send_via_messenger(message, method)
                    
                    self.message_queue.mark_delivered(
                        message_id=message_id,
                        method=method,
                        success=result.status == MessageStatus.SUCCESS,
                        error_message=result.error,
                        response_data=result.metadata
                    )
                    
                    if result.status == MessageStatus.SUCCESS:
                        logger.info(f"Message {message_id} sent successfully via {method.value}")
                        return  # Success on first method
                    else:
                        logger.warning(f"Failed to send {message_id} via {method.value}: {result.error}")
                        
                except Exception as e:
                    logger.error(f"Error sending {message_id} via {method.value}: {e}")
                    self.message_queue.mark_delivered(
                        message_id=message_id,
                        method=method,
                        success=False,
                        error_message=str(e)
                    )
    
    async def _send_via_messenger(self, message: QueuedMessage, method: DeliveryMethod) -> MessageResult:
        """Send message via specific messenger"""
        messenger = self.messengers.get(method)
        if not messenger:
            return MessageResult(
                status=MessageStatus.FAILED,
                error=f"Messenger {method.value} not available",
                platform=method.value.lower()
            )
        
        # Handle attachments (heatmaps)
        if message.metadata.get('type') == 'heatmap':
            file_path = message.metadata.get('file_path')
            if file_path and hasattr(messenger, 'send_attachment'):
                return await messenger.send_attachment(file_path, message.content)
        
        # Regular message
        return await messenger.send_message(message.content)
    
    async def start_queue_processor(self):
        """Start background queue processing"""
        if self._running:
            return
        
        self._running = True
        self._queue_processor_task = asyncio.create_task(self._queue_processor())
        logger.info("Queue processor started")
    
    async def stop_queue_processor(self):
        """Stop background queue processing"""
        self._running = False
        if self._queue_processor_task:
            self._queue_processor_task.cancel()
            try:
                await self._queue_processor_task
            except asyncio.CancelledError:
                pass
        logger.info("Queue processor stopped")
    
    async def _queue_processor(self):
        """Background task to process message queue"""
        while self._running:
            try:
                pending_messages = self.message_queue.get_pending_messages()
                
                for message in pending_messages:
                    await self._process_message_immediately(message.id)
                    
                    # Small delay between messages
                    await asyncio.sleep(1)
                
                # Check queue every 30 seconds
                await asyncio.sleep(30)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Queue processor error: {e}")
                await asyncio.sleep(60)  # Wait before retrying
    
    def get_system_status(self) -> Dict[str, Any]:
        """Get comprehensive system status"""
        messenger_status = {}
        for method, messenger in self.messengers.items():
            messenger_status[method.value] = {
                'available': True,
                'configured': messenger._is_configured(),
                'healthy': getattr(messenger, 'is_healthy', True)
            }
        
        queue_stats = self.message_queue.get_statistics()
        
        return {
            'messengers': messenger_status,
            'queue': queue_stats,
            'processor_running': self._running,
            'timestamp': datetime.now().isoformat()
        }
    
    async def send_system_health_report(self):
        """Send system health report"""
        status = self.get_system_status()
        
        # Generate health report
        report_lines = ["🏥 SYSTEM HEALTH REPORT", ""]
        
        # Messenger status
        report_lines.append("📡 MESSENGERS:")
        for method, info in status['messengers'].items():
            status_icon = "✅" if info['configured'] and info['healthy'] else "❌"
            report_lines.append(f"  {status_icon} {method}: {'OK' if info['healthy'] else 'ERROR'}")
        
        # Queue status
        queue = status['queue']
        report_lines.extend([
            "",
            "📬 MESSAGE QUEUE:",
            f"  Queued: {queue['queued_messages']}",
            f"  Pending: {queue['pending_messages']}",
            f"  Success Rate (24h): {queue['success_rate_24h']:.1%}",
            f"  Recent Attempts: {queue['recent_attempts']}"
        ])
        
        report_content = "\n".join(report_lines)
        
        await self.send_financial_alert(
            message=report_content,
            priority=MessagePriority.LOW,
            immediate=True
        )


# Global enhanced messaging instance
enhanced_messaging = EnhancedMessagingSystem()


async def main():
    """Test the enhanced messaging system"""
    print("🧪 Testing Enhanced Messaging System...")
    
    # Start queue processor
    await enhanced_messaging.start_queue_processor()
    
    try:
        # Send test financial alert
        message_id = await enhanced_messaging.send_financial_alert(
            "🚨 TEST ALERT: Enhanced messaging system operational",
            priority=MessagePriority.HIGH
        )
        print(f"Sent test alert: {message_id}")
        
        # Get system status
        status = enhanced_messaging.get_system_status()
        print(f"\nSystem Status: {json.dumps(status, indent=2)}")
        
        # Wait for processing
        await asyncio.sleep(5)
        
        # Send health report
        await enhanced_messaging.send_system_health_report()
        print("Health report sent")
        
    finally:
        # Stop queue processor
        await enhanced_messaging.stop_queue_processor()


if __name__ == "__main__":
    asyncio.run(main())