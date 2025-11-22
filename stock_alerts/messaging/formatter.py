"""
Stock Alert Message Formatter

Formats stock alerts for Signal and Telegram delivery.
Follows the same plaintext format pattern as forex signals.
"""

import logging
from datetime import datetime
from typing import List, Optional

from ..data.models import (
    VolumeAlert,
    ExtendedHoursAlert,
    AlertSeverity,
    AlertBatch,
    MarketSession,
)
from ..core.config import get_stock_settings

logger = logging.getLogger(__name__)


class StockAlertFormatter:
    """Formats stock alerts for messaging delivery"""

    def __init__(self):
        self.settings = get_stock_settings()
        self.max_alerts = self.settings.max_alerts_per_message
        self.include_technical = self.settings.include_technical_context

    def format_volume_alerts(
        self,
        alerts: List[VolumeAlert],
        include_header: bool = True
    ) -> str:
        """
        Format volume alerts as plaintext message

        Args:
            alerts: List of VolumeAlert objects
            include_header: Whether to include message header

        Returns:
            Formatted message string
        """
        if not alerts:
            return ""

        lines = []

        if include_header:
            lines.extend([
                "STOCK VOLUME ALERTS",
                f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
                f"Alerts: {len(alerts)}",
                "=" * 40,
                ""
            ])

        # Sort by severity
        sorted_alerts = sorted(
            alerts,
            key=lambda a: (
                {AlertSeverity.CRITICAL: 0, AlertSeverity.HIGH: 1,
                 AlertSeverity.MEDIUM: 2, AlertSeverity.LOW: 3}.get(a.severity, 4),
                -a.volume_ratio
            )
        )

        for i, alert in enumerate(sorted_alerts[:self.max_alerts]):
            lines.extend(self._format_volume_alert(alert))
            if i < len(sorted_alerts[:self.max_alerts]) - 1:
                lines.append("-" * 40)

        if len(alerts) > self.max_alerts:
            lines.append(f"\n... and {len(alerts) - self.max_alerts} more alerts")

        lines.extend([
            "",
            "=" * 40,
            "Real-time stock data from validated API sources"
        ])

        return "\n".join(lines)

    def _format_volume_alert(self, alert: VolumeAlert) -> List[str]:
        """Format a single volume alert"""
        # Severity indicator
        severity_prefix = {
            AlertSeverity.CRITICAL: "[!!!] ",
            AlertSeverity.HIGH: "[!!] ",
            AlertSeverity.MEDIUM: "[!] ",
            AlertSeverity.LOW: ""
        }.get(alert.severity, "")

        # Direction indicator
        direction = "+" if alert.price_change >= 0 else ""

        lines = [
            f"{severity_prefix}{alert.symbol} - UNUSUAL VOLUME",
            f"Price: ${alert.price:.2f} ({direction}{alert.price_change_percent:.2f}%)",
            f"Volume: {alert.current_volume:,} ({alert.volume_ratio:.1f}x average)",
        ]

        # Add technical context if enabled
        if self.include_technical:
            if alert.rsi:
                rsi_note = ""
                if alert.rsi > 70:
                    rsi_note = " [Overbought]"
                elif alert.rsi < 30:
                    rsi_note = " [Oversold]"
                lines.append(f"RSI(14): {alert.rsi:.1f}{rsi_note}")

            if alert.support and alert.resistance:
                lines.append(f"Support/Resistance: ${alert.support:.2f} / ${alert.resistance:.2f}")

        # Add context
        if alert.context:
            lines.append(f"Analysis: {alert.context}")

        lines.append("")  # Empty line between alerts

        return lines

    def format_extended_hours_alerts(
        self,
        alerts: List[ExtendedHoursAlert],
        include_header: bool = True
    ) -> str:
        """
        Format extended hours alerts as plaintext message

        Args:
            alerts: List of ExtendedHoursAlert objects
            include_header: Whether to include message header

        Returns:
            Formatted message string
        """
        if not alerts:
            return ""

        # Determine session
        session = alerts[0].session if alerts else MarketSession.AFTERHOURS
        session_name = "PRE-MARKET" if session == MarketSession.PREMARKET else "AFTER-HOURS"

        lines = []

        if include_header:
            lines.extend([
                f"{session_name} TRADING ALERTS",
                f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
                f"Alerts: {len(alerts)}",
                "=" * 40,
                ""
            ])

        # Sort by absolute price change
        sorted_alerts = sorted(
            alerts,
            key=lambda a: abs(a.price_change_percent),
            reverse=True
        )

        for i, alert in enumerate(sorted_alerts[:self.max_alerts]):
            lines.extend(self._format_extended_hours_alert(alert))
            if i < len(sorted_alerts[:self.max_alerts]) - 1:
                lines.append("-" * 40)

        if len(alerts) > self.max_alerts:
            lines.append(f"\n... and {len(alerts) - self.max_alerts} more alerts")

        lines.extend([
            "",
            "=" * 40,
            "Extended hours data from validated API sources"
        ])

        return "\n".join(lines)

    def _format_extended_hours_alert(self, alert: ExtendedHoursAlert) -> List[str]:
        """Format a single extended hours alert"""
        # Severity indicator
        severity_prefix = {
            AlertSeverity.CRITICAL: "[!!!] ",
            AlertSeverity.HIGH: "[!!] ",
            AlertSeverity.MEDIUM: "[!] ",
            AlertSeverity.LOW: ""
        }.get(alert.severity, "")

        # Direction indicator
        direction_symbol = "+" if alert.price_change >= 0 else ""
        direction_word = "UP" if alert.price_change >= 0 else "DOWN"

        session_name = "PRE-MARKET" if alert.session == MarketSession.PREMARKET else "AFTER-HOURS"

        lines = [
            f"{severity_prefix}{alert.symbol} - {session_name} {direction_word}",
            f"Price: ${alert.current_price:.2f} ({direction_symbol}{alert.price_change_percent:.2f}%)",
            f"Regular Close: ${alert.regular_close:.2f}",
            f"Extended Volume: {alert.extended_volume:,}",
        ]

        # Add bid/ask if available
        if alert.bid and alert.ask:
            spread = alert.ask - alert.bid
            lines.append(f"Bid/Ask: ${alert.bid:.2f} / ${alert.ask:.2f} (spread: ${spread:.2f})")

        # Add catalyst if known
        if alert.catalyst:
            lines.append(f"Potential Catalyst: {alert.catalyst}")

        lines.append("")  # Empty line

        return lines

    def format_combined_alerts(
        self,
        volume_alerts: List[VolumeAlert],
        extended_alerts: List[ExtendedHoursAlert]
    ) -> str:
        """
        Format both volume and extended hours alerts in a single message

        Args:
            volume_alerts: List of VolumeAlert objects
            extended_alerts: List of ExtendedHoursAlert objects

        Returns:
            Combined formatted message
        """
        lines = [
            "STOCK MARKET ALERTS",
            f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "=" * 50,
            ""
        ]

        # Add volume alerts section
        if volume_alerts:
            lines.extend([
                "UNUSUAL VOLUME",
                "-" * 40,
                ""
            ])

            for alert in volume_alerts[:5]:  # Top 5
                lines.extend(self._format_volume_alert(alert))

            if len(volume_alerts) > 5:
                lines.append(f"... and {len(volume_alerts) - 5} more volume alerts")
            lines.append("")

        # Add extended hours section
        if extended_alerts:
            session = extended_alerts[0].session
            session_name = "PRE-MARKET" if session == MarketSession.PREMARKET else "AFTER-HOURS"

            lines.extend([
                f"{session_name} MOVERS",
                "-" * 40,
                ""
            ])

            for alert in extended_alerts[:5]:  # Top 5
                lines.extend(self._format_extended_hours_alert(alert))

            if len(extended_alerts) > 5:
                lines.append(f"... and {len(extended_alerts) - 5} more {session_name.lower()} alerts")
            lines.append("")

        lines.extend([
            "=" * 50,
            "Real-time data from validated API sources"
        ])

        return "\n".join(lines)

    def format_market_summary(
        self,
        volume_alerts: List[VolumeAlert],
        extended_alerts: List[ExtendedHoursAlert],
        movers: Optional[List[dict]] = None
    ) -> str:
        """
        Format a complete market summary message

        Args:
            volume_alerts: List of volume alerts
            extended_alerts: List of extended hours alerts
            movers: Optional list of top movers

        Returns:
            Formatted summary message
        """
        lines = [
            "STOCK MARKET SUMMARY",
            f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "=" * 50,
            ""
        ]

        # Summary stats
        lines.extend([
            "OVERVIEW",
            f"Volume Alerts: {len(volume_alerts)}",
            f"Extended Hours Alerts: {len(extended_alerts)}",
            ""
        ])

        # Critical alerts first
        critical_volume = [a for a in volume_alerts if a.severity == AlertSeverity.CRITICAL]
        critical_extended = [a for a in extended_alerts if a.severity == AlertSeverity.CRITICAL]

        if critical_volume or critical_extended:
            lines.extend([
                "CRITICAL ALERTS",
                "-" * 40,
            ])

            for alert in critical_volume[:3]:
                lines.append(
                    f"[!!!] {alert.symbol}: ${alert.price:.2f} "
                    f"({alert.price_change_percent:+.2f}%) Vol: {alert.volume_ratio:.1f}x"
                )

            for alert in critical_extended[:3]:
                lines.append(
                    f"[!!!] {alert.symbol}: ${alert.current_price:.2f} "
                    f"({alert.price_change_percent:+.2f}%) Extended hours"
                )
            lines.append("")

        # Top movers if provided
        if movers:
            lines.extend([
                "TOP MOVERS BY VOLUME",
                "-" * 40,
            ])
            for mover in movers[:5]:
                lines.append(
                    f"{mover['symbol']}: {mover['volume_ratio']:.1f}x avg volume, "
                    f"${mover.get('price', 0):.2f} ({mover.get('change_percent', 0):+.2f}%)"
                )
            lines.append("")

        lines.extend([
            "=" * 50,
            "Real-time data from validated API sources"
        ])

        return "\n".join(lines)

    def format_single_alert(
        self,
        alert: VolumeAlert | ExtendedHoursAlert
    ) -> str:
        """
        Format a single alert for immediate notification

        Args:
            alert: Single alert object

        Returns:
            Formatted alert message
        """
        if isinstance(alert, VolumeAlert):
            lines = self._format_volume_alert(alert)
        else:
            lines = self._format_extended_hours_alert(alert)

        return "\n".join(lines)
