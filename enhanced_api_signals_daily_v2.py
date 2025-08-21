#!/usr/bin/env python3
"""
Enhanced API-Based Daily Signals System V2.0
- Refactored with proper module structure
- No sys.path hacks or directory changes  
- Clean error handling and logging
- Maintains all existing functionality and backward compatibility
"""

import asyncio
import argparse
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

# Clean imports using new package structure
from forex_signals.core.config import get_settings, validate_required_environment
from forex_signals.core.logging import setup_logging, get_logger, set_correlation_id
from forex_signals.core.exceptions import ForexSignalsError, ConfigurationError
from forex_signals.signals.generator import ForexSignalGenerator
from forex_signals.messaging.manager import MessagingManager


class EnhancedAPISignalsDailyV2:
    """
    Enhanced API-based daily signals system V2.0
    Clean implementation with proper architecture
    """
    
    def __init__(self):
        """Initialize the enhanced signals system"""
        # Setup logging first
        setup_logging()
        self.logger = get_logger(__name__)
        
        # Set correlation ID for this session
        self.correlation_id = set_correlation_id()
        
        self.logger.info("Initializing Enhanced API-based Daily Signals System V2.0...")
        
        try:
            # Validate environment first
            validate_required_environment()
            
            # Load settings
            self.settings = get_settings()
            
            # Initialize components
            self.signal_generator = ForexSignalGenerator()
            self.messaging_manager = MessagingManager()
            
            # Ensure required directories exist
            self._ensure_directories()
            
            self.logger.info("Enhanced signals system V2.0 initialized successfully")
            
        except ConfigurationError as e:
            self.logger.error(f"Configuration error: {e}")
            self.logger.error("Please check your .env file and ensure all required variables are set")
            raise
        except Exception as e:
            self.logger.error(f"Failed to initialize system: {e}")
            raise
    
    def _ensure_directories(self):
        """Ensure required directories exist"""
        directories = [
            Path(self.settings.log_dir),
            Path(self.settings.output_dir),
        ]
        
        for directory in directories:
            directory.mkdir(exist_ok=True)
    
    async def generate_signals_only(self) -> Optional[str]:
        """
        Generate signals without sending - for live generation mode
        
        Returns:
            Formatted signal text if successful, None otherwise
        """
        try:
            self.logger.info("Generating signals (live mode - no messaging)...")
            
            # Generate signals
            signal_result = await self.signal_generator.generate_forex_signals()
            
            if not signal_result or not signal_result.has_real_data:
                self.logger.warning("No valid signals generated")
                return None
            
            # Format signals
            formatted_message = self.signal_generator.format_signals_for_plaintext(signal_result)
            
            if not formatted_message:
                self.logger.warning("Message formatting failed")
                return None
            
            self.logger.info(f"Generated signals successfully ({len(signal_result.forex_alerts)} active)")
            return formatted_message
            
        except Exception as e:
            self.logger.error(f"Error in live signal generation: {e}")
            return None
    
    async def generate_and_send_daily_signals(self) -> bool:
        """
        Generate and send daily signals via configured messaging platforms
        
        Returns:
            True if successful, False otherwise
        """
        self.logger.info("=" * 80)
        self.logger.info(f"ENHANCED DAILY SIGNALS V2.0 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S PST')}")
        self.logger.info("=" * 80)
        self.logger.info("Features: Clean architecture, proper error handling, validated data")
        self.logger.info("Messaging: Signal + Telegram (no WhatsApp, no heatmaps)")
        self.logger.info("=" * 80)
        
        try:
            # Generate signals
            self.logger.info("Generating signals with enhanced system...")
            self.logger.info("   Multiple API fallbacks active")
            self.logger.info("   Price validation (3-source verification)")  
            self.logger.info("   Technical analysis (75% weight)")
            self.logger.info("   Economic analysis (20% weight)")
            self.logger.info("   Geopolitical analysis (5% weight)")
            
            signal_result = await self.signal_generator.generate_forex_signals()
            
            if not signal_result or not signal_result.has_real_data:
                self.logger.warning("No valid signals generated")
                self.logger.info("Data quality enforcement: No synthetic data fallback")
                return False
            
            # Log signal generation success
            self.logger.info(f"Generated {signal_result.active_signals} active signals from enhanced analysis")
            
            # Log first few signals for verification
            for signal in signal_result.forex_alerts[:3]:
                self.logger.info(f"   {signal.pair}: {signal.action.value} (confidence: {signal.confidence:.2f})")
            
            # Format message
            formatted_message = self.signal_generator.format_signals_for_plaintext(signal_result)
            
            if not formatted_message:
                self.logger.warning("Message formatting failed - skipping send")
                return False
            
            self.logger.info("Message formatted successfully")
            self.logger.info(f"Message length: {len(formatted_message)} characters")
            
            # Send via messaging platforms
            self.logger.info("Sending to configured messaging platforms...")
            
            messaging_result = await self.messaging_manager.send_message(
                message=formatted_message,
                platforms=['telegram', 'signal'],
                message_type='forex_signals'
            )
            
            # Evaluate results
            successful_platforms = [p for p, r in messaging_result.items() if r.success]
            failed_platforms = [p for p, r in messaging_result.items() if not r.success]
            
            if successful_platforms:
                self.logger.info(f"SUCCESS: Signals sent to {', '.join(successful_platforms)}")
                
                if failed_platforms:
                    self.logger.warning(f"PARTIAL: Failed on {', '.join(failed_platforms)}")
                else:
                    self.logger.info("COMPLETE SUCCESS: All platforms delivered")
                
                return True
            else:
                self.logger.error("FAILURE: All messaging platforms failed")
                for platform, result in messaging_result.items():
                    self.logger.error(f"   {platform}: {result.error}")
                return False
                
        except ForexSignalsError as e:
            self.logger.error(f"Forex signals error: {e}")
            if e.error_code:
                self.logger.error(f"   Error code: {e.error_code}")
            return False
        except Exception as e:
            self.logger.error(f"Unexpected error in signal processing: {e}", exc_info=True)
            return False
    
    def save_live_signals(self, signals_text: str) -> bool:
        """
        Save live signals to timestamped file
        
        Args:
            signals_text: Formatted signal text to save
            
        Returns:
            True if successful, False otherwise
        """
        try:
            timestamp = datetime.now().strftime('%Y-%m-%d_%H%M%S')
            output_file = Path(self.settings.output_dir) / f"live_signals_{timestamp}.txt"
            
            # Add generation footer
            enhanced_signals = signals_text + "\n\nGenerated via Enhanced API Signals V2.0 (--live mode)"
            
            # Write to file
            output_file.write_text(enhanced_signals, encoding='utf-8')
            
            # Update latest symlink
            latest_link = Path(self.settings.output_dir) / "latest_signals.txt"
            try:
                if latest_link.is_symlink() or latest_link.exists():
                    latest_link.unlink()
                
                # Create symlink with relative path
                latest_link.symlink_to(output_file.name)
            except Exception as e:
                self.logger.warning(f"Could not update latest symlink: {e}")
            
            self.logger.info(f"Live signals saved to: {output_file}")
            print(f"Signals saved to: {output_file}")
            print(f"Quick access: {latest_link}")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error saving live signals: {e}")
            print(f"Error saving live signals: {e}")
            return False


async def run_live_signals() -> bool:
    """
    Generate live signals without messaging
    
    Returns:
        True if successful, False otherwise
    """
    print("=" * 80)
    print(f"LIVE SIGNAL GENERATION V2.0 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S PST')}")
    print("=" * 80)
    print("Mode: Live generation (NO messaging)")
    print("Features: Clean architecture with validated data")
    print("=" * 80)
    
    try:
        # Initialize system
        system = EnhancedAPISignalsDailyV2()
        
        # Generate signals without sending
        signals_text = await system.generate_signals_only()
        
        if not signals_text:
            print("No valid signals generated")
            return False
        
        # Save to file
        success = system.save_live_signals(signals_text)
        
        if success:
            print("\nSignal Preview:")
            print("-" * 50)
            # Show first 15 lines of generated signals
            preview_lines = signals_text.split('\n')[:15]
            for line in preview_lines:
                print(line)
            if len(signals_text.split('\n')) > 15:
                print("... (see full output in file)")
            
            print("\nLive signal generation completed successfully!")
            return True
        else:
            print("Failed to save signals")
            return False
        
    except Exception as e:
        print(f"Live signal generation failed: {e}")
        return False


def run_daily_signals() -> bool:
    """
    Run scheduled daily signals execution
    
    Returns:
        True if successful, False otherwise
    """
    logger = get_logger(__name__)
    logger.info("Scheduled execution triggered - running enhanced daily signals V2.0")
    
    try:
        system = EnhancedAPISignalsDailyV2()
        success = asyncio.run(system.generate_and_send_daily_signals())
        
        if success:
            logger.info("Daily signals execution completed successfully")
        else:
            logger.error("Daily signals execution failed")
        
        return success
        
    except Exception as e:
        logger.error(f"Fatal error in daily signals: {e}", exc_info=True)
        return False


def main():
    """
    Main entry point with command line argument support
    """
    parser = argparse.ArgumentParser(
        description='Enhanced API-Based Daily Signals System V2.0',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s                    # Run daily signals (for cron)
  %(prog)s --live            # Generate live signals without messaging
  %(prog)s --test            # Test system without sending messages
        """
    )
    
    parser.add_argument('--live', action='store_true',
                       help='Generate live signals without messaging (saves to output directory)')
    parser.add_argument('--test', action='store_true',
                       help='Test signal generation without sending messages')
    
    args = parser.parse_args()
    
    if args.live:
        # Live signal generation mode
        print("Starting live signal generation mode V2.0...")
        success = asyncio.run(run_live_signals())
        sys.exit(0 if success else 1)
        
    elif args.test:
        # Test mode
        print("Testing signal generation system V2.0...")
        try:
            system = EnhancedAPISignalsDailyV2()
            success = asyncio.run(system.signal_generator.test_signal_generation())
            if success:
                print("System test passed!")
            else:
                print("System test failed!")
            sys.exit(0 if success else 1)
        except Exception as e:
            print(f"Test failed: {e}")
            sys.exit(1)
    else:
        # Default mode - run daily signals (for cron scheduling)
        logger = get_logger(__name__)
        logger.info("Enhanced API-Based Daily Signals System V2.0 Starting...")
        logger.info("Features: Clean architecture, proper error handling, validated data")
        logger.info("Platforms: Signal + Telegram only")
        
        success = run_daily_signals()
        
        if success:
            logger.info("Enhanced daily signals V2.0 completed successfully")
        else:
            logger.error("Enhanced daily signals V2.0 failed")
        
        sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()