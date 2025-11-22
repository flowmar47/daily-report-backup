#!/usr/bin/env python3
"""
Stock Volume Detection System

Real-time monitoring for unusual stock volume and extended hours activity.
Integrates with existing forex signals messaging infrastructure.

Features:
- Unusual volume detection (relative to historical averages)
- Pre-market activity monitoring (4:00 AM - 9:30 AM ET)
- After-hours activity monitoring (4:00 PM - 8:00 PM ET)
- Automated alerts to Signal and Telegram groups
- Multi-source API integration with fallbacks

Usage:
    # Manual execution - scan for unusual volume
    python stock_volume_detection.py

    # Scan specific symbols
    python stock_volume_detection.py --symbols AAPL,NVDA,TSLA

    # Monitor extended hours only
    python stock_volume_detection.py --extended-only

    # Generate without sending (test mode)
    python stock_volume_detection.py --dry-run

    # Continuous monitoring mode
    python stock_volume_detection.py --continuous --interval 300
"""

import asyncio
import argparse
import logging
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Dict, Any

# Add project root to path for imports
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from stock_alerts.core.config import get_stock_settings, validate_stock_environment
from stock_alerts.core.exceptions import StockAlertError, ConfigurationError
from stock_alerts.fetchers.stock_fetcher import StockDataFetcher
from stock_alerts.detection.volume_analyzer import VolumeAnalyzer
from stock_alerts.detection.extended_hours import ExtendedHoursMonitor
from stock_alerts.messaging.sender import StockAlertSender
from stock_alerts.messaging.formatter import StockAlertFormatter
from stock_alerts.data.models import AlertSeverity, MarketSession

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('logs/stock_volume_detection.log')
    ]
)
logger = logging.getLogger(__name__)


class StockVolumeDetectionSystem:
    """
    Main stock volume detection system

    Coordinates data fetching, analysis, and alert delivery.
    """

    def __init__(self, dry_run: bool = False):
        """
        Initialize the stock volume detection system

        Args:
            dry_run: If True, generate alerts but don't send messages
        """
        logger.info("=" * 60)
        logger.info("STOCK VOLUME DETECTION SYSTEM")
        logger.info(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info("=" * 60)

        self.dry_run = dry_run

        # Validate environment
        try:
            validate_stock_environment()
        except ValueError as e:
            logger.error(f"Configuration error: {e}")
            raise ConfigurationError(str(e))

        # Load settings
        self.settings = get_stock_settings()

        # Initialize components
        self.fetcher = StockDataFetcher()
        self.volume_analyzer = VolumeAnalyzer(fetcher=self.fetcher)
        self.extended_hours = ExtendedHoursMonitor(fetcher=self.fetcher)
        self.sender = StockAlertSender()
        self.formatter = StockAlertFormatter()

        # Ensure log directory exists
        Path('logs').mkdir(exist_ok=True)

        logger.info(f"System initialized - Dry run: {dry_run}")
        logger.info(f"Default watchlist: {len(self.settings.default_watchlist)} symbols")
        logger.info(f"Volume threshold: {self.settings.unusual_volume_threshold}x average")
        logger.info(f"Extended hours threshold: {self.settings.extended_hours_price_change_threshold}%")

    async def run_volume_scan(
        self,
        symbols: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Run volume analysis scan

        Args:
            symbols: Optional list of symbols (uses default watchlist if None)

        Returns:
            Dict with scan results
        """
        logger.info("-" * 40)
        logger.info("RUNNING VOLUME SCAN")
        logger.info("-" * 40)

        if symbols is None:
            symbols = self.settings.default_watchlist

        logger.info(f"Scanning {len(symbols)} symbols...")

        # Run volume analysis
        alerts = self.volume_analyzer.scan_watchlist(symbols)

        logger.info(f"Found {len(alerts)} unusual volume alerts")

        # Log alert summary
        for severity in AlertSeverity:
            count = len([a for a in alerts if a.severity == severity])
            if count > 0:
                logger.info(f"  {severity.value}: {count} alerts")

        # Send alerts if not dry run and alerts exist
        send_results = {}
        if alerts and not self.dry_run:
            logger.info("Sending volume alerts...")
            send_results = await self.sender.send_volume_alerts(alerts)
        elif alerts and self.dry_run:
            logger.info("DRY RUN - Alerts generated but not sent")
            message = self.formatter.format_volume_alerts(alerts)
            logger.info("Generated message:")
            for line in message.split('\n')[:20]:
                logger.info(f"  {line}")
            if len(message.split('\n')) > 20:
                logger.info("  ... (truncated)")

        return {
            'scan_type': 'volume',
            'symbols_scanned': len(symbols),
            'alerts_found': len(alerts),
            'alerts': alerts,
            'send_results': send_results,
            'timestamp': datetime.now().isoformat()
        }

    async def run_extended_hours_scan(
        self,
        symbols: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Run extended hours activity scan

        Args:
            symbols: Optional list of symbols (uses default watchlist if None)

        Returns:
            Dict with scan results
        """
        logger.info("-" * 40)
        logger.info("RUNNING EXTENDED HOURS SCAN")
        logger.info("-" * 40)

        # Check current session
        session = self.extended_hours.get_current_session()
        logger.info(f"Current session: {session.value}")

        if session not in (MarketSession.PREMARKET, MarketSession.AFTERHOURS):
            logger.info("Not currently in extended hours - skipping scan")
            return {
                'scan_type': 'extended_hours',
                'session': session.value,
                'skipped': True,
                'reason': 'Not in extended hours',
                'timestamp': datetime.now().isoformat()
            }

        if symbols is None:
            symbols = self.settings.default_watchlist

        logger.info(f"Scanning {len(symbols)} symbols for {session.value} activity...")

        # Run extended hours analysis
        alerts = self.extended_hours.scan_watchlist(symbols)

        logger.info(f"Found {len(alerts)} extended hours alerts")

        # Send alerts if not dry run and alerts exist
        send_results = {}
        if alerts and not self.dry_run:
            logger.info("Sending extended hours alerts...")
            send_results = await self.sender.send_extended_hours_alerts(alerts)
        elif alerts and self.dry_run:
            logger.info("DRY RUN - Alerts generated but not sent")
            message = self.formatter.format_extended_hours_alerts(alerts)
            logger.info("Generated message:")
            for line in message.split('\n')[:20]:
                logger.info(f"  {line}")

        return {
            'scan_type': 'extended_hours',
            'session': session.value,
            'symbols_scanned': len(symbols),
            'alerts_found': len(alerts),
            'alerts': alerts,
            'send_results': send_results,
            'timestamp': datetime.now().isoformat()
        }

    async def run_full_scan(
        self,
        symbols: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Run both volume and extended hours scans

        Args:
            symbols: Optional list of symbols

        Returns:
            Dict with combined scan results
        """
        logger.info("=" * 60)
        logger.info("RUNNING FULL MARKET SCAN")
        logger.info(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info("=" * 60)

        # Run both scans
        volume_result = await self.run_volume_scan(symbols)
        extended_result = await self.run_extended_hours_scan(symbols)

        # Combine alerts and send summary if we have both types
        volume_alerts = volume_result.get('alerts', [])
        extended_alerts = extended_result.get('alerts', [])

        # If we have alerts of both types, send combined message
        send_results = {}
        if (volume_alerts or extended_alerts) and not self.dry_run:
            if volume_alerts and extended_alerts:
                logger.info("Sending combined alert summary...")
                send_results = await self.sender.send_combined_alerts(
                    volume_alerts, extended_alerts
                )

        return {
            'volume_scan': volume_result,
            'extended_hours_scan': extended_result,
            'total_alerts': len(volume_alerts) + len(extended_alerts),
            'combined_send_results': send_results,
            'timestamp': datetime.now().isoformat()
        }

    async def run_continuous(
        self,
        symbols: Optional[List[str]] = None,
        interval_seconds: int = 300,
        max_iterations: Optional[int] = None
    ):
        """
        Run continuous monitoring loop

        Args:
            symbols: Optional list of symbols
            interval_seconds: Seconds between scans (default 5 minutes)
            max_iterations: Maximum number of iterations (None for infinite)
        """
        logger.info("=" * 60)
        logger.info("STARTING CONTINUOUS MONITORING")
        logger.info(f"Interval: {interval_seconds} seconds")
        logger.info(f"Max iterations: {max_iterations or 'Unlimited'}")
        logger.info("=" * 60)

        iteration = 0
        while max_iterations is None or iteration < max_iterations:
            iteration += 1
            logger.info(f"\n--- Iteration {iteration} ---")

            try:
                # Run full scan
                await self.run_full_scan(symbols)

            except Exception as e:
                logger.error(f"Error in scan iteration: {e}")

            # Wait for next interval
            if max_iterations is None or iteration < max_iterations:
                logger.info(f"Waiting {interval_seconds} seconds until next scan...")
                await asyncio.sleep(interval_seconds)

        logger.info("Continuous monitoring completed")

    async def get_market_summary(
        self,
        symbols: Optional[List[str]] = None
    ) -> str:
        """
        Generate a market summary without sending

        Args:
            symbols: Optional list of symbols

        Returns:
            Formatted market summary string
        """
        if symbols is None:
            symbols = self.settings.default_watchlist

        # Get volume leaders
        volume_leaders = self.volume_analyzer.get_volume_leaders(symbols)

        # Get session summary
        session_summary = self.extended_hours.get_session_summary(symbols)

        # Run scans
        volume_alerts = self.volume_analyzer.scan_watchlist(symbols)
        extended_alerts = self.extended_hours.scan_watchlist(symbols)

        # Format summary
        summary = self.formatter.format_market_summary(
            volume_alerts, extended_alerts, volume_leaders
        )

        return summary

    async def close(self):
        """Clean up resources"""
        await self.sender.close()


async def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description='Stock Volume Detection System',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    # Scan default watchlist for unusual volume
    python stock_volume_detection.py

    # Scan specific symbols
    python stock_volume_detection.py --symbols AAPL,NVDA,TSLA,AMD

    # Extended hours scan only
    python stock_volume_detection.py --extended-only

    # Test mode (don't send messages)
    python stock_volume_detection.py --dry-run

    # Continuous monitoring every 5 minutes
    python stock_volume_detection.py --continuous --interval 300

    # Generate market summary
    python stock_volume_detection.py --summary
        """
    )

    parser.add_argument(
        '--symbols',
        type=str,
        help='Comma-separated list of symbols to scan'
    )
    parser.add_argument(
        '--extended-only',
        action='store_true',
        help='Only scan for extended hours activity'
    )
    parser.add_argument(
        '--volume-only',
        action='store_true',
        help='Only scan for unusual volume'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Generate alerts but do not send messages'
    )
    parser.add_argument(
        '--continuous',
        action='store_true',
        help='Run in continuous monitoring mode'
    )
    parser.add_argument(
        '--interval',
        type=int,
        default=300,
        help='Seconds between scans in continuous mode (default: 300)'
    )
    parser.add_argument(
        '--max-iterations',
        type=int,
        default=None,
        help='Maximum iterations in continuous mode (default: unlimited)'
    )
    parser.add_argument(
        '--summary',
        action='store_true',
        help='Generate and print market summary'
    )
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Enable verbose logging'
    )

    args = parser.parse_args()

    # Set logging level
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    # Parse symbols
    symbols = None
    if args.symbols:
        symbols = [s.strip().upper() for s in args.symbols.split(',')]

    try:
        # Initialize system
        system = StockVolumeDetectionSystem(dry_run=args.dry_run)

        # Run appropriate scan mode
        if args.summary:
            summary = await system.get_market_summary(symbols)
            print("\n" + summary)

        elif args.continuous:
            await system.run_continuous(
                symbols=symbols,
                interval_seconds=args.interval,
                max_iterations=args.max_iterations
            )

        elif args.extended_only:
            result = await system.run_extended_hours_scan(symbols)
            logger.info(f"Scan complete: {result.get('alerts_found', 0)} alerts")

        elif args.volume_only:
            result = await system.run_volume_scan(symbols)
            logger.info(f"Scan complete: {result.get('alerts_found', 0)} alerts")

        else:
            # Default: run full scan
            result = await system.run_full_scan(symbols)
            logger.info(f"Full scan complete: {result.get('total_alerts', 0)} total alerts")

        # Cleanup
        await system.close()

        logger.info("Stock volume detection completed successfully")

    except ConfigurationError as e:
        logger.error(f"Configuration error: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        logger.info("Interrupted by user")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == '__main__':
    asyncio.run(main())
