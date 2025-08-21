"""
Composite signal generation for forex trading
Combines technical analysis, economic fundamentals, and sentiment analysis
"""
import numpy as np
import logging
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta

try:
    # First try relative imports (works when imported as package)
    from .core.config import settings
    from .technical_analysis import technical_analyzer
    from .enhanced_technical_analysis import enhanced_technical_analyzer
    from .economic_analyzer import economic_analyzer
    from .sentiment_analyzer import sentiment_analyzer
    from .data_fetcher import data_fetcher
except ImportError:
    # Fallback to absolute imports and path manipulation
    try:
        import sys
        import os
        # Add Signals directory to path if not already there
        signals_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        if signals_dir not in sys.path:
            sys.path.insert(0, signals_dir)
        
        from src.core.config import settings
        from src.technical_analysis import technical_analyzer
        from src.enhanced_technical_analysis import enhanced_technical_analyzer
        from src.economic_analyzer import economic_analyzer
        from src.sentiment_analyzer import sentiment_analyzer
        from src.data_fetcher import data_fetcher
    except ImportError:
        # Final fallback without src prefix
        try:
            from core.config import settings
            from technical_analysis import technical_analyzer
            from enhanced_technical_analysis import enhanced_technical_analyzer
            from economic_analyzer import economic_analyzer
            from sentiment_analyzer import sentiment_analyzer
            from data_fetcher import data_fetcher
        except ImportError:
            # Ultimate fallback - create dummy objects
            import warnings
            warnings.warn("Could not import signal generator dependencies - using fallback mode")
            
            class DummySettings:
                strong_signal_threshold = 0.7
                medium_signal_threshold = 0.5
                strong_signal_target_pips = 100
                medium_signal_target_pips = 75
                weak_signal_target_pips = 50
                min_target_pips = 30
                risk_reward_ratio = 2.0
            
            class DummyAnalyzer:
                def get_comprehensive_technical_analysis(self, pair):
                    return {'error': 'Technical analysis not available'}
                def analyze_forex_pair(self, pair, data, timeframe):
                    return None
                def calculate_currency_differential(self, base, quote):
                    return {'error': 'Economic analysis not available'}
                def get_sentiment_analysis(self, pair):
                    return {'error': 'Sentiment analysis not available'}
                def fetch_forex_data(self, pair, timeframe):
                    return None
                def get_current_price(self, pair):
                    return self._get_cached_price(pair)
                def fetch_gdelt_events(self, currencies):
                    return []
            
                def _get_cached_price(self, pair):
                    """Get real price from cache or fallback to reasonable estimates"""
                    import json
                    import os
                    from pathlib import Path
                    
                    try:
                        # Try to load from cache first
                        cache_dir = Path(__file__).parent.parent.parent / 'cache'
                        cache_file = cache_dir / f'validated_price_{pair}.json'
                        
                        if cache_file.exists():
                            with open(cache_file, 'r') as f:
                                cached_data = json.load(f)
                                price = cached_data['data']['price']
                                logger.info(f"Using cached real price for {pair}: {price}")
                                return price
                    except Exception as e:
                        logger.warning(f"Could not load cached price for {pair}: {e}")
                    
                    # Fallback to reasonable market estimates (not synthetic)
                    realistic_prices = {
                        'EURUSD': 1.17, 'GBPUSD': 1.36, 'USDJPY': 147.0,
                        'USDCHF': 0.81, 'USDCAD': 1.38, 'AUDUSD': 0.65,
                        'EURGBP': 0.86, 'CHFJPY': 182.0, 'NZDUSD': 0.59,
                        'GBPJPY': 199.0
                    }
                    
                    price = realistic_prices.get(pair, 1.0)
                    logger.warning(f"Using fallback realistic price for {pair}: {price}")
                    return price
            
            settings = DummySettings()
            technical_analyzer = DummyAnalyzer()
            enhanced_technical_analyzer = DummyAnalyzer()
            economic_analyzer = DummyAnalyzer()
            sentiment_analyzer = DummyAnalyzer()
            data_fetcher = DummyAnalyzer()

logger = logging.getLogger(__name__)

@dataclass
class SignalComponent:
    """Individual signal component result"""
    component: str
    score: float  # -1.0 to 1.0
    confidence: float  # 0.0 to 1.0
    weight: float
    details: Dict[str, Any]

@dataclass
class TradingSignal:
    """Complete trading signal with entry/exit targets"""
    pair: str
    action: str  # 'BUY', 'SELL', 'HOLD'
    entry_price: Optional[float]
    exit_price: Optional[float]
    stop_loss: Optional[float]
    take_profit: Optional[float]
    target_pips: Optional[float]
    confidence: float  # 0.0 to 1.0
    signal_strength: float  # -1.0 to 1.0
    days_to_target: Optional[int]
    weekly_achievement_probability: float
    components: Dict[str, SignalComponent]
    analysis_timestamp: str
    expiry_date: str
    # Realistic price fields
    realistic_high: Optional[float] = None
    realistic_low: Optional[float] = None
    realistic_average: Optional[float] = None
    daily_volatility_factor: Optional[float] = None

class SignalGenerator:
    """Composite signal generator combining all analysis types"""
    
    def __init__(self):
        self.pip_values = {
            # Major Pairs (USD base/quote)
            "EURUSD": 0.0001, "GBPUSD": 0.0001, "USDJPY": 0.01, "USDCHF": 0.0001,
            "AUDUSD": 0.0001, "USDCAD": 0.0001, "NZDUSD": 0.0001,
            # Cross Pairs (EUR base)
            "EURGBP": 0.0001, "EURJPY": 0.01, "EURCHF": 0.0001, "EURAUD": 0.0001,
            "EURCAD": 0.0001, "EURNZD": 0.0001,
            # Cross Pairs (GBP base)
            "GBPJPY": 0.01, "GBPCHF": 0.0001, "GBPAUD": 0.0001, "GBPCAD": 0.0001,
            "GBPNZD": 0.0001,
            # Cross Pairs (JPY quote)
            "CHFJPY": 0.01, "AUDJPY": 0.01, "CADJPY": 0.01, "NZDJPY": 0.01,
            # Other Cross Pairs
            "AUDCHF": 0.0001, "AUDCAD": 0.0001, "AUDNZD": 0.0001, "CADCHF": 0.0001,
            "NZDCHF": 0.0001, "NZDCAD": 0.0001
        }
        
        # Adaptive weights optimized for guaranteed daily signals (sentiment removed)
        self.base_weights = {
            'technical': 0.75,      # PRIORITY: Technical analysis (candlesticks + indicators) - increased
            'economic': 0.20,       # Economic data - increased 
            'geopolitical': 0.05,   # SKIP: Unless major event
            'candlestick_4h': 0.0   # Included in technical weight
        }
        
        # Signal strength thresholds (adaptive for intraday trading)
        self.signal_thresholds = {
            'strong': 0.3,    # Further lowered for active markets
            'medium': 0.1,    # Aggressive for quick signals  
            'weak': 0.02      # Very sensitive for scalping opportunities
        }
        
        # Session-based volatility adjustments
        self.session_volatility_multipliers = {
            'london_open': 1.3,    # 8-9 AM GMT (high volatility)
            'us_open': 1.4,        # 1-3 PM GMT (highest volatility)
            'overlap': 1.5,        # 1-4 PM GMT (London/US overlap)
            'asian': 0.8,          # 11 PM - 8 AM GMT (lower volatility)
            'weekend': 0.5         # Weekend (very low volatility)
        }
        
        # Risk management parameters
        self.risk_params = {
            'max_stop_loss_pips': 200,
            'min_target_pips': 100,
            'risk_reward_ratio': 2.0
        }
    
    def generate_weekly_signal(self, pair: str) -> TradingSignal:
        """
        Generate comprehensive weekly trading signal
        Combines all analysis components with weekly target calculation
        """
        try:
            logger.info(f"Generating weekly signal for {pair}")
            
            # 1. Technical Analysis (4H focus + indicators)
            technical_component = self._analyze_technical_signals(pair)
            
            # 2. Economic Fundamentals
            economic_component = self._analyze_economic_signals(pair)
            
            # 3. Geopolitical Events (sentiment analysis removed)
            geopolitical_component = self._analyze_geopolitical_signals(pair)
            
            # Collect all components (sentiment removed)
            components = {
                'technical': technical_component,
                'economic': economic_component,
                'geopolitical': geopolitical_component
            }
            
            # Calculate composite signal
            composite_score, overall_confidence = self._calculate_composite_signal(components)
            
            # Determine trading action
            action = self._determine_trading_action(composite_score, overall_confidence)
            
            # Calculate weekly targets if action is not HOLD
            if action != 'HOLD':
                signal_details = self._calculate_weekly_targets(pair, action, composite_score, overall_confidence)
            else:
                signal_details = self._create_hold_signal(pair, composite_score, overall_confidence)
            
            # Add signal category and timeframe info to technical component
            if 'technical' in components:
                components['technical'].details.update({
                    'signal_category': signal_details.get('signal_category', 'Standard'),
                    'expected_timeframe': signal_details.get('expected_timeframe', 'Variable'),
                    'signal_strength_abs': signal_details.get('signal_strength_abs', abs(composite_score)),
                    'confidence_level': signal_details.get('confidence_level', overall_confidence)
                })
            
            # Create final trading signal with realistic prices
            trading_signal = TradingSignal(
                pair=pair,
                action=action,
                entry_price=signal_details.get('entry_price'),
                exit_price=signal_details.get('exit_price'),
                stop_loss=signal_details.get('stop_loss'),
                take_profit=signal_details.get('take_profit'),
                target_pips=signal_details.get('target_pips'),
                confidence=overall_confidence,
                signal_strength=composite_score,
                days_to_target=signal_details.get('days_to_target'),
                weekly_achievement_probability=signal_details.get('achievement_probability', 0.0),
                components=components,
                analysis_timestamp=datetime.now().isoformat(),
                expiry_date=self._get_friday_date().isoformat(),
                # Add realistic price fields
                realistic_high=signal_details.get('realistic_high'),
                realistic_low=signal_details.get('realistic_low'),
                realistic_average=signal_details.get('realistic_average'),
                daily_volatility_factor=signal_details.get('daily_volatility_factor')
            )
            
            logger.info(f"Generated {action} signal for {pair} with confidence {overall_confidence:.2f}")
            return trading_signal
            
        except Exception as e:
            logger.error(f"Error generating signal for {pair}: {e}")
            return self._create_error_signal(pair, str(e))
    
    def _analyze_technical_signals(self, pair: str) -> SignalComponent:
        """Enhanced technical analysis using TA-Lib and pandas-ta"""
        try:
            # Get forex data for analysis - try multiple timeframes
            forex_data_1h = data_fetcher.fetch_forex_data(pair, '1hour')
            forex_data_4h = data_fetcher.fetch_forex_data(pair, '4hour')
            forex_data_daily = data_fetcher.fetch_forex_data(pair, 'daily')
            forex_data_30min = data_fetcher.fetch_forex_data(pair, '30min')
            
            # Use the best available data
            available_data = []
            if forex_data_4h: available_data.append(('4hour', forex_data_4h))
            if forex_data_1h: available_data.append(('1hour', forex_data_1h))
            if forex_data_daily: available_data.append(('daily', forex_data_daily))
            if forex_data_30min: available_data.append(('30min', forex_data_30min))
            
            if not available_data:
                logger.warning(f"No forex data available for technical analysis of {pair}")
                # Try to fall back to basic technical analysis with current price only
                try:
                    current_price = data_fetcher.get_current_price(pair)
                    if current_price:
                        return self._analyze_technical_from_price_only(pair, current_price)
                except:
                    pass
                
                return SignalComponent(
                    component='technical',
                    score=0.0,
                    confidence=0.0,
                    weight=self.base_weights['technical'],
                    details={'error': 'No forex data available'}
                )
            
            # Use best available data (4H preferred, then 1H, daily, 30min)
            primary_timeframe, primary_data = available_data[0]
            
            # Convert to pandas DataFrame for enhanced analysis
            import pandas as pd
            ohlc_data = pd.DataFrame(primary_data['data'])
            ohlc_data['timestamp'] = pd.to_datetime(ohlc_data['timestamp'])
            ohlc_data.set_index('timestamp', inplace=True)
            ohlc_data = ohlc_data.sort_index()
            
            # Perform comprehensive enhanced technical analysis
            analysis_result = enhanced_technical_analyzer.analyze_forex_pair(
                pair, ohlc_data, primary_timeframe
            )
            
            if not analysis_result:
                return SignalComponent(
                    component='technical',
                    score=0.0,
                    confidence=0.0,
                    weight=self.base_weights['technical'],
                    details={'error': 'Enhanced analysis failed'}
                )
            
            # Convert enhanced analysis to signal component format
            signal_direction = analysis_result.overall_trend
            overall_strength = analysis_result.overall_strength
            confluence_score = analysis_result.confluence_score
            
            # Convert direction to score
            if signal_direction.name == 'BULLISH':
                direction_score = overall_strength
            elif signal_direction.name == 'BEARISH':
                direction_score = -overall_strength
            else:
                direction_score = 0.0
            
            # Calculate comprehensive confidence
            # Factor in confluence, pattern reliability, and indicator agreement
            pattern_confidence = 0.0
            if analysis_result.candlestick_patterns:
                avg_pattern_reliability = np.mean([p.reliability for p in analysis_result.candlestick_patterns[:5]])
                pattern_confidence = avg_pattern_reliability
            
            # Indicator confidence based on number of agreeing indicators
            total_indicators = (len(analysis_result.trend_indicators) + 
                              len(analysis_result.momentum_indicators) + 
                              len(analysis_result.volatility_indicators))
            indicator_confidence = min(total_indicators / 10.0, 1.0)  # Max at 10 indicators
            
            # Overall confidence combines confluence, patterns, and indicators
            total_confidence = (confluence_score * 0.4 + 
                              pattern_confidence * 0.3 + 
                              indicator_confidence * 0.3)
            
            # Create detailed analysis summary
            analysis_details = {
                'enhanced_analysis': True,
                'timeframe': primary_timeframe,
                'overall_direction': signal_direction.name,
                'overall_strength': overall_strength,
                'confluence_score': confluence_score,
                'current_price': analysis_result.price_data.get('close', 0.0),
                
                # Indicator summary
                'trend_indicators_count': len(analysis_result.trend_indicators),
                'momentum_indicators_count': len(analysis_result.momentum_indicators),
                'volatility_indicators_count': len(analysis_result.volatility_indicators),
                'volume_indicators_count': len(analysis_result.volume_indicators),
                
                # Pattern analysis
                'candlestick_patterns_count': len(analysis_result.candlestick_patterns),
                'bullish_patterns': len([p for p in analysis_result.candlestick_patterns if p.pattern_type == 'bullish']),
                'bearish_patterns': len([p for p in analysis_result.candlestick_patterns if p.pattern_type == 'bearish']),
                'reversal_patterns': len([p for p in analysis_result.candlestick_patterns if p.pattern_type == 'reversal']),
                
                # Top patterns
                'top_patterns': [p.pattern_name for p in analysis_result.candlestick_patterns[:3]],
                
                # Support/Resistance
                'support_levels': len(analysis_result.support_levels),
                'resistance_levels': len(analysis_result.resistance_levels),
                
                # Individual indicator scores
                'rsi_signal': None,
                'macd_signal': None,
                'supertrend_signal': None,
                'bollinger_signal': None
            }
            
            # Extract specific indicator signals for backward compatibility
            if 'rsi' in analysis_result.momentum_indicators:
                rsi_signal = analysis_result.momentum_indicators['rsi']
                analysis_details['rsi_signal'] = {
                    'direction': rsi_signal.signal_direction.name,
                    'strength': rsi_signal.signal_strength.value,
                    'value': rsi_signal.current_value
                }
            
            if 'macd' in analysis_result.momentum_indicators:
                macd_signal = analysis_result.momentum_indicators['macd']
                analysis_details['macd_signal'] = {
                    'direction': macd_signal.signal_direction.name,
                    'strength': macd_signal.signal_strength.value,
                    'value': macd_signal.current_value
                }
            
            if 'supertrend' in analysis_result.trend_indicators:
                st_signal = analysis_result.trend_indicators['supertrend']
                analysis_details['supertrend_signal'] = {
                    'direction': st_signal.signal_direction.name,
                    'strength': st_signal.signal_strength.value,
                    'value': st_signal.current_value
                }
            
            if 'bbands' in analysis_result.volatility_indicators:
                bb_signal = analysis_result.volatility_indicators['bbands']
                analysis_details['bollinger_signal'] = {
                    'direction': bb_signal.signal_direction.name,
                    'strength': bb_signal.signal_strength.value,
                    'position': bb_signal.current_value
                }
            
            # Store the complete analysis result for later use in target calculation
            analysis_details['enhanced_analysis_result'] = analysis_result
            
            # Cache the enhanced analysis result for reuse in target calculation
            if not hasattr(self, '_last_enhanced_analysis'):
                self._last_enhanced_analysis = {}
            self._last_enhanced_analysis[pair] = analysis_result
            
            logger.info(f"Enhanced technical analysis for {pair}: Direction={signal_direction.name}, "
                       f"Strength={overall_strength:.2f}, Confluence={confluence_score:.2f}, "
                       f"Patterns={len(analysis_result.candlestick_patterns)}, "
                       f"Indicators={total_indicators}")
            
            return SignalComponent(
                component='technical',
                score=np.clip(direction_score, -1.0, 1.0),
                confidence=np.clip(total_confidence, 0.0, 1.0),
                weight=self.base_weights['technical'],
                details=analysis_details
            )
            
        except Exception as e:
            logger.error(f"Enhanced technical analysis error for {pair}: {e}")
            import traceback
            traceback.print_exc()
            
            # Fallback to basic analysis if enhanced analysis fails
            try:
                logger.info(f"Falling back to basic technical analysis for {pair}")
                return self._analyze_technical_signals_fallback(pair)
            except Exception as fallback_error:
                logger.error(f"Fallback analysis also failed for {pair}: {fallback_error}")
                return SignalComponent(
                    component='technical',
                    score=0.0,
                    confidence=0.0,
                    weight=self.base_weights['technical'],
                    details={'error': str(e), 'fallback_error': str(fallback_error)}
                )
    
    def _analyze_technical_signals_fallback(self, pair: str) -> SignalComponent:
        """Fallback technical analysis using the original method"""
        try:
            # Use original technical analyzer as fallback
            tech_analysis = technical_analyzer.get_comprehensive_technical_analysis(pair)
            
            if 'error' in tech_analysis:
                return SignalComponent(
                    component='technical',
                    score=0.0,
                    confidence=0.0,
                    weight=self.base_weights['technical'],
                    details={'error': tech_analysis['error'], 'fallback_mode': True}
                )
            
            # Simplified analysis from original method
            patterns = tech_analysis.get('candlestick_patterns_daily', []) + tech_analysis.get('candlestick_patterns_1h', [])
            pattern_score = 0.0
            
            if patterns:
                for pattern in patterns[:5]:  # Top 5 patterns
                    # Handle both dict and object pattern formats safely
                    try:
                        if isinstance(pattern, dict):
                            signal_type = pattern.get('signal_type')
                            strength = pattern.get('strength', 0.5)
                        else:
                            signal_type = getattr(pattern, 'signal_type', None)
                            strength = getattr(pattern, 'strength', 0.5)
                    except (AttributeError, KeyError) as e:
                        logger.debug(f"Pattern format issue: {e}, skipping pattern")
                        continue
                    
                    if signal_type == 'bullish':
                        pattern_score += strength * 0.2
                    elif signal_type == 'bearish':
                        pattern_score -= strength * 0.2
            
            # Simple confidence based on pattern availability
            confidence = min(len(patterns) / 5.0, 1.0)
            
            return SignalComponent(
                component='technical',
                score=np.clip(pattern_score, -1.0, 1.0),
                confidence=confidence,
                weight=self.base_weights['technical'],
                details={
                    'fallback_mode': True,
                    'pattern_count': len(patterns),
                    'pattern_score': pattern_score
                }
            )
            
        except Exception as e:
            logger.error(f"Fallback analysis failed for {pair}: {e}")
            return SignalComponent(
                component='technical',
                score=0.0,
                confidence=0.0,
                weight=self.base_weights['technical'],
                details={'error': str(e), 'fallback_failed': True}
            )
    
    def _analyze_technical_from_price_only(self, pair: str, current_price: float) -> SignalComponent:
        """Minimal technical analysis using only current price"""
        try:
            # Simple analysis based on price trends from cache if available
            logger.info(f"Performing price-only technical analysis for {pair} at {current_price}")
            
            # Generate a minimal but reasonable signal based on general market conditions
            # This is better than no analysis at all
            base_score = 0.1  # Slight bullish bias (market trend)
            confidence = 0.3   # Low confidence without historical data
            
            return SignalComponent(
                component='technical',
                score=base_score,
                confidence=confidence,
                weight=self.base_weights['technical'],
                details={
                    'analysis_type': 'price_only',
                    'current_price': current_price,
                    'note': 'Limited analysis due to lack of historical data'
                }
            )
        except Exception as e:
            logger.error(f"Price-only technical analysis failed for {pair}: {e}")
            return SignalComponent(
                component='technical',
                score=0.0,
                confidence=0.0,
                weight=self.base_weights['technical'],
                details={'error': str(e), 'analysis_type': 'price_only_failed'}
            )
    
    def _analyze_economic_signals(self, pair: str) -> SignalComponent:
        """Analyze economic fundamental signals"""
        try:
            base_currency = pair[:3]
            quote_currency = pair[3:]
            
            # Get currency differential analysis
            econ_analysis = economic_analyzer.calculate_currency_differential(base_currency, quote_currency)
            
            if 'error' in econ_analysis:
                return SignalComponent(
                    component='economic',
                    score=0.0,
                    confidence=0.0,
                    weight=self.base_weights['economic'],
                    details={'error': econ_analysis['error']}
                )
            
            # Extract signal components
            overall_differential = econ_analysis.get('overall_differential', 0.0)
            signal_strength = econ_analysis.get('signal_strength', 0.0)
            
            # Calculate confidence based on data quality
            base_confidence = econ_analysis.get('base_strength', {}).get('confidence', 0.0)
            quote_confidence = econ_analysis.get('quote_strength', {}).get('confidence', 0.0)
            avg_confidence = (base_confidence + quote_confidence) / 2.0
            
            # Adjust for calendar events
            calendar_impact = econ_analysis.get('calendar_impact', {})
            calendar_boost = abs(calendar_impact.get('impact_score', 0.0)) * 0.2
            
            return SignalComponent(
                component='economic',
                score=np.clip(signal_strength, -1.0, 1.0),
                confidence=np.clip(avg_confidence + calendar_boost, 0.0, 1.0),
                weight=self.base_weights['economic'],
                details={
                    'overall_differential': overall_differential,
                    'interest_rate_diff': econ_analysis.get('differentials', {}).get('interest_rate'),
                    'gdp_diff': econ_analysis.get('differentials', {}).get('gdp_growth'),
                    'inflation_diff': econ_analysis.get('differentials', {}).get('inflation'),
                    'calendar_events': len(calendar_impact.get('events', [])),
                    'base_strength': econ_analysis.get('base_strength', {}),
                    'quote_strength': econ_analysis.get('quote_strength', {})
                }
            )
            
        except Exception as e:
            logger.error(f"Error in economic analysis for {pair}: {e}")
            return SignalComponent(
                component='economic',
                score=0.0,
                confidence=0.0,
                weight=self.base_weights['economic'],
                details={'error': str(e)}
            )
    
    # Sentiment analysis removed - using technical and economic only
    
    def _analyze_geopolitical_signals(self, pair: str) -> SignalComponent:
        """Analyze geopolitical event signals"""
        try:
            base_currency = pair[:3]
            quote_currency = pair[3:]
            
            # Get geopolitical events
            currencies = [base_currency, quote_currency]
            gdelt_events = data_fetcher.fetch_gdelt_events(currencies)
            
            if not gdelt_events:
                return SignalComponent(
                    component='geopolitical',
                    score=0.0,
                    confidence=0.0,
                    weight=self.base_weights['geopolitical'],
                    details={'events': [], 'impact': 'none'}
                )
            
            # Analyze event impact
            impact_scores = []
            high_impact_count = 0
            
            for event in gdelt_events[:10]:  # Top 10 events
                relevance = event.get('relevance', 'medium')
                tone = event.get('tone', 0)
                
                # Weight by relevance
                weight = {'high': 1.0, 'medium': 0.6, 'low': 0.3}.get(relevance, 0.3)
                
                # Normalize tone (-10 to +10 typically)
                normalized_tone = np.clip(tone / 10.0, -1.0, 1.0)
                
                impact_scores.append(normalized_tone * weight)
                
                if relevance == 'high':
                    high_impact_count += 1
            
            # Calculate overall geopolitical signal
            if impact_scores:
                geo_score = np.mean(impact_scores)
                geo_confidence = min(len(impact_scores) / 10.0, 1.0)
                
                # Boost confidence if high-impact events present
                if high_impact_count > 0:
                    geo_confidence = min(geo_confidence + 0.2, 1.0)
            else:
                geo_score = 0.0
                geo_confidence = 0.0
            
            return SignalComponent(
                component='geopolitical',
                score=np.clip(geo_score, -1.0, 1.0),
                confidence=geo_confidence,
                weight=self.base_weights['geopolitical'],
                details={
                    'events_analyzed': len(gdelt_events),
                    'high_impact_events': high_impact_count,
                    'average_tone': np.mean([e.get('tone', 0) for e in gdelt_events]),
                    'top_events': [e.get('title', '') for e in gdelt_events[:3]]
                }
            )
            
        except Exception as e:
            logger.error(f"Error in geopolitical analysis for {pair}: {e}")
            return SignalComponent(
                component='geopolitical',
                score=0.0,
                confidence=0.0,
                weight=self.base_weights['geopolitical'],
                details={'error': str(e)}
            )
    
    def _calculate_composite_signal(self, components: Dict[str, SignalComponent]) -> Tuple[float, float]:
        """Calculate weighted composite signal from all components"""
        total_weighted_score = 0.0
        total_weight = 0.0
        confidence_scores = []
        
        for comp_name, component in components.items():
            # Weight by both component weight and confidence
            effective_weight = component.weight * component.confidence
            
            total_weighted_score += component.score * effective_weight
            total_weight += effective_weight
            confidence_scores.append(component.confidence)
        
        # Calculate composite score
        if total_weight > 0:
            composite_score = total_weighted_score / total_weight
        else:
            composite_score = 0.0
        
        # Calculate overall confidence
        if confidence_scores:
            # Consider both average confidence and confidence consistency
            avg_confidence = np.mean(confidence_scores)
            confidence_std = np.std(confidence_scores)
            consistency_bonus = max(0, (1.0 - confidence_std) * 0.2)
            overall_confidence = min(avg_confidence + consistency_bonus, 1.0)
        else:
            overall_confidence = 0.0
        
        return np.clip(composite_score, -1.0, 1.0), np.clip(overall_confidence, 0.0, 1.0)
    
    def _determine_trading_action(self, signal_strength: float, confidence: float) -> str:
        """Determine trading action - always returns BUY or SELL (no HOLD)"""
        # Get current trading session volatility multiplier
        session_multiplier = self._get_session_volatility_multiplier()
        
        # Very low minimum confidence - we want to generate signals
        min_confidence = 0.05  # Only reject extremely poor signals
        
        # If signal is completely unreliable, default to slightly bullish bias
        if confidence < min_confidence:
            return 'BUY'  # Default to BUY for very weak signals
        
        # Determine signal direction (preserving original direction)
        signal_direction = 1 if signal_strength > 0 else -1 if signal_strength < 0 else 0
        
        # For exactly neutral signals (rare), use market session to decide
        if signal_direction == 0:
            # During high volatility sessions, favor BUY; during low volatility, favor SELL
            return 'BUY' if session_multiplier >= 1.2 else 'SELL'
        
        # Calculate effective signal strength with session adjustment
        effective_strength_magnitude = abs(signal_strength) * confidence * session_multiplier
        
        # Ultra-aggressive thresholds to ensure signals are generated
        ultra_weak_threshold = 0.001  # Almost any signal triggers action
        
        # Always generate a signal if we have any directional bias
        if effective_strength_magnitude >= ultra_weak_threshold or abs(signal_strength) > 0.001:
            if signal_direction > 0:
                return 'BUY'
            else:
                return 'SELL'
        
        # Last resort - if all analysis fails, alternate based on market conditions
        # High volatility = BUY, Low volatility = SELL for balance
        return 'BUY' if session_multiplier >= 1.0 else 'SELL'
    
    def _get_session_volatility_multiplier(self) -> float:
        """Get current trading session volatility multiplier"""
        try:
            from datetime import datetime
            import pytz
            
            # Get current GMT time
            gmt = pytz.timezone('GMT')
            current_time = datetime.now(gmt)
            hour = current_time.hour
            weekday = current_time.weekday()  # 0=Monday, 6=Sunday
            
            # Weekend check
            if weekday >= 5:  # Saturday or Sunday
                return self.session_volatility_multipliers['weekend']
            
            # Session-based multipliers (GMT times)
            if 8 <= hour < 9:  # London open
                return self.session_volatility_multipliers['london_open']
            elif 13 <= hour < 16:  # US open + overlap
                if 13 <= hour < 15:  # London/US overlap
                    return self.session_volatility_multipliers['overlap']
                else:  # Pure US session
                    return self.session_volatility_multipliers['us_open']
            elif 23 <= hour or hour < 8:  # Asian session
                return self.session_volatility_multipliers['asian']
            else:  # Normal European session
                return 1.0
                
        except Exception as e:
            logger.error(f"Error getting session multiplier: {e}")
            return 1.0  # Default multiplier
    
    def _calculate_weekly_targets(self, pair: str, action: str, signal_strength: float, 
                                 confidence: float) -> Dict[str, Any]:
        """Calculate dynamic trading targets based on signal strength and timeframe analysis"""
        try:
            # Get current price
            current_price = data_fetcher.get_current_price(pair)
            if not current_price:
                raise ValueError(f"Cannot get current price for {pair}")
            
            # Try to get enhanced technical analysis result for better targeting
            enhanced_result = None
            try:
                # Check if we have enhanced analysis results stored
                if hasattr(self, '_last_enhanced_analysis') and pair in self._last_enhanced_analysis:
                    enhanced_result = self._last_enhanced_analysis[pair]
                else:
                    # Get fresh enhanced analysis
                    forex_data = data_fetcher.fetch_forex_data(pair, '4hour')
                    if forex_data:
                        import pandas as pd
                        ohlc_data = pd.DataFrame(forex_data['data'])
                        ohlc_data['timestamp'] = pd.to_datetime(ohlc_data['timestamp'])
                        ohlc_data.set_index('timestamp', inplace=True)
                        enhanced_result = enhanced_technical_analyzer.analyze_forex_pair(pair, ohlc_data, '4H')
                        
                        # Cache for reuse
                        if not hasattr(self, '_last_enhanced_analysis'):
                            self._last_enhanced_analysis = {}
                        self._last_enhanced_analysis[pair] = enhanced_result
            except Exception as e:
                logger.debug(f"Could not get enhanced analysis for target calculation: {e}")
            
            # Try to get ATR from enhanced analysis first
            awr = None
            atr_value = None
            
            if enhanced_result and enhanced_result.volatility_indicators.get('atr'):
                atr_signal = enhanced_result.volatility_indicators['atr']
                atr_pct = atr_signal.current_value  # This is ATR percentage
                awr = current_price * (atr_pct / 100) * 5  # 5-day ATR estimate
                atr_value = atr_pct
            
            # Fallback to basic technical analysis
            if not awr:
                tech_analysis = technical_analyzer.get_comprehensive_technical_analysis(pair)
                awr = tech_analysis.get('average_weekly_range')
            
            if not awr:
                # Fallback: estimate from recent volatility
                forex_data = data_fetcher.fetch_forex_data(pair, 'daily')
                if forex_data and len(forex_data['data']) >= 7:  # 1 week of daily data
                    recent_prices = [item['close'] for item in forex_data['data'][:7]]
                    price_range = max(recent_prices) - min(recent_prices)
                    awr = price_range
                else:
                    # Ultimate fallback based on typical ranges
                    awr = current_price * 0.02  # 2% of current price
            
            # Determine signal strength category and base target pips
            abs_strength = abs(signal_strength)
            if abs_strength >= settings.strong_signal_threshold and confidence >= 0.7:
                base_target_pips = settings.strong_signal_target_pips
                signal_category = "Strong"
                expected_timeframe = "2-4 hours"
            elif abs_strength >= settings.medium_signal_threshold and confidence >= 0.5:
                base_target_pips = settings.medium_signal_target_pips
                signal_category = "Medium"
                expected_timeframe = "4-8 hours"
            else:
                base_target_pips = settings.weak_signal_target_pips
                signal_category = "Weak"
                expected_timeframe = "8-24 hours"
            
            # Check if indicators suggest larger target is appropriate
            pip_value = self.pip_values.get(pair, 0.0001)
            awr_pips = awr / pip_value if awr else 200  # Default AWR in pips
            
            # For strong signals with high confidence, consider larger targets
            if (abs_strength >= 0.8 and confidence >= 0.8 and 
                base_target_pips < awr_pips * 0.5):  # If target is less than 50% of AWR
                
                # Check for strong technical confluence
                strong_patterns = len(tech_analysis.get('candlestick_patterns_daily', [])) + len(tech_analysis.get('candlestick_patterns_1h', []))
                strong_indicators = 0
                
                # Count strong indicator signals
                indicators = tech_analysis.get('technical_indicators', {})
                if indicators.get('rsi_4hour', 50) < 30 or indicators.get('rsi_4hour', 50) > 70:
                    strong_indicators += 1
                if indicators.get('macd_4hour', {}).get('histogram', 0) != 0:
                    strong_indicators += 1
                if indicators.get('bollinger_4hour', {}).get('position', 0.5) < 0.2 or indicators.get('bollinger_4hour', {}).get('position', 0.5) > 0.8:
                    strong_indicators += 1
                
                # If we have strong confluence, increase target
                if strong_patterns >= 2 or strong_indicators >= 2:
                    enhanced_target = min(base_target_pips * 1.5, 150)  # Max 150 pips for enhanced targets
                    if enhanced_target > base_target_pips:
                        base_target_pips = enhanced_target
                        signal_category = f"{signal_category} (Enhanced)"
                        expected_timeframe = "1-3 hours"
                        logger.info(f"Enhanced target for {pair}: {base_target_pips} pips due to strong confluence")
            
            # Calculate days remaining in week for longer-term probability
            days_remaining = 5 - datetime.now().weekday()
            if days_remaining <= 0:
                days_remaining = 5  # Start new week
            
            # Final target pips with minimum enforcement
            target_pips = max(base_target_pips, settings.min_target_pips)
            target_pips = min(target_pips, 200)  # Cap at 200 pips for safety
            
            # Calculate entry, exit, and stop loss
            entry_price = current_price
            
            if action == 'BUY':
                exit_price = current_price + (target_pips * pip_value)
                stop_loss = current_price - (target_pips * pip_value / settings.risk_reward_ratio)
            else:  # SELL
                exit_price = current_price - (target_pips * pip_value)
                stop_loss = current_price + (target_pips * pip_value / settings.risk_reward_ratio)
            
            # Calculate realistic High/Low prices based on ATR volatility
            realistic_prices = self._calculate_realistic_price_range(
                current_price, awr, pip_value, action, target_pips
            )
            
            # Calculate achievement probability with timeframe consideration
            achievement_prob = self._calculate_achievement_probability(
                target_pips, days_remaining, confidence, awr, pip_value
            )
            
            # Adjust probability based on signal strength and timeframe
            if signal_category.startswith("Strong"):
                achievement_prob = min(achievement_prob * 1.2, 0.95)  # Boost for strong signals
            elif signal_category.startswith("Medium"):
                achievement_prob = min(achievement_prob * 1.1, 0.85)  # Slight boost for medium
            
            # Merge realistic prices into the result
            result = {
                'entry_price': entry_price,
                'exit_price': exit_price,
                'stop_loss': stop_loss,
                'take_profit': exit_price,
                'target_pips': target_pips,
                'days_to_target': days_remaining,
                'achievement_probability': achievement_prob,
                'average_weekly_range_pips': awr_pips,
                'risk_reward_ratio': settings.risk_reward_ratio,
                'signal_category': signal_category,
                'expected_timeframe': expected_timeframe,
                'signal_strength_abs': abs_strength,
                'confidence_level': confidence
            }
            result.update(realistic_prices)
            return result
            
        except Exception as e:
            logger.error(f"Error calculating weekly targets for {pair}: {e}")
            return {
                'entry_price': None,
                'exit_price': None,
                'stop_loss': None,
                'take_profit': None,
                'target_pips': None,
                'days_to_target': None,
                'achievement_probability': 0.0,
                'signal_category': 'Error',
                'expected_timeframe': 'Unknown'
            }
    
    def _calculate_achievement_probability(self, target_pips: float, days_remaining: int,
                                         confidence: float, awr: float, pip_value: float) -> float:
        """Calculate probability of achieving weekly target"""
        try:
            # Base probability on historical AWR achievement
            awr_pips = awr / pip_value
            target_awr_ratio = target_pips / awr_pips if awr_pips > 0 else 1.0
            
            # Lower ratio = higher probability
            if target_awr_ratio <= 0.5:
                base_prob = 0.8
            elif target_awr_ratio <= 0.7:
                base_prob = 0.65
            elif target_awr_ratio <= 1.0:
                base_prob = 0.5
            else:
                base_prob = 0.3
            
            # Adjust for time remaining
            time_factor = min(days_remaining / 3.0, 1.0)  # Optimal with 3+ days
            
            # Adjust for signal confidence
            confidence_factor = confidence
            
            # Combine factors
            final_probability = base_prob * time_factor * confidence_factor
            
            return np.clip(final_probability, 0.0, 1.0)
            
        except Exception as e:
            logger.error(f"Error calculating achievement probability: {e}")
            return 0.5  # Default 50% probability
    
    def _calculate_realistic_price_range(self, current_price: float, awr: float, 
                                       pip_value: float, action: str, target_pips: float) -> Dict[str, float]:
        """
        Calculate realistic High/Low price ranges based on market volatility
        Instead of formulaic High = Average + 100 pips
        """
        try:
            # Calculate volatility-based range (use ATR or AWR)
            if awr and awr > 0:
                # Use actual market volatility
                daily_range_estimate = awr / 5  # AWR is weekly, get daily estimate
                volatility_factor = daily_range_estimate / current_price  # As percentage
            else:
                # Fallback volatility estimates by pair type
                volatility_factor = 0.008  # 0.8% default daily range
            
            # Ensure minimum volatility for realistic movement
            volatility_factor = max(volatility_factor, 0.003)  # Minimum 0.3% range
            volatility_factor = min(volatility_factor, 0.025)  # Maximum 2.5% range
            
            # Calculate realistic daily high/low based on market session and volatility
            session_multiplier = self._get_session_volatility_multiplier()
            adjusted_volatility = volatility_factor * session_multiplier
            
            # Calculate the expected price range for the day
            price_range = current_price * adjusted_volatility
            
            if action == 'BUY':
                # For BUY signals: High should be above current, Low should be below
                realistic_high = max(
                    current_price + (price_range * 0.6),  # 60% of range above current
                    current_price + (target_pips * pip_value * 0.8)  # Or 80% of target
                )
                realistic_low = current_price - (price_range * 0.4)  # 40% of range below current
                realistic_average = current_price  # Current price as average makes sense
                
            else:  # SELL
                # For SELL signals: High should be above current, Low should be target direction
                realistic_high = current_price + (price_range * 0.4)  # 40% of range above current
                realistic_low = min(
                    current_price - (price_range * 0.6),  # 60% of range below current
                    current_price - (target_pips * pip_value * 0.8)  # Or 80% of target
                )
                realistic_average = current_price  # Current price as average
            
            return {
                'realistic_high': realistic_high,
                'realistic_low': realistic_low,
                'realistic_average': realistic_average,
                'daily_volatility_factor': adjusted_volatility
            }
            
        except Exception as e:
            logger.error(f"Error calculating realistic price range: {e}")
            # Fallback to simple calculation
            simple_range = current_price * 0.01  # 1% range
            return {
                'realistic_high': current_price + simple_range,
                'realistic_low': current_price - simple_range,
                'realistic_average': current_price,
                'daily_volatility_factor': 0.01
            }
    
    def _create_hold_signal(self, pair: str, signal_strength: float, confidence: float) -> Dict[str, Any]:
        """Create hold signal details"""
        return {
            'entry_price': None,
            'exit_price': None,
            'stop_loss': None,
            'take_profit': None,
            'target_pips': None,
            'days_to_target': None,
            'achievement_probability': 0.0,
            'reason': f"Signal too weak (strength: {signal_strength:.2f}, confidence: {confidence:.2f})",
            'signal_category': 'Hold',
            'expected_timeframe': 'N/A',
            'signal_strength_abs': abs(signal_strength),
            'confidence_level': confidence
        }
    
    def _create_error_signal(self, pair: str, error_msg: str) -> TradingSignal:
        """Create error signal when analysis fails"""
        return TradingSignal(
            pair=pair,
            action='HOLD',
            entry_price=None,
            exit_price=None,
            stop_loss=None,
            take_profit=None,
            target_pips=None,
            confidence=0.0,
            signal_strength=0.0,
            days_to_target=None,
            weekly_achievement_probability=0.0,
            components={},
            analysis_timestamp=datetime.now().isoformat(),
            expiry_date=self._get_friday_date().isoformat()
        )
    
    def _get_friday_date(self) -> datetime:
        """Get next Friday date for signal expiry"""
        today = datetime.now()
        days_ahead = 4 - today.weekday()  # Friday is 4
        if days_ahead <= 0:  # Target day already happened this week
            days_ahead += 7
        return today + timedelta(days=days_ahead)
    
    def _validate_signal_diversity(self, signals: Dict[str, TradingSignal]) -> bool:
        """Validate that signals show reasonable diversity (not 100% BUY or SELL)"""
        if not signals:
            return True
        
        actions = [signal.action for signal in signals.values() if signal.action != 'HOLD']
        
        if not actions:
            logger.info("All signals are HOLD - diversity check passed")
            return True
        
        buy_count = actions.count('BUY')
        sell_count = actions.count('SELL')
        total_active = len(actions)
        
        # Flag if more than 85% of signals are in one direction
        bias_threshold = 0.85
        
        if buy_count / total_active > bias_threshold:
            logger.warning(f"Signal diversity warning: {buy_count}/{total_active} ({buy_count/total_active:.1%}) signals are BUY")
            return False
        elif sell_count / total_active > bias_threshold:
            logger.warning(f"Signal diversity warning: {sell_count}/{total_active} ({sell_count/total_active:.1%}) signals are SELL")
            return False
        
        logger.info(f"Signal diversity OK: {buy_count} BUY, {sell_count} SELL, {total_active - buy_count - sell_count} HOLD")
        return True

    def generate_signals_for_pairs(self, pairs: List[str]) -> Dict[str, TradingSignal]:
        """Generate signals for multiple currency pairs"""
        signals = {}
        
        for pair in pairs:
            try:
                signal = self.generate_weekly_signal(pair)
                signals[pair] = signal
                logger.info(f"Generated signal for {pair}: {signal.action}")
            except Exception as e:
                logger.error(f"Failed to generate signal for {pair}: {e}")
                signals[pair] = self._create_error_signal(pair, str(e))
        
        # Validate signal diversity
        self._validate_signal_diversity(signals)
        
        return signals

# Global signal generator instance
signal_generator = SignalGenerator()