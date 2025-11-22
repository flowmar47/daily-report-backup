"""
Stock Alert Sender - Integrates with existing messaging infrastructure

Sends formatted stock alerts to Signal and Telegram groups
using the same infrastructure as the forex signals system.
"""

import asyncio
import logging
from typing import List, Dict, Optional, Any

import httpx

from ..core.config import get_stock_settings
from ..data.models import VolumeAlert, ExtendedHoursAlert
from .formatter import StockAlertFormatter

logger = logging.getLogger(__name__)


class StockAlertSender:
    """Sends stock alerts to Signal and Telegram"""

    def __init__(self):
        self.settings = get_stock_settings()
        self.formatter = StockAlertFormatter()

        # HTTP client for async requests
        self._client: Optional[httpx.AsyncClient] = None

    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create async HTTP client"""
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(timeout=30.0)
        return self._client

    async def close(self):
        """Close HTTP client"""
        if self._client and not self._client.is_closed:
            await self._client.aclose()

    async def send_telegram(self, message: str) -> bool:
        """
        Send message via Telegram

        Args:
            message: Message text to send

        Returns:
            True if successful, False otherwise
        """
        bot_token = self.settings.telegram_bot_token
        group_id = self.settings.telegram_group_id

        if not bot_token or not group_id:
            logger.warning("Telegram not configured, skipping")
            return False

        try:
            client = await self._get_client()

            url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
            payload = {
                "chat_id": group_id,
                "text": message,
                "parse_mode": "HTML" if "<" in message else None
            }

            response = await client.post(url, json=payload)

            if response.status_code == 200:
                result = response.json()
                if result.get('ok'):
                    logger.info("Message sent to Telegram successfully")
                    return True
                else:
                    logger.error(f"Telegram API error: {result.get('description')}")
                    return False
            else:
                logger.error(f"Telegram HTTP error: {response.status_code}")
                return False

        except Exception as e:
            logger.error(f"Error sending to Telegram: {e}")
            return False

    async def send_signal(self, message: str) -> bool:
        """
        Send message via Signal

        Args:
            message: Message text to send

        Returns:
            True if successful, False otherwise
        """
        phone = self.settings.signal_phone_number
        group_id = self.settings.signal_group_id
        cli_url = self.settings.signal_cli_url

        if not phone or not group_id:
            logger.warning("Signal not configured, skipping")
            return False

        try:
            client = await self._get_client()

            url = f"{cli_url}/v2/send"
            payload = {
                "number": phone,
                "recipients": [group_id],
                "message": message
            }

            response = await client.post(url, json=payload)

            if response.status_code in [200, 201]:
                logger.info("Message sent to Signal successfully")
                return True
            else:
                logger.error(f"Signal HTTP error: {response.status_code}")
                return False

        except Exception as e:
            logger.error(f"Error sending to Signal: {e}")
            return False

    async def send_to_all(self, message: str) -> Dict[str, bool]:
        """
        Send message to all configured platforms concurrently

        Args:
            message: Message text to send

        Returns:
            Dict mapping platform name to success status
        """
        results = {}

        # Run sends concurrently
        telegram_task = asyncio.create_task(self.send_telegram(message))
        signal_task = asyncio.create_task(self.send_signal(message))

        results['telegram'] = await telegram_task
        results['signal'] = await signal_task

        # Log summary
        successful = [k for k, v in results.items() if v]
        failed = [k for k, v in results.items() if not v]

        if successful:
            logger.info(f"Successfully sent to: {', '.join(successful)}")
        if failed:
            logger.warning(f"Failed to send to: {', '.join(failed)}")

        return results

    async def send_volume_alerts(
        self,
        alerts: List[VolumeAlert],
        platforms: Optional[List[str]] = None
    ) -> Dict[str, bool]:
        """
        Format and send volume alerts

        Args:
            alerts: List of VolumeAlert objects
            platforms: Optional list of platforms ('telegram', 'signal')

        Returns:
            Dict mapping platform to success status
        """
        if not alerts:
            logger.info("No volume alerts to send")
            return {}

        message = self.formatter.format_volume_alerts(alerts)

        if platforms is None:
            return await self.send_to_all(message)

        results = {}
        if 'telegram' in platforms:
            results['telegram'] = await self.send_telegram(message)
        if 'signal' in platforms:
            results['signal'] = await self.send_signal(message)

        return results

    async def send_extended_hours_alerts(
        self,
        alerts: List[ExtendedHoursAlert],
        platforms: Optional[List[str]] = None
    ) -> Dict[str, bool]:
        """
        Format and send extended hours alerts

        Args:
            alerts: List of ExtendedHoursAlert objects
            platforms: Optional list of platforms

        Returns:
            Dict mapping platform to success status
        """
        if not alerts:
            logger.info("No extended hours alerts to send")
            return {}

        message = self.formatter.format_extended_hours_alerts(alerts)

        if platforms is None:
            return await self.send_to_all(message)

        results = {}
        if 'telegram' in platforms:
            results['telegram'] = await self.send_telegram(message)
        if 'signal' in platforms:
            results['signal'] = await self.send_signal(message)

        return results

    async def send_combined_alerts(
        self,
        volume_alerts: List[VolumeAlert],
        extended_alerts: List[ExtendedHoursAlert],
        platforms: Optional[List[str]] = None
    ) -> Dict[str, bool]:
        """
        Format and send combined volume and extended hours alerts

        Args:
            volume_alerts: List of VolumeAlert objects
            extended_alerts: List of ExtendedHoursAlert objects
            platforms: Optional list of platforms

        Returns:
            Dict mapping platform to success status
        """
        if not volume_alerts and not extended_alerts:
            logger.info("No alerts to send")
            return {}

        message = self.formatter.format_combined_alerts(volume_alerts, extended_alerts)

        if platforms is None:
            return await self.send_to_all(message)

        results = {}
        if 'telegram' in platforms:
            results['telegram'] = await self.send_telegram(message)
        if 'signal' in platforms:
            results['signal'] = await self.send_signal(message)

        return results

    async def send_single_alert(
        self,
        alert: VolumeAlert | ExtendedHoursAlert,
        platforms: Optional[List[str]] = None
    ) -> Dict[str, bool]:
        """
        Send a single alert immediately

        Args:
            alert: Single alert object
            platforms: Optional list of platforms

        Returns:
            Dict mapping platform to success status
        """
        message = self.formatter.format_single_alert(alert)

        if platforms is None:
            return await self.send_to_all(message)

        results = {}
        if 'telegram' in platforms:
            results['telegram'] = await self.send_telegram(message)
        if 'signal' in platforms:
            results['signal'] = await self.send_signal(message)

        return results

    def send_volume_alerts_sync(
        self,
        alerts: List[VolumeAlert],
        platforms: Optional[List[str]] = None
    ) -> Dict[str, bool]:
        """Synchronous wrapper for send_volume_alerts"""
        return asyncio.run(self.send_volume_alerts(alerts, platforms))

    def send_extended_hours_alerts_sync(
        self,
        alerts: List[ExtendedHoursAlert],
        platforms: Optional[List[str]] = None
    ) -> Dict[str, bool]:
        """Synchronous wrapper for send_extended_hours_alerts"""
        return asyncio.run(self.send_extended_hours_alerts(alerts, platforms))

    def send_combined_alerts_sync(
        self,
        volume_alerts: List[VolumeAlert],
        extended_alerts: List[ExtendedHoursAlert],
        platforms: Optional[List[str]] = None
    ) -> Dict[str, bool]:
        """Synchronous wrapper for send_combined_alerts"""
        return asyncio.run(self.send_combined_alerts(volume_alerts, extended_alerts, platforms))


# Create global sender instance
_sender_instance: Optional[StockAlertSender] = None


def get_sender() -> StockAlertSender:
    """Get global sender instance"""
    global _sender_instance
    if _sender_instance is None:
        _sender_instance = StockAlertSender()
    return _sender_instance
