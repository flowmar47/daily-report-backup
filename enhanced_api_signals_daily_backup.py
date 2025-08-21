#!/usr/bin/env python3
"""
Enhanced API-Based Daily Signals System
- Incorporates all improvements: fallback APIs, enhanced analysis, structured formatting
- Uses validated pricing with 3-source verification
- Technical 75%, Economic 20%, Geopolitical 5% analysis weights
- Scheduled for 6 AM PST weekdays
- NO web scraping, NO heatmaps, NO WhatsApp
- Signal and Telegram messaging only with structured plaintext format
"""

import asyncio
import logging
import sys
import os
import argparse
from datetime import datetime
from typing import Dict, Any, Optional
from pathlib import Path

# Setup logging with proper encoding
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/enhanced_api_signals.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Ensure required directories exist
os.makedirs('logs', exist_ok=True)
os.makedirs('LiveSignals', exist_ok=True)

class EnhancedAPISignalsDaily:
    """Enhanced API-based daily signals system with all improvements"""
    
    def __init__(self):
        logger.info("🚀 Initializing Enhanced API-based Daily Signals System...")
        
        # Add paths for imports
        sys.path.append(os.path.dirname(__file__))
        sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))
        
        # Import our enhanced components
        try:
            from forex_signal_integration import ForexSignalIntegration
            self.signal_integration = ForexSignalIntegration()
            
            if not self.signal_integration.setup_successful:
                raise Exception("Forex signal integration setup failed")
                
            logger.info("✅ Enhanced signal generation system initialized")
            
            # Import structured template generator for proper formatting
            try:
                from src.data_processors.template_generator import StructuredTemplateGenerator
                self.template_generator = StructuredTemplateGenerator()
                logger.info("✅ Structured template generator loaded")
            except ImportError:
                logger.warning("⚠️ Template generator not available, using manual formatting")
                self.template_generator = None
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize enhanced system: {e}")
            raise
    
    async def generate_signals_only(self) -> Optional[str]:
        """Generate signals without sending - for live generation"""
        
        try:
            logger.info("🔍 Generating signals (live mode - no messaging)...")
            
            signal_data = await self.signal_integration.generate_forex_signals()
            
            if not signal_data or not signal_data.get('has_real_data'):
                logger.warning("⚠️ No valid signals generated from enhanced system")
                return None
            
            # Format using enhanced template
            message = self._format_enhanced_message(signal_data)
            return message
            
        except Exception as e:
            logger.error(f"❌ Error in signal generation (live mode): {e}")
            return None
    
    async def generate_and_send_daily_signals(self) -> bool:
        """Generate enhanced signals and send with structured formatting"""
        
        logger.info("=" * 80)
        logger.info(f"📊 ENHANCED DAILY SIGNALS - {datetime.now().strftime('%Y-%m-%d %H:%M:%S PST')}")
        logger.info("=" * 80)
        logger.info("🔧 Features: Fallback APIs, 3-source validation, Technical 75% + Economic 20%")
        logger.info("📡 Messaging: Signal + Telegram only (no WhatsApp, no heatmaps)")
        logger.info("=" * 80)
        
        try:
            # Generate signals using enhanced system with fallback APIs
            logger.info("🔍 Generating signals with enhanced API system...")
            logger.info("   ✅ Multiple API fallbacks active")
            logger.info("   ✅ Price validation (3-source verification)")
            logger.info("   ✅ Technical analysis (75% weight)")
            logger.info("   ✅ Economic analysis (20% weight)")
            logger.info("   ✅ Geopolitical analysis (5% weight)")
            
            signal_data = await self.signal_integration.generate_forex_signals()
            
            if not signal_data or not signal_data.get('has_real_data'):
                logger.warning("⚠️ No valid signals generated from enhanced system")
                logger.info("🔒 Real data enforcement: No synthetic data fallback allowed")
                return False
            
            # Log signal generation success
            signals = signal_data.get('signals', signal_data.get('forex_alerts', []))
            logger.info(f"✅ Generated {len(signals)} signals from enhanced analysis")
            
            for signal in signals[:3]:  # Log first 3 signals
                pair = signal.get('pair', 'Unknown')
                action = signal.get('action', 'Unknown')
                confidence = signal.get('confidence', 0)
                logger.info(f"   📈 {pair}: {action} (confidence: {confidence:.2f})")
            
            # Format using structured template (exact plaintext spec)
            message = self._format_enhanced_message(signal_data)
            
            if not message:
                logger.warning("⚠️ Message formatting failed - skipping send")
                return False
            
            logger.info("📝 Message formatted with structured template")
            logger.info(f"📏 Message length: {len(message)} characters")
            
            # Send to both platforms
            logger.info("📤 Sending to Signal and Telegram...")
            telegram_success = self._send_to_telegram(message)
            signal_success = self._send_to_signal(message)
            
            # Handle results
            telegram_ok = telegram_success
            signal_ok = signal_success
            
            # Log detailed results
            if telegram_ok and signal_ok:
                logger.info("🎉 SUCCESS: Enhanced signals sent to BOTH platforms!")
                return True
            elif telegram_ok or signal_ok:
                logger.warning(f"⚠️ PARTIAL SUCCESS: Telegram={telegram_ok}, Signal={signal_ok}")
                return True
            else:
                logger.error("💥 FAILURE: Enhanced signals failed on all platforms")
                return False
                
        except Exception as e:
            logger.error(f"❌ Error in enhanced signal processing: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def _format_enhanced_message(self, signal_data: Dict[str, Any]) -> Optional[str]:
        """Format signals using enhanced structured template"""
        
        try:
            # Use structured template generator for exact plaintext format if available
            if self.template_generator:
                structured_message = self.template_generator.generate_structured_message(signal_data)
                
                if structured_message and len(structured_message) > 50:
                    logger.info("✅ Using structured template generator output")
                    return structured_message
            
            # Fallback to manual formatting if template fails or not available
            logger.warning("⚠️ Template generator not available or failed, using manual formatting")
            return self._manual_format_message(signal_data)
            
        except Exception as e:
            logger.error(f"❌ Enhanced formatting error: {e}")
            return self._manual_format_message(signal_data)
    
    def _manual_format_message(self, signal_data: Dict[str, Any]) -> Optional[str]:
        """Manual message formatting as fallback"""
        
        try:
            # Get signals from either format
            signals = signal_data.get('signals', signal_data.get('forex_alerts', []))
            
            if not signals:
                return None
            
            # Create structured message (exact plaintext specification)
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M PST')
            message_lines = [
                "FOREX TRADING SIGNALS",
                f"Generated: {timestamp}",
                "",
                "FOREX PAIRS",
                ""
            ]
            
            # Add each signal in exact format
            for signal in signals:
                if signal.get('action') == 'HOLD':
                    continue
                
                pair = signal.get('pair', 'Unknown')
                entry_price = signal.get('entry_price', signal.get('average', 0))
                target_price = signal.get('target_price', signal.get('exit_price', signal.get('exit', 0)))
                action = signal.get('action', 'Unknown')
                confidence = signal.get('confidence', 0)
                
                # Skip signals with None prices instead of using defaults
                if entry_price is None or target_price is None or entry_price == 0 or target_price == 0:
                    logger.warning(f"⚠️ Skipping {pair} signal due to None/zero prices: entry={entry_price}, target={target_price}")
                    continue
                
                # Calculate high/low based on action
                if action == 'BUY':
                    high_price = target_price if target_price > entry_price else entry_price * 1.001
                    low_price = entry_price
                else:  # SELL
                    high_price = entry_price
                    low_price = target_price if target_price < entry_price else entry_price * 0.999
                
                message_lines.extend([
                    f"Pair: {pair}",
                    f"High: {high_price:.5f}" if high_price is not None else "High: N/A",
                    f"Average: {entry_price:.5f}" if entry_price is not None else "Average: N/A",
                    f"Low: {low_price:.5f}" if low_price is not None else "Low: N/A",
                    f"MT4 Action: MT4 {action}",
                    f"Exit: {target_price:.5f}" if target_price is not None else "Exit: N/A",
                    ""
                ])
            
            # Add footer
            message_lines.extend([
                f"Enhanced API Analysis - {len([s for s in signals if s.get('action') != 'HOLD'])} signals",
                "Real market data from validated sources"
            ])
            
            return "\n".join(message_lines)
            
        except Exception as e:
            logger.error(f"❌ Manual formatting error: {e}")
            return None
    
    def _send_to_telegram(self, message: str) -> bool:
        """Send message to Telegram with enhanced error handling"""
        try:
            from dotenv import load_dotenv
            load_dotenv()
            
            import requests
            
            bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
            chat_id = os.getenv('TELEGRAM_GROUP_ID')
            
            if not bot_token or not chat_id:
                logger.error("❌ Telegram credentials not configured")
                return False
            
            url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
            data = {
                'chat_id': chat_id,
                'text': message,
                'parse_mode': 'HTML'
            }
            
            response = requests.post(url, data=data, timeout=30)
            
            if response.status_code == 200:
                logger.info("✅ Telegram: Enhanced signals delivered successfully")
                return True
            else:
                logger.error(f"❌ Telegram failed: {response.status_code} - {response.text}")
                return False
                    
        except Exception as e:
            logger.error(f"❌ Telegram send error: {e}")
            return False
    
    def _send_to_signal(self, message: str) -> bool:
        """Send message to Signal with enhanced error handling"""
        try:
            from dotenv import load_dotenv
            load_dotenv()
            
            import requests
            
            phone = os.getenv('SIGNAL_PHONE_NUMBER')
            group_id = os.getenv('SIGNAL_GROUP_ID')
            
            if not phone or not group_id:
                logger.error("❌ Signal credentials not configured")
                return False
            
            # Signal CLI Docker API endpoint
            url = "http://localhost:8080/v2/send"
            data = {
                'number': phone,
                'recipients': [group_id],
                'message': message
            }
            
            response = requests.post(url, json=data, timeout=30)
            
            if response.status_code == 201:
                logger.info("✅ Signal: Enhanced signals delivered successfully")
                return True
            else:
                logger.error(f"❌ Signal failed: {response.status_code} - {response.text}")
                return False
                    
        except Exception as e:
            logger.error(f"❌ Signal send error: {e}")
            return False
    
    def save_live_signals(self, signals_text: str) -> bool:
        """Save live signals to timestamped file in LiveSignals directory"""
        
        try:
            file_timestamp = datetime.now().strftime('%Y-%m-%d_%H%M%S')
            output_file = f"LiveSignals/live_signals_{file_timestamp}.txt"
            
            # Add live generation footer
            enhanced_signals = signals_text + "\n\nGenerated via Enhanced API Signals (--live mode)"
            
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(enhanced_signals)
            
            # Update latest symlink
            latest_link = "LiveSignals/latest_signals.txt"
            try:
                if os.path.islink(latest_link):
                    os.unlink(latest_link)
                elif os.path.exists(latest_link):
                    os.remove(latest_link)
                
                # Create symlink with relative path
                relative_path = os.path.basename(output_file)
                os.symlink(relative_path, latest_link)
            except Exception as e:
                logger.warning(f"⚠️ Could not update latest symlink: {e}")
            
            logger.info(f"💾 Live signals saved to: {output_file}")
            print(f"💾 Signals saved to: {output_file}")
            print(f"📄 Quick access: LiveSignals/latest_signals.txt")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Error saving live signals: {e}")
            print(f"❌ Error saving live signals: {e}")
            return False

async def run_live_signals() -> bool:
    """Generate live signals without messaging"""
    
    print("=" * 80)
    print(f"🔍 LIVE SIGNAL GENERATION - {datetime.now().strftime('%Y-%m-%d %H:%M:%S PST')}")
    print("=" * 80)
    print("💾 Mode: Live generation (NO messaging)")
    print("🔧 Features: Same analysis as scheduled system")
    print("=" * 80)
    
    try:
        automation = EnhancedAPISignalsDaily()
        
        # Generate signals without sending
        signals_text = await automation.generate_signals_only()
        
        if not signals_text:
            print("❌ No valid signals generated")
            return False
        
        # Save to file
        success = automation.save_live_signals(signals_text)
        
        if success:
            print("\n📊 Signal Preview:")
            print("-" * 50)
            # Show first 15 lines of generated signals
            preview_lines = signals_text.split('\n')[:15]
            for line in preview_lines:
                print(line)
            if len(signals_text.split('\n')) > 15:
                print("... (see full output in file)")
            
            print("\n✅ Live signal generation completed successfully!")
            return True
        else:
            print("❌ Failed to save signals")
            return False
        
    except Exception as e:
        logger.error(f"❌ Error in live signal generation: {e}")
        print(f"❌ Live signal generation failed: {e}")
        return False

def run_daily_signals():
    """Wrapper function for scheduled execution"""
    logger.info("🕕 Scheduled execution triggered - running enhanced daily signals")
    
    automation = EnhancedAPISignalsDaily()
    success = asyncio.run(automation.generate_and_send_daily_signals())
    
    if success:
        logger.info("✅ Daily signals execution completed successfully")
    else:
        logger.error("❌ Daily signals execution failed")
    
    return success

def main():
    """Main entry point with --live flag support (cron handles scheduling)"""
    
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Enhanced API-Based Daily Signals System')
    parser.add_argument('--live', action='store_true', 
                       help='Generate live signals without messaging (saves to LiveSignals directory)')
    args = parser.parse_args()
    
    if args.live:
        # Live signal generation mode
        print("Starting live signal generation mode...")
        success = asyncio.run(run_live_signals())
        if success:
            print("Live signal generation completed successfully!")
            sys.exit(0)
        else:
            print("Live signal generation failed!")
            sys.exit(1)
    else:
        # Default mode - run daily signals once (cron handles scheduling)
        logger.info("🚀 Enhanced API-Based Daily Signals System Starting...")
        logger.info("🔧 Features: Fallback APIs, validated pricing, structured messaging")
        logger.info("📡 Platforms: Signal + Telegram only")
        
        # Run daily signals (called by cron)
        success = run_daily_signals()
        
        if success:
            logger.info("✅ Enhanced daily signals completed successfully")
            sys.exit(0)
        else:
            logger.error("❌ Enhanced daily signals failed")
            sys.exit(1)

if __name__ == "__main__":
    main()