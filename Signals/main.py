#!/usr/bin/env python3
"""
Main entry point for the Forex Signal Generation System
Runs weekly analysis at 6 AM Monday and generates trading signals
"""
import argparse
import logging
import sys
import os
from datetime import datetime
from typing import List, Optional

import schedule
import time

from src.core.config import settings
from src.signal_generator import signal_generator
from src.report_generator import report_generator

def setup_logging(log_level: str = 'INFO', log_file: Optional[str] = None):
    """Setup logging configuration"""
    log_dir = settings.log_dir
    os.makedirs(log_dir, exist_ok=True)

    log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'

    handlers = [logging.StreamHandler(sys.stdout)]

    if log_file:
        handlers.append(logging.FileHandler(os.path.join(log_dir, log_file)))
    else:
        timestamp = datetime.now().strftime('%Y%m%d')
        handlers.append(logging.FileHandler(os.path.join(log_dir, f'forex_signals_{timestamp}.log')))

    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format=log_format,
        handlers=handlers
    )

    logger = logging.getLogger(__name__)
    logger.info("Forex Signal Generation System started")
    return logger
def generate_signals(pairs: List[str], output_formats: List[str] = None, 
                    output_dir: str = 'reports', save_reports: bool = True) -> dict:
    """
    Generate trading signals for specified currency pairs
    
    Args:
        pairs: List of currency pairs to analyze
        output_formats: List of output formats ('txt', 'json', 'csv', 'html')
        output_dir: Directory to save reports
        save_reports: Whether to save reports to files
    
    Returns:
        Dictionary with signals and report paths
    """
    logger = logging.getLogger(__name__)
    
    if output_formats is None:
        output_formats = ['txt', 'json']
    
    try:
        logger.info(f"Starting signal generation for pairs: {pairs}")
        
        # Generate signals for all pairs
        signals = signal_generator.generate_signals_for_pairs(pairs)
        
        # Count active signals
        active_signals = sum(1 for signal in signals.values() if signal.action != 'HOLD')
        logger.info(f"Generated {len(signals)} signals ({active_signals} active)")
        
        # Generate reports in requested formats
        report_paths = {}
        
        for output_format in output_formats:
            try:
                logger.info(f"Generating {output_format.upper()} report")
                
                # Generate report content
                report_content = report_generator.generate_comprehensive_report(
                    signals, output_format
                )
                
                # Save report if requested
                if save_reports:
                    report_path = report_generator.save_report(
                        report_content, output_format, output_dir
                    )
                    report_paths[output_format] = report_path
                    logger.info(f"Saved {output_format.upper()} report to: {report_path}")
                else:
                    report_paths[output_format] = report_content
                    
            except Exception as e:
                logger.error(f"Failed to generate {output_format} report: {e}")
                report_paths[output_format] = None
        
        return {
            'signals': signals,
            'report_paths': report_paths,
            'timestamp': datetime.now().isoformat(),
            'active_signals_count': active_signals,
            'total_pairs_analyzed': len(signals)
        }
        
    except Exception as e:
        logger.error(f"Signal generation failed: {e}")
        raise

def run_weekly_analysis():
    """Run the weekly analysis scheduled for Monday 6 AM"""
    logger = logging.getLogger(__name__)
    
    try:
        logger.info("=== WEEKLY FOREX SIGNAL ANALYSIS STARTED ===")
        
        # Get currency pairs from config
        trading_config = config.get_trading_config()
        pairs = trading_config.get('currency_pairs', ['USDCAD', 'EURUSD', 'CHFJPY', 'USDJPY', 'USDCHF'])
        
        # Generate signals and reports
        results = generate_signals(
            pairs=pairs,
            output_formats=['txt', 'json', 'csv', 'html'],
            save_reports=True
        )
        
        # Log summary
        logger.info(f"Weekly analysis completed:")
        logger.info(f"  - Pairs analyzed: {results['total_pairs_analyzed']}")
        logger.info(f"  - Active signals: {results['active_signals_count']}")
        logger.info(f"  - Reports generated: {len(results['report_paths'])}")
        
        # Print signal summary
        for pair, signal in results['signals'].items():
            if signal.action != 'HOLD':
                logger.info(f"  - {pair}: {signal.action} (confidence: {signal.confidence:.1%})")
        
        logger.info("=== WEEKLY FOREX SIGNAL ANALYSIS COMPLETED ===")
        
        return results
        
    except Exception as e:
        logger.error(f"Weekly analysis failed: {e}")
        raise

def print_signal_summary(signals: dict):
    """Print a summary of generated signals to console"""
    print("\n" + "="*60)
    print("FOREX TRADING SIGNALS SUMMARY")
    print("="*60)
    
    active_signals = []
    hold_signals = []
    
    for pair, signal in signals.items():
        if signal.action != 'HOLD':
            active_signals.append((pair, signal))
        else:
            hold_signals.append((pair, signal))
    
    # Print active signals
    if active_signals:
        print(f"\nACTIVE SIGNALS ({len(active_signals)}):")
        print("-" * 30)
        
        for pair, signal in sorted(active_signals, key=lambda x: x[1].confidence, reverse=True):
            action_symbol = "📈" if signal.action == "BUY" else "📉"
            confidence_stars = "★" * int(signal.confidence * 5)
            
            print(f"{pair:8} {signal.action:4} {action_symbol} "
                  f"Conf: {signal.confidence:.1%} {confidence_stars}")
            
            if signal.entry_price and signal.target_pips:
                print(f"         Entry: {signal.entry_price:.5f} "
                      f"Target: {signal.target_pips:.0f} pips "
                      f"Prob: {signal.weekly_achievement_probability:.1%}")
    
    # Print hold signals
    if hold_signals:
        print(f"\nHOLD RECOMMENDATIONS ({len(hold_signals)}):")
        print("-" * 30)
        
        for pair, signal in hold_signals:
            print(f"{pair:8} HOLD ⏸️  Signal too weak")
    
    print(f"\nGenerated at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}")
    print("="*60)

def main():
    """Main function with command line interface"""
    parser = argparse.ArgumentParser(
        description="Forex Signal Generation System",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Generate signals for default pairs
  python main.py --generate

  # Generate signals for specific pairs
  python main.py --generate --pairs EURUSD GBPUSD

  # Schedule weekly analysis (runs Monday 6 AM)
  python main.py --schedule

  # Generate signals with specific output formats
  python main.py --generate --formats txt json html

  # Run in test mode (no file output)
  python main.py --generate --test-mode
        """
    )
    
    # Main commands
    parser.add_argument('--generate', action='store_true',
                       help='Generate signals immediately')
    parser.add_argument('--schedule', action='store_true',
                       help='Run scheduled weekly analysis (Monday 6 AM)')
    
    # Configuration options
    parser.add_argument('--pairs', nargs='+', 
                       default=['USDCAD', 'EURUSD', 'CHFJPY', 'USDJPY', 'USDCHF'],
                       help='Currency pairs to analyze')
    parser.add_argument('--formats', nargs='+', 
                       choices=['txt', 'json', 'csv', 'html'],
                       default=['txt', 'json'],
                       help='Output formats for reports')
    parser.add_argument('--output-dir', default='reports',
                       help='Directory to save reports')
    
    # Mode options
    parser.add_argument('--test-mode', action='store_true',
                       help='Run in test mode (no file output)')
    parser.add_argument('--log-level', choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
                       default='INFO', help='Logging level')
    parser.add_argument('--log-file', help='Custom log file name')
    
    args = parser.parse_args()
    
    # Validate arguments
    if not args.generate and not args.schedule:
        parser.error("Must specify either --generate or --schedule")
    
    # Setup logging
    logger = setup_logging(args.log_level, args.log_file)
    
    try:
        if args.generate:
            # Generate signals immediately
            logger.info("Running immediate signal generation")
            
            results = generate_signals(
                pairs=args.pairs,
                output_formats=args.formats,
                output_dir=args.output_dir,
                save_reports=not args.test_mode
            )
            
            # Print summary to console
            print_signal_summary(results['signals'])
            
            if not args.test_mode:
                print(f"\nReports saved to: {args.output_dir}/")
                for format_type, path in results['report_paths'].items():
                    if path:
                        print(f"  - {format_type.upper()}: {os.path.basename(path)}")
            else:
                print("\n(Test mode: no files saved)")
        
        elif args.schedule:
            # Schedule weekly analysis
            logger.info("Starting scheduled weekly analysis service")
            print("Forex Signal Generation System - Scheduled Mode")
            print("Scheduled to run every Monday at 6:00 AM")
            print("Press Ctrl+C to stop")
            
            # Schedule the job
            schedule.every().monday.at("06:00").do(run_weekly_analysis)
            
            # Check if we should run immediately (if it's Monday after 6 AM)
            now = datetime.now()
            if now.weekday() == 0 and now.hour >= 6:  # Monday after 6 AM
                logger.info("It's Monday after 6 AM - running analysis now")
                run_weekly_analysis()
            
            # Keep the scheduler running
            while True:
                schedule.run_pending()
                time.sleep(60)  # Check every minute
                
    except KeyboardInterrupt:
        logger.info("Signal generation system stopped by user")
        print("\nSignal generation system stopped.")
        sys.exit(0)
        
    except Exception as e:
        logger.error(f"System error: {e}")
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()