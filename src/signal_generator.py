"""
Composite signal generation for forex trading
Combines technical analysis, economic fundamentals, and sentiment analysis
"""
import numpy as np
import logging
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta

from src.core.config import settings
from .technical_analysis import technical_analyzer
from .economic_analyzer import economic_analyzer
from .sentiment_analyzer import sentiment_analyzer
from .data_fetcher import data_fetcher

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
        
        # Adaptive weights optimized for intraday signals (2-3 per day)
        self.base_weights = {
            'technical': 0.45,      # Increased from 0.35 for more reactive signals
            'economic': 0.15,       # Decreased from 0.25 (less important for intraday)
            'sentiment': 0.25,      # Increased from 0.20 for market mood
            'geopolitical': 0.05,   # Decreased from 0.10 (minimal intraday impact)
            'candlestick_4h': 0.10  # Maintained for trend direction
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
            
            # 3. Market Sentiment
            sentiment_component = self._analyze_sentiment_signals(pair)
            
            # 4. Geopolitical Events
            geopolitical_component = self._analyze_geopolitical_signals(pair)
            
            # Collect all components
            components = {
                'technical': technical_component,
                'economic': economic_component,
                'sentiment': sentiment_component,
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
            
            # Create final trading signal
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
                expiry_date=self._get_friday_date().isoformat()
            )
            
            logger.info(f"Generated {action} signal for {pair} with confidence {overall_confidence:.2f}")
            return trading_signal
            
        except Exception as e:
            logger.error(f"Error generating signal for {pair}: {e}")
            return self._create_error_signal(pair, str(e))
    
    def _analyze_technical_signals(self, pair: str) -> SignalComponent:
        """Analyze multi-timeframe technical signals for increased signal frequency"""
        try:
            # Get comprehensive technical analysis with multi-timeframe support
            tech_analysis = technical_analyzer.get_comprehensive_technical_analysis(pair)
            
            if 'error' in tech_analysis:
                return SignalComponent(
                    component='technical',
                    score=0.0,
                    confidence=0.0,
                    weight=self.base_weights['technical'],
                    details={'error': tech_analysis['error']}
                )
            
            # Multi-timeframe candlestick pattern analysis
            pattern_scores = []
            total_pattern_confidence = 0.0
            pattern_details = {}
            
            # 4H patterns (highest weight - 60%)
            patterns_4h = tech_analysis.get('candlestick_patterns_4h', [])
            if patterns_4h:
                for i, pattern in enumerate(patterns_4h[:3]):  # Top 3 patterns
                    weight = (1.0 / (i + 1)) * 0.6  # 60% weight for 4H
                    if pattern['signal_type'] == 'bullish':
                        pattern_scores.append(pattern['strength'] * weight)
                    elif pattern['signal_type'] == 'bearish':
                        pattern_scores.append(-pattern['strength'] * weight)
                total_pattern_confidence += len(patterns_4h[:3]) * 0.6
                pattern_details['4h_patterns'] = len(patterns_4h)
            
            # 1H patterns (medium weight - 30%)
            patterns_1h = tech_analysis.get('candlestick_patterns_1h', [])
            if patterns_1h:
                for i, pattern in enumerate(patterns_1h[:3]):
                    weight = (1.0 / (i + 1)) * 0.3  # 30% weight for 1H
                    if pattern['signal_type'] == 'bullish':
                        pattern_scores.append(pattern['strength'] * weight)
                    elif pattern['signal_type'] == 'bearish':
                        pattern_scores.append(-pattern['strength'] * weight)
                total_pattern_confidence += len(patterns_1h[:3]) * 0.3
                pattern_details['1h_patterns'] = len(patterns_1h)
            
            # 30M patterns (lower weight - 10% for quick signals)
            patterns_30m = tech_analysis.get('candlestick_patterns_30m', [])
            if patterns_30m:
                for i, pattern in enumerate(patterns_30m[:2]):
                    weight = (1.0 / (i + 1)) * 0.1  # 10% weight for 30M
                    if pattern['signal_type'] == 'bullish':
                        pattern_scores.append(pattern['strength'] * weight)
                    elif pattern['signal_type'] == 'bearish':
                        pattern_scores.append(-pattern['strength'] * weight)
                total_pattern_confidence += len(patterns_30m[:2]) * 0.1
                pattern_details['30m_patterns'] = len(patterns_30m)
            
            # Calculate combined pattern score
            candlestick_score = np.mean(pattern_scores) if pattern_scores else 0.0
            candlestick_confidence = min(total_pattern_confidence / 3.0, 1.0)
            
            # Multi-timeframe indicator signals from technical analysis
            multi_tf_signals = tech_analysis.get('multi_timeframe_signals', {})
            indicator_scores = []
            indicator_details = {}
            
            # Process signals from all available timeframes
            timeframe_weights = {'30min': 0.15, '1hour': 0.25, '4hour': 0.45, 'daily': 0.15}
            
            for timeframe, signals in multi_tf_signals.items():
                tf_weight = timeframe_weights.get(timeframe, 0.1)
                tf_score = 0.0
                signal_count = 0
                
                # RSI signals
                if 'rsi' in signals:
                    rsi_signal = signals['rsi']
                    if rsi_signal['signal'] == 'bullish':
                        tf_score += rsi_signal['strength'] * 0.8  # Strong RSI weight
                    elif rsi_signal['signal'] == 'bearish':
                        tf_score -= rsi_signal['strength'] * 0.8
                    signal_count += 1
                
                # MACD signals
                if 'macd' in signals:
                    macd_signal = signals['macd']
                    if macd_signal['signal'] == 'bullish':
                        tf_score += macd_signal['strength'] * 0.6
                    elif macd_signal['signal'] == 'bearish':
                        tf_score -= macd_signal['strength'] * 0.6
                    signal_count += 1
                
                # Bollinger Band signals
                if 'bollinger' in signals:
                    bb_signal = signals['bollinger']
                    if bb_signal['signal'] == 'bullish':
                        tf_score += bb_signal['strength'] * 0.5
                    elif bb_signal['signal'] == 'bearish':
                        tf_score -= bb_signal['strength'] * 0.5
                    signal_count += 1
                
                # Stochastic signals
                if 'stochastic' in signals:
                    stoch_signal = signals['stochastic']
                    if stoch_signal['signal'] == 'bullish':
                        tf_score += stoch_signal['strength'] * 0.4
                    elif stoch_signal['signal'] == 'bearish':
                        tf_score -= stoch_signal['strength'] * 0.4
                    signal_count += 1
                
                # EMA trend signals
                if 'ema_trend' in signals:
                    ema_signal = signals['ema_trend']
                    if ema_signal['signal'] == 'bullish':
                        tf_score += ema_signal['strength'] * 0.3
                    elif ema_signal['signal'] == 'bearish':
                        tf_score -= ema_signal['strength'] * 0.3
                    signal_count += 1
                
                # Weight by timeframe and add to total
                if signal_count > 0:
                    weighted_tf_score = (tf_score / signal_count) * tf_weight
                    indicator_scores.append(weighted_tf_score)
                    indicator_details[f'{timeframe}_signals'] = signal_count
                    indicator_details[f'{timeframe}_score'] = tf_score / signal_count if signal_count > 0 else 0.0
            
            # Calculate combined indicator score
            indicator_score = sum(indicator_scores) if indicator_scores else 0.0
            
            # Incorporate short-term signals for intraday trading
            short_term_signals = tech_analysis.get('short_term_signals', {})
            short_term_score = 0.0
            short_term_confidence = 0.0
            
            if short_term_signals and short_term_signals.get('overall_signal') != 'neutral':
                signal_direction = short_term_signals['overall_signal']
                signal_confidence = short_term_signals.get('confidence', 0.0)
                
                # Strong boost for intraday signals
                if signal_direction == 'bullish':
                    short_term_score = 0.4 * signal_confidence  # Up to 40% boost
                elif signal_direction == 'bearish':
                    short_term_score = -0.4 * signal_confidence
                
                short_term_confidence = signal_confidence
            
            # Enhanced weighted combination with short-term signals
            # Patterns: 50%, Indicators: 30%, Short-term: 20%
            total_score = (candlestick_score * 0.5 + 
                          indicator_score * 0.3 + 
                          short_term_score * 0.2)
            
            # Calculate confidence based on signal availability across timeframes
            timeframe_confidence = len(multi_tf_signals) / 4.0  # Up to 4 timeframes
            indicator_confidence = len(indicator_scores) / 4.0  # Multiple indicators
            total_confidence = (candlestick_confidence * 0.4 + 
                              timeframe_confidence * 0.3 + 
                              indicator_confidence * 0.2 +
                              short_term_confidence * 0.1)
            
            # Merge all details for comprehensive reporting
            all_details = {
                'candlestick_score': candlestick_score,
                'candlestick_confidence': candlestick_confidence,
                'indicator_score': indicator_score,
                'short_term_score': short_term_score,
                'short_term_confidence': short_term_confidence,
                'total_pattern_signals': len(pattern_scores),
                'total_indicator_signals': len(indicator_scores),
                'short_term_pattern_count': len(short_term_signals.get('momentum_shifts', []) +
                                               short_term_signals.get('volatility_breakouts', []) +
                                               short_term_signals.get('trend_continuations', []) +
                                               short_term_signals.get('reversal_patterns', [])),
                'available_timeframes': tech_analysis.get('available_timeframes', []),
                'average_weekly_range': tech_analysis.get('average_weekly_range'),
                **pattern_details,
                **indicator_details
            }
            
            return SignalComponent(
                component='technical',
                score=np.clip(total_score, -1.0, 1.0),
                confidence=np.clip(total_confidence, 0.0, 1.0),
                weight=self.base_weights['technical'],
                details=all_details
            )
            
        except Exception as e:
            logger.error(f"Error in technical analysis for {pair}: {e}")
            return SignalComponent(
                component='technical',
                score=0.0,
                confidence=0.0,
                weight=self.base_weights['technical'],
                details={'error': str(e)}
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
    
    def _analyze_sentiment_signals(self, pair: str) -> SignalComponent:
        """Analyze market sentiment signals"""
        try:
            # Get comprehensive sentiment analysis
            sentiment_analysis = sentiment_analyzer.analyze_pair_sentiment(pair)
            
            # Extract sentiment components
            overall_sentiment = sentiment_analysis.overall_sentiment
            confidence_level = sentiment_analysis.confidence_level
            
            # Adjust score based on market mood strength
            mood_multiplier = {
                'strong': 1.0,
                'moderate': 0.7,
                'weak': 0.4
            }.get(sentiment_analysis.strength, 0.4)
            
            adjusted_score = overall_sentiment * mood_multiplier
            
            return SignalComponent(
                component='sentiment',
                score=np.clip(adjusted_score, -1.0, 1.0),
                confidence=confidence_level,
                weight=self.base_weights['sentiment'],
                details={
                    'market_mood': sentiment_analysis.market_mood,
                    'strength': sentiment_analysis.strength,
                    'source_count': len(sentiment_analysis.sentiment_sources),
                    'sources': [s.source for s in sentiment_analysis.sentiment_sources],
                    'raw_sentiment': overall_sentiment
                }
            )
            
        except Exception as e:
            logger.error(f"Error in sentiment analysis for {pair}: {e}")
            return SignalComponent(
                component='sentiment',
                score=0.0,
                confidence=0.0,
                weight=self.base_weights['sentiment'],
                details={'error': str(e)}
            )
    
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
        """Determine trading action with session-based volatility adjustments"""
        # Get current trading session volatility multiplier
        session_multiplier = self._get_session_volatility_multiplier()
        
        # Adjust minimum confidence based on market session
        min_confidence = 0.15 if session_multiplier > 1.0 else 0.25
        
        if confidence < min_confidence:
            return 'HOLD'
        
        # Calculate effective signal strength with session adjustment
        effective_strength = abs(signal_strength) * confidence * session_multiplier
        
        # More aggressive thresholds during high volatility sessions
        if session_multiplier >= 1.3:  # Active market sessions
            threshold = self.signal_thresholds['weak']  # Very sensitive
        elif session_multiplier >= 1.0:  # Normal sessions
            threshold = self.signal_thresholds['medium'] * 0.7  # Slightly more aggressive
        else:  # Low volatility sessions
            threshold = self.signal_thresholds['medium']
        
        # Determine action based on effective strength and direction
        if effective_strength >= threshold:
            if signal_strength > 0:
                return 'BUY'
            else:
                return 'SELL'
        else:
            # Ultra-aggressive scalping mode for 2-3 signals per day requirement
            # If we have ANY directional bias and reasonable confidence, trade it
            if confidence >= 0.6 and abs(signal_strength) > 0.005:  # 0.5% minimum movement
                if signal_strength > 0:
                    return 'BUY'
                else:
                    return 'SELL'
            return 'HOLD'
    
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
            
            # Get comprehensive technical analysis for timeframe information
            tech_analysis = technical_analyzer.get_comprehensive_technical_analysis(pair)
            awr = tech_analysis.get('average_weekly_range')
            
            if not awr:
                # Fallback: estimate from recent volatility
                forex_data = data_fetcher.fetch_forex_data(pair, '4hour')
                if forex_data and len(forex_data['data']) >= 42:  # ~1 week of 4H data
                    recent_prices = [item['close'] for item in forex_data['data'][:42]]
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
                strong_patterns = len(tech_analysis.get('candlestick_patterns_4h', []))
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
            
            # Calculate achievement probability with timeframe consideration
            achievement_prob = self._calculate_achievement_probability(
                target_pips, days_remaining, confidence, awr, pip_value
            )
            
            # Adjust probability based on signal strength and timeframe
            if signal_category.startswith("Strong"):
                achievement_prob = min(achievement_prob * 1.2, 0.95)  # Boost for strong signals
            elif signal_category.startswith("Medium"):
                achievement_prob = min(achievement_prob * 1.1, 0.85)  # Slight boost for medium
            
            return {
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
        
        return signals

# Global signal generator instance
signal_generator = SignalGenerator()