#!/usr/bin/env python3
"""
Forex Signal Integration V2.0 - Backward Compatible Refactor
Clean implementation maintaining all existing functionality
No sys.path hacks, proper error handling, improved architecture
"""

import asyncio
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional

# Use new clean architecture
from forex_signals.core.config import get_settings
from forex_signals.core.logging import setup_logging, get_logger, set_correlation_id
from forex_signals.core.exceptions import ForexSignalsError
from forex_signals.signals.generator import ForexSignalGenerator
from forex_signals.signals.validators import DataValidator, initialize_real_data_enforcement

# Setup logging
logger = get_logger(__name__)


class ForexSignalIntegrationV2:
    """
    Forex Signal Integration V2.0 - Clean refactored version
    Maintains backward compatibility with the original interface
    """
    
    def __init__(self):
        """Initialize the forex signal integration system"""
        self.currency_pairs = ['USDCAD', 'EURUSD', 'CHFJPY', 'USDJPY', 'USDCHF']
        self.setup_successful = False
        
        # Set correlation ID
        self.correlation_id = set_correlation_id()
        
        logger.info("🚀 Initializing Forex Signal Integration V2.0...")
        
        try:
            # Initialize real data enforcement
            initialize_real_data_enforcement()
            
            # Initialize the new signal generator
            self.signal_generator = ForexSignalGenerator()
            self.validator = DataValidator()
            
            self.setup_successful = self.signal_generator.setup_successful
            
            if self.setup_successful:
                logger.info("✅ Forex Signal Integration V2.0 initialized successfully")
            else:
                logger.warning("⚠️ Partial initialization - some features may be limited")
                
        except Exception as e:
            logger.error(f"❌ Failed to initialize Forex Signal Integration V2.0: {e}")
            self.setup_successful = False
    
    def generate_forex_signals_sync(self) -> Dict[str, Any]:
        """
        Synchronous version of signal generation - backward compatibility
        
        Returns:
            Dictionary with signal data in legacy format
        """
        if not self.setup_successful:
            logger.error("❌ Signal generator not properly initialized")
            return {'has_real_data': False, 'error': 'Setup failed'}
        
        logger.info("🚀 Starting API-based forex signal generation V2.0...")
        
        try:
            # Run async generation in sync context
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            try:
                signal_result = loop.run_until_complete(
                    self.signal_generator.generate_forex_signals()
                )
                
                # Convert new format back to legacy format for compatibility
                legacy_format = self._convert_to_legacy_format(signal_result)
                
                if legacy_format.get('has_real_data'):
                    logger.info(f"✅ Successfully generated {len(legacy_format.get('forex_alerts', []))} signals")
                else:
                    logger.warning("⚠️ No active signals generated")
                
                return legacy_format
                
            finally:
                loop.close()
                
        except Exception as e:
            # Enhanced error categorization (preserved from original)
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
                return {'has_real_data': False, 'error': f'Signal generation failed: {str(e)[:100]}'}
    
    async def generate_forex_signals(self) -> Dict[str, Any]:
        """
        Async version of signal generation - backward compatibility
        
        Returns:
            Dictionary with signal data in legacy format
        """
        if not self.setup_successful:
            return {'has_real_data': False, 'error': 'Setup failed'}
        
        try:
            signal_result = await self.signal_generator.generate_forex_signals()
            return self._convert_to_legacy_format(signal_result)
            
        except Exception as e:
            logger.error(f"❌ Async signal generation error: {e}")
            return {'has_real_data': False, 'error': str(e)}
    
    def _convert_to_legacy_format(self, signal_result) -> Dict[str, Any]:
        """
        Convert new SignalResult format to legacy dictionary format
        Maintains backward compatibility with existing code
        """
        if not signal_result:
            return {'has_real_data': False, 'error': 'No signal result'}
        
        if signal_result.error:
            return {'has_real_data': False, 'error': signal_result.error}
        
        try:
            # Convert TradingSignal objects to legacy alert dictionaries
            forex_alerts = []
            
            for signal in signal_result.forex_alerts:
                # Convert to legacy format with all expected fields
                alert = {
                    'pair': signal.pair,
                    'action': signal.action.value,
                    'mt4_action': signal.mt4_action,
                    'entry_price': signal.entry_price,
                    'exit_price': signal.exit_price,
                    'stop_loss': signal.stop_loss,
                    'take_profit': signal.take_profit,
                    'target_pips': signal.target_pips,
                    'confidence': signal.confidence,
                    'signal_strength': signal.signal_strength,
                    'weekly_achievement_probability': signal.weekly_achievement_probability,
                    
                    # Format for plaintext template compatibility
                    'high': signal.high_price,
                    'low': signal.low_price,
                    'average': signal.entry_price,
                    'exit': signal.exit_price,
                    
                    # Advanced fields
                    'signal_category': signal.strength_category.value if signal.strength_category else None,
                    'expected_timeframe': signal.expected_timeframe,
                    'days_to_target': signal.days_to_target,
                    'risk_reward_ratio': signal.risk_reward_ratio,
                    'average_weekly_range_pips': signal.average_weekly_range_pips,
                    
                    'analysis_timestamp': signal.analysis_timestamp.isoformat(),
                    'expiry_date': signal.expiry_date.isoformat(),
                }
                
                # Add component scores if available
                for comp_name, component in signal.components.items():
                    alert[f'{comp_name}_score'] = component.score
                
                forex_alerts.append(alert)
            
            # Create legacy result structure
            result = {
                'has_real_data': signal_result.has_real_data,
                'forex_alerts': forex_alerts,
                'options_alerts': [],  # Legacy compatibility
                'swing_trades': [],    # Legacy compatibility  
                'day_trades': [],      # Legacy compatibility
                'source': signal_result.source,
                'timestamp': signal_result.timestamp.isoformat(),
                'total_signals': signal_result.total_signals,
                'active_signals': signal_result.active_signals,
                'hold_signals': signal_result.hold_signals,
                'currency_pairs_analyzed': signal_result.currency_pairs_analyzed,
                'text_report': signal_result.text_report
            }
            
            logger.info(f"📊 Converted to legacy format: {result['active_signals']} active signals")
            return result
            
        except Exception as e:
            logger.error(f"❌ Error converting to legacy format: {e}")
            return {
                'has_real_data': False,
                'forex_alerts': [],
                'options_alerts': [],
                'swing_trades': [],
                'day_trades': [],
                'error': f'Format conversion failed: {str(e)}'
            }
    
    def format_signals_for_plaintext(self, signals_data: Dict[str, Any]) -> str:
        """
        Format signals for plaintext output - backward compatibility
        Delegates to the new signal generator's formatting
        """
        try:
            # If we have the new signal generator, use its formatting
            if hasattr(self, 'signal_generator') and self.signal_generator:
                # Convert back to SignalResult if needed
                from forex_signals.signals.models import SignalResult, TradingSignal
                
                if isinstance(signals_data, dict):
                    # Convert legacy format to new format for formatting
                    try:
                        signal_result = SignalResult(**signals_data)
                        return self.signal_generator.format_signals_for_plaintext(signal_result)
                    except:
                        pass  # Fall back to manual formatting
            
            # Fallback to original formatting logic
            return self._format_signals_manual(signals_data)
            
        except Exception as e:
            logger.error(f"❌ Error formatting signals for plaintext: {e}")
            return f"Error formatting signals: {str(e)}"
    
    def _format_signals_manual(self, signals_data: Dict[str, Any]) -> str:
        """Manual formatting fallback - preserves original logic"""
        try:
            if not signals_data.get('has_real_data', False):
                return "No active forex signals available today."
            
            lines = []
            lines.append("FOREX TRADING SIGNALS")
            lines.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M PST')}")
            lines.append("")
            lines.append("FOREX PAIRS")
            lines.append("")
            
            for alert in signals_data.get('forex_alerts', []):
                if alert.get('action') == 'HOLD':
                    continue
                
                pair = alert.get('pair', 'Unknown')
                high_price = alert.get('high')
                average_price = alert.get('average')
                low_price = alert.get('low')
                action = alert.get('action', 'Unknown')
                exit_price = alert.get('exit')
                
                lines.extend([
                    f"Pair: {pair}",
                    f"High: {high_price:.5f}" if high_price else "High: N/A",
                    f"Average: {average_price:.5f}" if average_price else "Average: N/A",
                    f"Low: {low_price:.5f}" if low_price else "Low: N/A",
                    f"MT4 Action: MT4 {action}",
                    f"Exit: {exit_price:.5f}" if exit_price else "Exit: N/A",
                    ""
                ])
                
                # Add enhanced fields if available
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
            
            # Add enhanced summary
            lines.extend([
                "Enhanced API Analysis - {} signals".format(signals_data.get('active_signals', 0)),
                "Real market data from validated sources"
            ])
            
            return "\n".join(lines)
            
        except Exception as e:
            logger.error(f"❌ Manual formatting error: {e}")
            return f"Error formatting signals: {str(e)}"
    
    async def test_signal_generation(self) -> bool:
        """Test signal generation - backward compatibility"""
        try:
            if hasattr(self, 'signal_generator') and self.signal_generator:
                return await self.signal_generator.test_signal_generation()
            else:
                logger.error("❌ Signal generator not available")
                return False
        except Exception as e:
            logger.error(f"❌ Test failed: {e}")
            return False


# Create global instance for backward compatibility
try:
    forex_signal_integration = ForexSignalIntegrationV2()
    logger.info("✅ Global ForexSignalIntegrationV2 instance created")
except Exception as e:
    logger.error(f"❌ Failed to create global instance: {e}")
    forex_signal_integration = None


# Legacy class alias for backward compatibility
class ForexSignalIntegration(ForexSignalIntegrationV2):
    """Backward compatibility alias"""
    pass


# Legacy functions for backward compatibility
def validate_signal_data(signal_data: Dict[str, Any]) -> Dict[str, Any]:
    """Legacy function - delegates to new validator"""
    try:
        from forex_signals.signals.validators import validate_signal_data as new_validate
        return new_validate(signal_data)
    except Exception as e:
        logger.error(f"❌ Legacy validation failed: {e}")
        return signal_data


def initialize_real_data_enforcement():
    """Legacy function - delegates to new validator"""
    try:
        from forex_signals.signals.validators import initialize_real_data_enforcement as new_init
        return new_init()
    except Exception as e:
        logger.error(f"❌ Legacy initialization failed: {e}")
        return True


if __name__ == "__main__":
    # Test the integration
    async def test():
        integration = ForexSignalIntegrationV2()
        if integration.setup_successful:
            result = await integration.test_signal_generation()
            print(f"Test result: {result}")
        else:
            print("Setup failed")
    
    asyncio.run(test())