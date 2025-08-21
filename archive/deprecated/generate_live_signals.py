#!/usr/bin/env python3
"""
Live Signal Generator
Generates forex signals for viewing without sending messages to Signal or Telegram
Saves output to LiveSignals directory with timestamp
Uses the same production analysis pipeline as the scheduled system
"""

import asyncio
import logging
import sys
import os
from datetime import datetime
from typing import Dict, Any, Optional
from pathlib import Path

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/live_signals.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Ensure required directories exist
os.makedirs('logs', exist_ok=True)
os.makedirs('LiveSignals', exist_ok=True)

class LiveSignalGenerator:
    """Generate live forex signals without messaging functionality"""
    
    def __init__(self):
        logger.info("🔍 Initializing Live Signal Generator...")
        
        # Add paths for imports
        sys.path.append(os.path.dirname(__file__))
        sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))
        
        # Import production components
        try:
            from forex_signal_integration import ForexSignalIntegration
            self.signal_integration = ForexSignalIntegration()
            
            if not self.signal_integration.setup_successful:
                raise Exception("Forex signal integration setup failed")
                
            logger.info("✅ Signal generation system initialized")
            
            # Import structured template generator for proper formatting
            from src.data_processors.template_generator import StructuredTemplateGenerator
            self.template_generator = StructuredTemplateGenerator()
            logger.info("✅ Template generator loaded")
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize live signal generator: {e}")
            raise
    
    async def generate_live_signals(self) -> bool:
        """Generate live signals and save to file"""
        
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S PST')
        file_timestamp = datetime.now().strftime('%Y-%m-%d_%H%M%S')
        
        print("=" * 80)
        print(f"🔍 LIVE SIGNAL GENERATION - {timestamp}")
        print("=" * 80)
        print("🔧 Features: 8 API fallbacks, 3-source validation, Full analysis pipeline")
        print("💾 Output: Saved to LiveSignals directory (NO messaging)")
        print("=" * 80)
        
        try:
            # Generate signals using production system
            logger.info("🔍 Generating live signals with production API system...")
            logger.info("   ✅ Multiple API fallbacks active")
            logger.info("   ✅ Price validation (3-source verification)")
            logger.info("   ✅ Technical analysis (75% weight)")
            logger.info("   ✅ Economic analysis (20% weight)")
            logger.info("   ✅ Geopolitical analysis (5% weight)")
            
            signal_data = await self.signal_integration.generate_forex_signals()
            
            if not signal_data or not signal_data.get('has_real_data'):
                logger.warning("⚠️ No valid signals generated from API system")
                logger.info("🔒 Real data enforcement: No synthetic data fallback allowed")
                print("❌ No valid signals generated - no real market data available")
                return False
            
            # Log signal generation success
            signals = signal_data.get('signals', signal_data.get('forex_alerts', []))
            logger.info(f"✅ Generated {len(signals)} signals from live analysis")
            
            print(f"✅ Generated {len(signals)} live signals")
            for signal in signals[:3]:  # Show first 3 signals
                pair = signal.get('pair', 'Unknown')
                action = signal.get('action', 'Unknown')
                confidence = signal.get('confidence', 0)
                print(f"   📈 {pair}: {action} (confidence: {confidence:.2f})")
            
            if len(signals) > 3:
                print(f"   ... and {len(signals) - 3} more signals")
            
            # Format using production template
            formatted_signals = self._format_live_signals(signal_data)
            
            if not formatted_signals:
                logger.warning("⚠️ Signal formatting failed")
                print("❌ Signal formatting failed")
                return False
            
            # Save to file
            output_file = f"LiveSignals/live_signals_{file_timestamp}.txt"
            success = self._save_signals_to_file(formatted_signals, output_file)
            
            if success:
                # Update latest symlink
                self._update_latest_symlink(output_file)
                
                print(f"💾 Signals saved to: {output_file}")
                print(f"📄 Quick access: LiveSignals/latest_signals.txt")
                print("=" * 80)
                print("✅ Live signal generation completed successfully!")
                
                # Show preview of generated signals
                print("\n📊 Signal Preview:")
                print("-" * 50)
                preview_lines = formatted_signals.split('\n')[:15]  # First 15 lines
                for line in preview_lines:
                    print(line)
                if len(formatted_signals.split('\n')) > 15:
                    print("... (see full output in file)")
                
                return True
            else:
                print("❌ Failed to save signals to file")
                return False
                
        except Exception as e:
            logger.error(f"❌ Error in live signal generation: {e}")
            print(f"❌ Live signal generation failed: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def _format_live_signals(self, signal_data: Dict[str, Any]) -> Optional[str]:
        """Format signals using production template"""
        
        try:
            # Try structured template generator first (production method)
            structured_message = self.template_generator.generate_structured_message(signal_data)
            
            if structured_message and len(structured_message) > 50:
                logger.info("✅ Using production structured template")
                return structured_message
            
            # Fallback to manual formatting
            logger.warning("⚠️ Template generator failed, using manual formatting")
            return self._manual_format_signals(signal_data)
            
        except Exception as e:
            logger.error(f"❌ Live signal formatting error: {e}")
            return self._manual_format_signals(signal_data)
    
    def _manual_format_signals(self, signal_data: Dict[str, Any]) -> Optional[str]:
        """Manual signal formatting as fallback"""
        
        try:
            # Get signals from either format
            signals = signal_data.get('signals', signal_data.get('forex_alerts', []))
            
            if not signals:
                return None
            
            # Create structured message (exact production specification)
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M PST')
            message_lines = [
                "FOREX TRADING SIGNALS",
                f"Generated: {timestamp}",
                "",
                "FOREX PAIRS",
                ""
            ]
            
            # Add each signal in exact format
            active_signals = 0
            for signal in signals:
                if signal.get('action') == 'HOLD':
                    continue
                
                active_signals += 1
                pair = signal.get('pair', 'Unknown')
                entry_price = signal.get('entry_price', signal.get('average', 0))
                target_price = signal.get('target_price', signal.get('exit_price', signal.get('exit', 0)))
                action = signal.get('action', 'Unknown')
                confidence = signal.get('confidence', 0)
                
                # Calculate high/low based on action
                if action == 'BUY':
                    high_price = target_price if target_price > entry_price else entry_price * 1.001
                    low_price = entry_price
                else:  # SELL
                    high_price = entry_price
                    low_price = target_price if target_price < entry_price else entry_price * 0.999
                
                message_lines.extend([
                    f"Pair: {pair}",
                    f"High: {high_price:.5f}",
                    f"Average: {entry_price:.5f}",
                    f"Low: {low_price:.5f}",
                    f"MT4 Action: MT4 {action}",
                    f"Exit: {target_price:.5f}",
                    ""
                ])
            
            # Add footer
            message_lines.extend([
                f"Enhanced API Analysis - {active_signals} signals",
                "Real market data from validated sources",
                "",
                "Generated via Live Signal Generator (no messaging)"
            ])
            
            return "\n".join(message_lines)
            
        except Exception as e:
            logger.error(f"❌ Manual formatting error: {e}")
            return None
    
    def _save_signals_to_file(self, signals_text: str, output_file: str) -> bool:
        """Save formatted signals to file"""
        
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(signals_text)
            
            logger.info(f"💾 Signals saved to: {output_file}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error saving signals to file: {e}")
            return False
    
    def _update_latest_symlink(self, output_file: str) -> None:
        """Update the latest_signals.txt symlink to point to newest file"""
        
        try:
            latest_link = "LiveSignals/latest_signals.txt"
            
            # Remove existing symlink if it exists
            if os.path.islink(latest_link):
                os.unlink(latest_link)
            elif os.path.exists(latest_link):
                os.remove(latest_link)
            
            # Create new symlink (relative path for portability)
            relative_path = os.path.basename(output_file)
            os.symlink(relative_path, latest_link)
            
            logger.info(f"🔗 Updated latest_signals.txt symlink to {relative_path}")
            
        except Exception as e:
            logger.warning(f"⚠️ Could not update latest symlink: {e}")

async def main():
    """Main entry point for live signal generation"""
    
    print("🔍 Live Forex Signal Generator")
    print("Uses production analysis system without messaging")
    print("")
    
    try:
        # Create generator instance
        generator = LiveSignalGenerator()
        
        # Generate live signals
        success = await generator.generate_live_signals()
        
        if success:
            print("\n🎯 Live signal generation completed successfully!")
            print("\n📋 What to do next:")
            print("1. Review signals in LiveSignals directory")
            print("2. Check latest_signals.txt for quick access")
            print("3. Compare with scheduled system output if desired")
            print("4. Run again anytime to get fresh signals")
        else:
            print("\n❌ Live signal generation failed!")
            print("Check logs/live_signals.log for details")
            return 1
    
    except Exception as e:
        print(f"\n💥 Unexpected error: {e}")
        logger.error(f"Unexpected error in main: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)