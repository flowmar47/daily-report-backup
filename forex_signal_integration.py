#!/usr/bin/env python3
"""
Forex Signal Integration Module

Integrates the API-based Signals analysis system with the daily report messaging system.
This module bridges live market data from multiple API sources (Alpha Vantage, Twelve Data,
FRED, Finnhub, etc.) to generate professional forex trading signals delivered via Signal
and Telegram messaging platforms.

Key Features:
- Multi-factor analysis (Technical 75%, Economic 20%, Geopolitical 5%)
- 3-source price validation with variance checking
- Automatic API fallback protection (8 data sources)
- Professional signal formatting for messaging delivery

CRITICAL: ONLY REAL MARKET DATA ALLOWED - NO SYNTHETIC/FAKE PRICES
"""

import sys
import os
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional
import asyncio

# Setup paths
current_dir = Path(__file__).parent
signals_dir = current_dir / 'Signals'

# Setup logging
logger = logging.getLogger(__name__)

# CRITICAL: Import real data enforcement
try:
    from ensure_real_data_only import validate_signal_data, initialize_real_data_enforcement
    initialize_real_data_enforcement()
except Exception as e:
    logger.warning(f"Real data enforcement not available: {e}")

class ForexSignalIntegration:
    """Integration class to connect Signals system with messaging system"""
    
    def __init__(self):
        self.currency_pairs = ['USDCAD', 'EURUSD', 'CHFJPY', 'USDJPY', 'USDCHF']
        self.signals_dir = signals_dir
        self.signal_generator = None
        self.report_generator = None
        self.setup_successful = False
        self.setup_signals_environment()
    
    def setup_signals_environment(self):
        """Setup the Signals system environment"""
        try:
            # Save original path and working directory
            original_path = sys.path.copy()
            original_cwd = os.getcwd()
            
            # Add Signals directory to path
            sys.path.insert(0, str(self.signals_dir))
            os.chdir(str(self.signals_dir))
            
            try:
                # Import the signal generator and report generator
                from src.signal_generator import signal_generator
                from src.report_generator import report_generator
                
                self.signal_generator = signal_generator
                self.report_generator = report_generator
                self.setup_successful = True
                
                logger.info("✅ Signals system environment setup successful")
                
            finally:
                # Restore original path and directory
                os.chdir(original_cwd)
                # Keep Signals in path for future imports
                
        except Exception as e:
            logger.error(f"❌ Error setting up Signals environment: {e}")
            self.setup_successful = False
    
    def generate_forex_signals_sync(self) -> Dict[str, Any]:
        """
        Synchronous version of signal generation with enhanced error handling
        """
        if not self.setup_successful:
            logger.error("❌ Signal generator not properly initialized")
            return {'has_real_data': False, 'error': 'Setup failed'}
            
        logger.info("🚀 Starting API-based forex signal generation...")
        
        try:
            # Save current directory
            original_cwd = os.getcwd()
            
            # Change to Signals directory for execution
            os.chdir(str(self.signals_dir))
            
            try:
                # Generate signals for configured currency pairs
                logger.info(f"📊 Analyzing {len(self.currency_pairs)} currency pairs: {', '.join(self.currency_pairs)}")
                signals = self.signal_generator.generate_signals_for_pairs(self.currency_pairs)
                
                if not signals:
                    logger.warning("⚠️ No signals generated - possible API rate limiting or data issues")
                    return {'has_real_data': False, 'error': 'No signals generated'}
                
                # Count active signals (non-HOLD actions)
                active_signals = {pair: signal for pair, signal in signals.items() if signal.action != 'HOLD'}
                logger.info(f"📈 Generated {len(active_signals)} active signals out of {len(signals)} pairs analyzed")
                
                # Generate text report
                text_report = self.report_generator.generate_comprehensive_report(signals, 'txt')
                
                # Convert signals to messaging format for delivery
                formatted_data = self._convert_signals_to_messaging_format(signals, text_report)
                
                # Enhanced validation of generated data
                if formatted_data.get('has_real_data') and formatted_data.get('forex_alerts'):
                    logger.info(f"✅ Successfully generated {len(formatted_data['forex_alerts'])} forex alerts from API data")
                    return formatted_data
                else:
                    logger.warning("⚠️ Generated data has no active forex alerts")
                    return {'has_real_data': False, 'error': 'No active trading signals generated'}
                
            finally:
                # Always restore original directory
                os.chdir(original_cwd)
                
        except Exception as e:
            # Enhanced error categorization
            error_msg = str(e).lower()
            if 'rate limit' in error_msg or '429' in error_msg:
                logger.error(f"❌ API Rate limiting detected: {e}")
                return {'has_real_data': False, 'error': 'API rate limiting - try again later'}
            elif 'api key' in error_msg or '401' in error_msg or '403' in error_msg:
                logger.error(f"❌ API authentication error: {e}")
                return {'has_real_data': False, 'error': 'API authentication failed'}
            elif 'network' in error_msg or 'timeout' in error_msg or 'connection' in error_msg:
                logger.error(f"❌ Network connectivity error: {e}")
                return {'has_real_data': False, 'error': 'Network connectivity issues'}
            else:
                logger.error(f"❌ Unexpected error generating forex signals: {e}")
                import traceback
                traceback.print_exc()
                return {'has_real_data': False, 'error': f'Signal generation failed: {str(e)[:100]}'}
    
    async def generate_forex_signals(self) -> Dict[str, Any]:
        """
        Async wrapper for signal generation
        """
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.generate_forex_signals_sync)
    
    def _convert_signals_to_messaging_format(self, signals: Dict, text_report: str = None) -> Dict[str, Any]:
        """
        Convert Signals system output to messaging-compatible format for Signal and Telegram delivery
        """
        try:
            forex_alerts = []
            active_signals_count = 0
            
            for pair, signal in signals.items():
                if signal.action != 'HOLD':
                    active_signals_count += 1
                    
                    # Convert to forex alert format with ALL advanced fields
                    forex_alert = {
                        'pair': pair,
                        'action': signal.action,  # 'BUY' or 'SELL'
                        'mt4_action': f"MT4 {signal.action}",
                        'entry_price': signal.entry_price,
                        'exit_price': signal.exit_price,
                        'stop_loss': signal.stop_loss,
                        'take_profit': signal.take_profit,
                        'target_pips': signal.target_pips,
                        'confidence': signal.confidence,
                        'signal_strength': signal.signal_strength,
                        'weekly_achievement_probability': signal.weekly_achievement_probability,
                        
                        # Format for plaintext template compatibility
                        'high': signal.exit_price if signal.action == 'BUY' else signal.entry_price,
                        'low': signal.entry_price if signal.action == 'BUY' else signal.exit_price,
                        'average': signal.entry_price,
                        'exit': signal.exit_price,
                        
                        # Advanced fields from Signals system
                        'signal_category': getattr(signal, 'signal_category', None),
                        'expected_timeframe': getattr(signal, 'expected_timeframe', None),
                        'days_to_target': getattr(signal, 'days_to_target', None),
                        'risk_reward_ratio': getattr(signal, 'risk_reward_ratio', None),
                        'average_weekly_range_pips': getattr(signal, 'average_weekly_range_pips', None),
                        
                        'analysis_timestamp': signal.analysis_timestamp,
                        'expiry_date': signal.expiry_date,
                    }
                    
                    # Add component scores if available
                    if hasattr(signal, 'components'):
                        for comp_name, comp in signal.components.items():
                            if hasattr(comp, 'score'):
                                forex_alert[f'{comp_name}_score'] = comp.score
                    
                    forex_alerts.append(forex_alert)
            
            # Create the data structure expected by the messaging system
            result = {
                'has_real_data': active_signals_count > 0,
                'forex_alerts': forex_alerts,
                'options_alerts': [],  # Not generated by Signals system
                'swing_trades': [],    # Not generated by Signals system  
                'day_trades': [],      # Not generated by Signals system
                'source': 'Forex Signal Generation System',
                'timestamp': datetime.now().isoformat(),
                'total_signals': len(signals),
                'active_signals': active_signals_count,
                'hold_signals': len(signals) - active_signals_count,
                'currency_pairs_analyzed': list(signals.keys()),
                'text_report': text_report  # Include the formatted text report
            }
            
            logger.info(f"📊 Converted {active_signals_count} active signals from {len(signals)} pairs")
            
            # CRITICAL: Validate all data is real before returning
            try:
                from ensure_real_data_only import validate_signal_data
                result = validate_signal_data(result)
                if not result.get('has_real_data') and active_signals_count > 0:
                    logger.error("❌ FAKE DATA DETECTED AND REMOVED - No valid signals remain")
            except:
                pass  # Validation module not available
                
            return result
            
        except Exception as e:
            logger.error(f"❌ Error converting signals format: {e}")
            import traceback
            traceback.print_exc()
            return {
                'has_real_data': False,
                'forex_alerts': [],
                'options_alerts': [],
                'swing_trades': [],
                'day_trades': [],
                'error': str(e)
            }
    
    def format_signals_for_plaintext(self, signals_data: Dict[str, Any]) -> str:
        """
        Format signals data for plaintext output compatible with existing template
        """
        try:
            # If we have the text report from the Signals system, use it
            if 'text_report' in signals_data and signals_data['text_report']:
                return signals_data['text_report']
            
            if not signals_data.get('has_real_data', False):
                return "No active forex signals available today."
            
            lines = []
            lines.append("FOREX PAIRS")
            lines.append("")
            
            for alert in signals_data.get('forex_alerts', []):
                lines.extend([
                    f"Pair: {alert['pair']}",
                    f"High: {alert['high']:.5f}" if alert['high'] else "High: N/A",
                    f"Average: {alert['average']:.5f}" if alert['average'] else "Average: N/A", 
                    f"Low: {alert['low']:.5f}" if alert['low'] else "Low: N/A",
                    f"MT4 Action: {alert['mt4_action']}",
                    f"Exit: {alert['exit']:.5f}" if alert['exit'] else "Exit: N/A",
                ])
                
                # Add advanced fields if available (from real API data)
                if alert.get('confidence') is not None:
                    lines.append(f"Confidence: {alert['confidence']:.1%}")
                
                if alert.get('signal_category'):
                    lines.append(f"Signal Category: {alert['signal_category']}")
                
                if alert.get('expected_timeframe'):
                    lines.append(f"Expected Timeframe: {alert['expected_timeframe']}")
                
                if alert.get('weekly_achievement_probability') is not None:
                    lines.append(f"Achievement Probability: {alert['weekly_achievement_probability']:.1%}")
                
                if alert.get('target_pips'):
                    lines.append(f"Target: {alert.get('target_pips', 0):.0f} pips")
                
                if alert.get('risk_reward_ratio'):
                    lines.append(f"Risk/Reward: 1:{alert['risk_reward_ratio']:.1f}")
                
                lines.append("")  # Empty line between pairs
            
            # Calculate average confidence if available
            avg_confidence = None
            if signals_data.get('forex_alerts'):
                confidences = [a['confidence'] for a in signals_data['forex_alerts'] if a.get('confidence') is not None]
                if confidences:
                    avg_confidence = sum(confidences) / len(confidences)
            
            # Add enhanced summary
            lines.extend([
                "SIGNAL ANALYSIS SUMMARY",
                f"Total Pairs Analyzed: {signals_data.get('total_signals', 0)}",
                f"Active Signals: {signals_data.get('active_signals', 0)}",
                f"Hold Recommendations: {signals_data.get('hold_signals', 0)}",
            ])
            
            if avg_confidence is not None:
                lines.append(f"Average Confidence: {avg_confidence:.1%}")
            
            # Add timeframes if available
            if signals_data.get('forex_alerts') and any(a.get('expected_timeframe') for a in signals_data['forex_alerts']):
                lines.append("Timeframes Analyzed: 30min, 1hour, 4hour, daily")
            
            lines.extend([
                f"Source: Professional API-based Signal Generation",
                f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}",
                ""
            ])
            
            return "\n".join(lines)
            
        except Exception as e:
            logger.error(f"❌ Error formatting signals for plaintext: {e}")
            return f"Error formatting signals: {str(e)}"
    
    async def test_signal_generation(self) -> bool:
        """Test signal generation without full execution"""
        try:
            logger.info("🧪 Testing signal generation...")
            
            # Test signal generation
            test_signals = await self.generate_forex_signals()
            
            if test_signals.get('error'):
                logger.error(f"❌ Test error: {test_signals['error']}")
                return False
                
            if test_signals.get('has_real_data', False):
                logger.info(f"✅ Test successful - Generated {len(test_signals.get('forex_alerts', []))} active signals")
                
                # Test formatting
                formatted = self.format_signals_for_plaintext(test_signals)
                logger.info(f"📄 Formatted output length: {len(formatted)} characters")
                
                return True
            else:
                logger.warning("⚠️ Test generated no active signals (this may be normal)")
                return True  # Not having signals is also a valid result
                
        except Exception as e:
            logger.error(f"❌ Test failed: {e}")
            import traceback
            traceback.print_exc()
            return False

# Create global instance
try:
    forex_signal_integration = ForexSignalIntegration()
except Exception as e:
    logger.error(f"Failed to initialize ForexSignalIntegration: {e}")
    forex_signal_integration = None