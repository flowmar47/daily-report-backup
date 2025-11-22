#!/usr/bin/env python3
"""
Stock Alerts Demo Script

Demonstrates the stock volume detection system capabilities.
Run this to test the system without sending actual messages.

Usage:
    python stock_alerts_demo.py
"""

import asyncio
import logging
import sys
from pathlib import Path
from datetime import datetime

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))


def demo_data_fetcher():
    """Demonstrate stock data fetching capabilities"""
    print("\n" + "=" * 60)
    print("DEMO: Stock Data Fetcher")
    print("=" * 60)

    from stock_alerts.fetchers.stock_fetcher import StockDataFetcher

    fetcher = StockDataFetcher()

    # Test symbols
    test_symbols = ['AAPL', 'NVDA', 'TSLA']

    print(f"\nFetching quotes for: {', '.join(test_symbols)}")
    print("-" * 40)

    for symbol in test_symbols:
        quote = fetcher.get_quote(symbol)
        if quote:
            direction = "+" if quote.change >= 0 else ""
            print(f"\n{symbol}:")
            print(f"  Price: ${quote.price:.2f}")
            print(f"  Change: {direction}{quote.change_percent:.2f}%")
            print(f"  Volume: {quote.volume:,}")
            print(f"  Source: {quote.source}")
        else:
            print(f"\n{symbol}: Unable to fetch quote")

    # Test historical data
    print("\n" + "-" * 40)
    print("Fetching historical data for AAPL...")

    historical = fetcher.get_historical_data('AAPL', days=10)
    if historical:
        print(f"Got {len(historical)} historical bars")
        print(f"Latest: {historical[-1].timestamp.strftime('%Y-%m-%d')} "
              f"Close: ${historical[-1].close:.2f} "
              f"Volume: {historical[-1].volume:,}")
    else:
        print("Unable to fetch historical data")

    # Test comprehensive stock data
    print("\n" + "-" * 40)
    print("Fetching comprehensive data for NVDA...")

    stock_data = fetcher.get_stock_data('NVDA')
    if stock_data:
        print(f"Symbol: {stock_data.symbol}")
        print(f"Price: ${stock_data.quote.price:.2f}")
        if stock_data.avg_volume_20d:
            print(f"20-day Avg Volume: {stock_data.avg_volume_20d:,.0f}")
        if stock_data.rsi_14:
            print(f"RSI(14): {stock_data.rsi_14:.1f}")
        if stock_data.support_level and stock_data.resistance_level:
            print(f"Support/Resistance: ${stock_data.support_level:.2f} / ${stock_data.resistance_level:.2f}")
    else:
        print("Unable to fetch stock data")


def demo_volume_analyzer():
    """Demonstrate volume analysis capabilities"""
    print("\n" + "=" * 60)
    print("DEMO: Volume Analyzer")
    print("=" * 60)

    from stock_alerts.detection.volume_analyzer import VolumeAnalyzer
    from stock_alerts.fetchers.stock_fetcher import StockDataFetcher

    fetcher = StockDataFetcher()
    analyzer = VolumeAnalyzer(fetcher=fetcher)

    # Get volume leaders
    print("\nTop 5 Volume Leaders (from watchlist subset):")
    print("-" * 40)

    test_symbols = ['AAPL', 'MSFT', 'NVDA', 'TSLA', 'AMD', 'META', 'GOOGL', 'AMZN']
    leaders = analyzer.get_volume_leaders(symbols=test_symbols, top_n=5)

    for i, leader in enumerate(leaders, 1):
        print(f"{i}. {leader['symbol']}: {leader['volume_ratio']:.2f}x average, "
              f"${leader.get('price', 0):.2f} ({leader.get('change_percent', 0):+.2f}%)")

    # Scan for unusual volume
    print("\n" + "-" * 40)
    print("Scanning for unusual volume...")

    alerts = analyzer.scan_watchlist(symbols=test_symbols[:5])

    if alerts:
        print(f"\nFound {len(alerts)} unusual volume alerts:")
        for alert in alerts[:3]:
            print(f"\n  {alert.symbol}:")
            print(f"    Volume: {alert.current_volume:,} ({alert.volume_ratio:.1f}x avg)")
            print(f"    Price: ${alert.price:.2f} ({alert.price_change_percent:+.2f}%)")
            print(f"    Severity: {alert.severity.value}")
            if alert.context:
                print(f"    Context: {alert.context}")
    else:
        print("No unusual volume alerts at this time")

    # Test accumulation/distribution detection
    print("\n" + "-" * 40)
    print("Analyzing accumulation/distribution for AAPL...")

    ad_result = analyzer.detect_accumulation_distribution('AAPL')
    if ad_result:
        print(f"Pattern: {ad_result['pattern']}")
        print(f"A/D Ratio: {ad_result['ad_ratio']}")
        print(f"Up Days: {ad_result['up_days']}, Down Days: {ad_result['down_days']}")
    else:
        print("Insufficient data for A/D analysis")


def demo_extended_hours():
    """Demonstrate extended hours monitoring"""
    print("\n" + "=" * 60)
    print("DEMO: Extended Hours Monitor")
    print("=" * 60)

    from stock_alerts.detection.extended_hours import ExtendedHoursMonitor
    from stock_alerts.fetchers.stock_fetcher import StockDataFetcher

    fetcher = StockDataFetcher()
    monitor = ExtendedHoursMonitor(fetcher=fetcher)

    # Check current session
    session = monitor.get_current_session()
    print(f"\nCurrent Market Session: {session.value}")

    # Get session summary
    print("\n" + "-" * 40)
    print("Market Session Summary:")

    test_symbols = ['AAPL', 'NVDA', 'TSLA', 'AMD', 'META']
    summary = monitor.get_session_summary(symbols=test_symbols)

    print(f"  Symbols Analyzed: {summary['symbols_analyzed']}")
    print(f"  Advancing: {summary['advancing']}")
    print(f"  Declining: {summary['declining']}")
    print(f"  Unchanged: {summary['unchanged']}")

    if summary.get('biggest_gainer'):
        bg = summary['biggest_gainer']
        print(f"  Biggest Gainer: {bg['symbol']} ({bg['change_percent']:+.2f}%)")

    if summary.get('biggest_loser'):
        bl = summary['biggest_loser']
        print(f"  Biggest Loser: {bl['symbol']} ({bl['change_percent']:+.2f}%)")

    # Get movers
    print("\n" + "-" * 40)
    print("Top Movers:")

    movers = monitor.get_movers(symbols=test_symbols, direction="both", top_n=5)
    for mover in movers:
        print(f"  {mover['symbol']}: ${mover['price']:.2f} ({mover['change_percent']:+.2f}%)")


def demo_message_formatting():
    """Demonstrate message formatting"""
    print("\n" + "=" * 60)
    print("DEMO: Message Formatting")
    print("=" * 60)

    from stock_alerts.messaging.formatter import StockAlertFormatter
    from stock_alerts.data.models import VolumeAlert, ExtendedHoursAlert, AlertSeverity, MarketSession

    formatter = StockAlertFormatter()

    # Create sample volume alert
    volume_alert = VolumeAlert(
        symbol="NVDA",
        severity=AlertSeverity.HIGH,
        current_volume=50000000,
        avg_volume=15000000,
        volume_ratio=3.33,
        price=875.50,
        price_change=25.30,
        price_change_percent=2.97,
        rsi=68.5,
        support=820.00,
        resistance=900.00,
        context="Very high volume, positive price action, near resistance"
    )

    # Create sample extended hours alert
    extended_alert = ExtendedHoursAlert(
        symbol="TSLA",
        severity=AlertSeverity.MEDIUM,
        session=MarketSession.AFTERHOURS,
        current_price=248.75,
        regular_close=242.50,
        price_change=6.25,
        price_change_percent=2.58,
        extended_volume=125000,
        bid=248.50,
        ask=249.00,
        catalyst="Possible earnings-related news"
    )

    # Format volume alerts
    print("\nSample Volume Alert Message:")
    print("-" * 40)
    message = formatter.format_volume_alerts([volume_alert])
    print(message)

    # Format extended hours alerts
    print("\n" + "-" * 40)
    print("Sample Extended Hours Alert Message:")
    print("-" * 40)
    message = formatter.format_extended_hours_alerts([extended_alert])
    print(message)


async def demo_full_system():
    """Demonstrate the full system (dry run)"""
    print("\n" + "=" * 60)
    print("DEMO: Full System (Dry Run)")
    print("=" * 60)

    try:
        from stock_volume_detection import StockVolumeDetectionSystem

        # Initialize in dry-run mode
        system = StockVolumeDetectionSystem(dry_run=True)

        # Run a small scan
        test_symbols = ['AAPL', 'NVDA', 'TSLA', 'AMD']

        print(f"\nRunning full scan on: {', '.join(test_symbols)}")
        print("-" * 40)

        result = await system.run_full_scan(symbols=test_symbols)

        print(f"\nScan Results:")
        print(f"  Volume Alerts: {result.get('volume_scan', {}).get('alerts_found', 0)}")
        print(f"  Extended Hours Alerts: {result.get('extended_hours_scan', {}).get('alerts_found', 0)}")
        print(f"  Total Alerts: {result.get('total_alerts', 0)}")

        await system.close()

    except Exception as e:
        print(f"Error running full system demo: {e}")
        logger.error(f"Full system demo error: {e}", exc_info=True)


def main():
    """Run all demos"""
    print("\n" + "#" * 60)
    print("#" + " " * 58 + "#")
    print("#   STOCK VOLUME DETECTION SYSTEM - DEMONSTRATION" + " " * 9 + "#")
    print("#" + " " * 58 + "#")
    print("#" * 60)
    print(f"\nTimestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    try:
        # Run component demos
        demo_data_fetcher()
        demo_volume_analyzer()
        demo_extended_hours()
        demo_message_formatting()

        # Run full system demo
        asyncio.run(demo_full_system())

        print("\n" + "=" * 60)
        print("DEMO COMPLETED SUCCESSFULLY")
        print("=" * 60)
        print("\nTo run the actual system:")
        print("  python stock_volume_detection.py              # Full scan")
        print("  python stock_volume_detection.py --dry-run    # Test mode")
        print("  python stock_volume_detection.py --help       # See all options")

    except ImportError as e:
        print(f"\nImport error: {e}")
        print("\nMake sure you have all dependencies installed:")
        print("  pip install yfinance requests httpx pytz pydantic pydantic-settings")

    except Exception as e:
        print(f"\nError during demo: {e}")
        logger.error(f"Demo error: {e}", exc_info=True)


if __name__ == '__main__':
    main()
