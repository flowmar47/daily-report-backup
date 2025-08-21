"""
Technical analysis module with 4-hour candlestick patterns and indicators
Critical: 4-hour timeframe is mandatory for candlestick pattern detection
"""
import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from datetime import datetime, timedelta
import logging

try:
    from src.core.config import settings
    from src.data_fetcher import data_fetcher
except ImportError:
    try:
        from .core.config import settings
        from .data_fetcher import data_fetcher
    except ImportError:
        from core.config import settings
        from data_fetcher import data_fetcher

logger = logging.getLogger(__name__)

@dataclass
class CandlestickPattern:
    """Candlestick pattern detection result"""
    name: str
    signal_type: str  # 'bullish', 'bearish', 'reversal'
    strength: float  # 0.0 to 1.0
    timestamp: str
    description: str

@dataclass
class TechnicalIndicators:
    """Technical indicators result"""
    rsi_4h: float
    rsi_daily: float
    macd_4h: Dict[str, float]
    macd_daily: Dict[str, float]
    bollinger_4h: Dict[str, float]
    bollinger_daily: Dict[str, float]
    sma_50: float
    sma_200: float
    ema_20_4h: float
    atr_4h: float
    stochastic_4h: Dict[str, float]

class TechnicalAnalyzer:
    """Technical analysis with 4H candlestick focus"""
    
    def __init__(self):
        self.pip_values = {
            "EURUSD": 0.0001,
            "USDJPY": 0.01,
            "GBPUSD": 0.0001,
            "AUDUSD": 0.0001,
            "USDCAD": 0.0001
        }
    
    def analyze_4h_candlesticks(self, forex_data: Dict) -> List[CandlestickPattern]:
        """
        CRITICAL: Analyze 4-hour candlestick patterns specifically
        This is the core requirement for pattern detection
        """
        if not forex_data or 'data' not in forex_data:
            return []
        
        data = forex_data['data']
        if len(data) < 4:  # Need at least 4 candles for complex patterns
            return []
        
        df = pd.DataFrame(data)
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df = df.sort_values('timestamp')
        
        patterns = []
        
        # Single candle patterns
        patterns.extend(self._detect_hammer(df))
        patterns.extend(self._detect_shooting_star(df))
        patterns.extend(self._detect_doji(df))
        patterns.extend(self._detect_spinning_top(df))
        
        # Two candle patterns
        patterns.extend(self._detect_engulfing(df))
        patterns.extend(self._detect_harami(df))
        
        # Three candle patterns
        patterns.extend(self._detect_morning_evening_star(df))
        patterns.extend(self._detect_three_white_soldiers(df))
        patterns.extend(self._detect_three_black_crows(df))
        
        # Sort by timestamp (most recent first)
        patterns.sort(key=lambda x: x.timestamp, reverse=True)
        
        return patterns[:10]  # Return top 10 most recent patterns
    
    def _detect_hammer(self, df: pd.DataFrame) -> List[CandlestickPattern]:
        """Detect hammer candlestick patterns (bullish reversal)"""
        patterns = []
        
        for i in range(len(df)):
            candle = df.iloc[i]
            
            # Calculate candle properties
            body = abs(candle['close'] - candle['open'])
            upper_shadow = candle['high'] - max(candle['open'], candle['close'])
            lower_shadow = min(candle['open'], candle['close']) - candle['low']
            total_range = candle['high'] - candle['low']
            
            if total_range == 0:
                continue
            
            # Hammer criteria
            if (lower_shadow > 2 * body and  # Long lower shadow
                upper_shadow < 0.1 * total_range and  # Small upper shadow
                body < 0.3 * total_range):  # Small body
                
                strength = min(lower_shadow / body, 1.0) * 0.8
                
                patterns.append(CandlestickPattern(
                    name="Hammer",
                    signal_type="bullish",
                    strength=strength,
                    timestamp=candle['timestamp'].isoformat(),
                    description="Bullish reversal pattern with long lower shadow"
                ))
        
        return patterns
    
    def _detect_shooting_star(self, df: pd.DataFrame) -> List[CandlestickPattern]:
        """Detect shooting star patterns (bearish reversal)"""
        patterns = []
        
        for i in range(len(df)):
            candle = df.iloc[i]
            
            body = abs(candle['close'] - candle['open'])
            upper_shadow = candle['high'] - max(candle['open'], candle['close'])
            lower_shadow = min(candle['open'], candle['close']) - candle['low']
            total_range = candle['high'] - candle['low']
            
            if total_range == 0:
                continue
            
            # Shooting star criteria
            if (upper_shadow > 2 * body and  # Long upper shadow
                lower_shadow < 0.1 * total_range and  # Small lower shadow
                body < 0.3 * total_range):  # Small body
                
                strength = min(upper_shadow / body, 1.0) * 0.8
                
                patterns.append(CandlestickPattern(
                    name="Shooting Star",
                    signal_type="bearish",
                    strength=strength,
                    timestamp=candle['timestamp'].isoformat(),
                    description="Bearish reversal pattern with long upper shadow"
                ))
        
        return patterns
    
    def _detect_doji(self, df: pd.DataFrame) -> List[CandlestickPattern]:
        """Detect doji patterns (reversal/indecision)"""
        patterns = []
        
        for i in range(len(df)):
            candle = df.iloc[i]
            
            body = abs(candle['close'] - candle['open'])
            total_range = candle['high'] - candle['low']
            
            if total_range == 0:
                continue
            
            # Doji criteria - very small body relative to range
            if body < 0.1 * total_range:
                strength = 1.0 - (body / total_range) * 10  # Smaller body = stronger doji
                
                patterns.append(CandlestickPattern(
                    name="Doji",
                    signal_type="reversal",
                    strength=strength * 0.7,
                    timestamp=candle['timestamp'].isoformat(),
                    description="Indecision pattern indicating potential reversal"
                ))
        
        return patterns
    
    def _detect_spinning_top(self, df: pd.DataFrame) -> List[CandlestickPattern]:
        """Detect spinning top patterns"""
        patterns = []
        
        for i in range(len(df)):
            candle = df.iloc[i]
            
            body = abs(candle['close'] - candle['open'])
            upper_shadow = candle['high'] - max(candle['open'], candle['close'])
            lower_shadow = min(candle['open'], candle['close']) - candle['low']
            total_range = candle['high'] - candle['low']
            
            if total_range == 0:
                continue
            
            # Spinning top criteria
            if (body < 0.3 * total_range and  # Small body
                upper_shadow > 0.3 * total_range and  # Upper shadow
                lower_shadow > 0.3 * total_range):  # Lower shadow
                
                strength = (upper_shadow + lower_shadow) / (2 * total_range)
                
                patterns.append(CandlestickPattern(
                    name="Spinning Top",
                    signal_type="reversal",
                    strength=strength * 0.6,
                    timestamp=candle['timestamp'].isoformat(),
                    description="Indecision pattern with long shadows"
                ))
        
        return patterns
    
    def _detect_engulfing(self, df: pd.DataFrame) -> List[CandlestickPattern]:
        """Detect bullish and bearish engulfing patterns"""
        patterns = []
        
        for i in range(1, len(df)):
            prev_candle = df.iloc[i-1]
            curr_candle = df.iloc[i]
            
            prev_body = abs(prev_candle['close'] - prev_candle['open'])
            curr_body = abs(curr_candle['close'] - curr_candle['open'])
            
            # Bullish engulfing
            if (prev_candle['close'] < prev_candle['open'] and  # Previous bearish
                curr_candle['close'] > curr_candle['open'] and  # Current bullish
                curr_candle['open'] < prev_candle['close'] and  # Opens below prev close
                curr_candle['close'] > prev_candle['open'] and  # Closes above prev open
                curr_body > prev_body * 1.1):  # Larger body
                
                strength = min(curr_body / prev_body, 2.0) / 2.0
                
                patterns.append(CandlestickPattern(
                    name="Bullish Engulfing",
                    signal_type="bullish",
                    strength=strength * 0.9,
                    timestamp=curr_candle['timestamp'].isoformat(),
                    description="Bullish reversal - current candle engulfs previous bearish candle"
                ))
            
            # Bearish engulfing
            elif (prev_candle['close'] > prev_candle['open'] and  # Previous bullish
                  curr_candle['close'] < curr_candle['open'] and  # Current bearish
                  curr_candle['open'] > prev_candle['close'] and  # Opens above prev close
                  curr_candle['close'] < prev_candle['open'] and  # Closes below prev open
                  curr_body > prev_body * 1.1):  # Larger body
                
                strength = min(curr_body / prev_body, 2.0) / 2.0
                
                patterns.append(CandlestickPattern(
                    name="Bearish Engulfing",
                    signal_type="bearish",
                    strength=strength * 0.9,
                    timestamp=curr_candle['timestamp'].isoformat(),
                    description="Bearish reversal - current candle engulfs previous bullish candle"
                ))
        
        return patterns
    
    def _detect_harami(self, df: pd.DataFrame) -> List[CandlestickPattern]:
        """Detect harami patterns"""
        patterns = []
        
        for i in range(1, len(df)):
            prev_candle = df.iloc[i-1]
            curr_candle = df.iloc[i]
            
            prev_body = abs(prev_candle['close'] - prev_candle['open'])
            curr_body = abs(curr_candle['close'] - curr_candle['open'])
            
            # Harami criteria - current candle body within previous candle body
            if (prev_body > curr_body * 1.5 and  # Previous body significantly larger
                max(curr_candle['open'], curr_candle['close']) <= max(prev_candle['open'], prev_candle['close']) and
                min(curr_candle['open'], curr_candle['close']) >= min(prev_candle['open'], prev_candle['close'])):
                
                signal_type = "bullish" if prev_candle['close'] < prev_candle['open'] else "bearish"
                # Avoid divide by zero error
                strength = (prev_body / max(curr_body, 0.0001)) / 10.0  # Normalized strength
                
                patterns.append(CandlestickPattern(
                    name="Harami",
                    signal_type=signal_type,
                    strength=min(strength, 1.0) * 0.7,
                    timestamp=curr_candle['timestamp'].isoformat(),
                    description=f"{signal_type.capitalize()} harami - small candle within large candle"
                ))
        
        return patterns
    
    def _detect_morning_evening_star(self, df: pd.DataFrame) -> List[CandlestickPattern]:
        """Detect morning star (bullish) and evening star (bearish) patterns"""
        patterns = []
        
        for i in range(2, len(df)):
            candle1 = df.iloc[i-2]  # First candle
            candle2 = df.iloc[i-1]  # Star candle
            candle3 = df.iloc[i]    # Third candle
            
            body1 = abs(candle1['close'] - candle1['open'])
            body2 = abs(candle2['close'] - candle2['open'])
            body3 = abs(candle3['close'] - candle3['open'])
            
            # Morning star (bullish reversal)
            if (candle1['close'] < candle1['open'] and  # First candle bearish
                body2 < body1 * 0.3 and  # Star has small body
                candle3['close'] > candle3['open'] and  # Third candle bullish
                candle3['close'] > (candle1['open'] + candle1['close']) / 2):  # Third closes above midpoint of first
                
                strength = (body1 + body3) / (body2 + 0.0001)  # Avoid division by zero
                strength = min(strength / 20.0, 1.0)
                
                patterns.append(CandlestickPattern(
                    name="Morning Star",
                    signal_type="bullish",
                    strength=strength * 0.85,
                    timestamp=candle3['timestamp'].isoformat(),
                    description="Bullish reversal - three candle pattern"
                ))
            
            # Evening star (bearish reversal)
            elif (candle1['close'] > candle1['open'] and  # First candle bullish
                  body2 < body1 * 0.3 and  # Star has small body
                  candle3['close'] < candle3['open'] and  # Third candle bearish
                  candle3['close'] < (candle1['open'] + candle1['close']) / 2):  # Third closes below midpoint of first
                
                strength = (body1 + body3) / (body2 + 0.0001)
                strength = min(strength / 20.0, 1.0)
                
                patterns.append(CandlestickPattern(
                    name="Evening Star",
                    signal_type="bearish",
                    strength=strength * 0.85,
                    timestamp=candle3['timestamp'].isoformat(),
                    description="Bearish reversal - three candle pattern"
                ))
        
        return patterns
    
    def _detect_three_white_soldiers(self, df: pd.DataFrame) -> List[CandlestickPattern]:
        """Detect three white soldiers (bullish continuation)"""
        patterns = []
        
        for i in range(2, len(df)):
            candle1 = df.iloc[i-2]
            candle2 = df.iloc[i-1]
            candle3 = df.iloc[i]
            
            # All three candles bullish with increasing closes
            if (candle1['close'] > candle1['open'] and
                candle2['close'] > candle2['open'] and
                candle3['close'] > candle3['open'] and
                candle2['close'] > candle1['close'] and
                candle3['close'] > candle2['close'] and
                candle2['open'] > candle1['open'] and
                candle3['open'] > candle2['open']):
                
                # Calculate strength based on consistency
                total_gain = candle3['close'] - candle1['open']
                avg_body = (abs(candle1['close'] - candle1['open']) + 
                          abs(candle2['close'] - candle2['open']) + 
                          abs(candle3['close'] - candle3['open'])) / 3
                
                strength = min(total_gain / (avg_body * 5), 1.0)
                
                patterns.append(CandlestickPattern(
                    name="Three White Soldiers",
                    signal_type="bullish",
                    strength=strength * 0.8,
                    timestamp=candle3['timestamp'].isoformat(),
                    description="Strong bullish continuation - three consecutive bullish candles"
                ))
        
        return patterns
    
    def _detect_three_black_crows(self, df: pd.DataFrame) -> List[CandlestickPattern]:
        """Detect three black crows (bearish continuation)"""
        patterns = []
        
        for i in range(2, len(df)):
            candle1 = df.iloc[i-2]
            candle2 = df.iloc[i-1]
            candle3 = df.iloc[i]
            
            # All three candles bearish with decreasing closes
            if (candle1['close'] < candle1['open'] and
                candle2['close'] < candle2['open'] and
                candle3['close'] < candle3['open'] and
                candle2['close'] < candle1['close'] and
                candle3['close'] < candle2['close'] and
                candle2['open'] < candle1['open'] and
                candle3['open'] < candle2['open']):
                
                # Calculate strength based on consistency
                total_loss = candle1['open'] - candle3['close']
                avg_body = (abs(candle1['close'] - candle1['open']) + 
                          abs(candle2['close'] - candle2['open']) + 
                          abs(candle3['close'] - candle3['open'])) / 3
                
                strength = min(total_loss / (avg_body * 5), 1.0)
                
                patterns.append(CandlestickPattern(
                    name="Three Black Crows",
                    signal_type="bearish",
                    strength=strength * 0.8,
                    timestamp=candle3['timestamp'].isoformat(),
                    description="Strong bearish continuation - three consecutive bearish candles"
                ))
        
        return patterns
    
    def calculate_rsi(self, prices: List[float], period: int = 14) -> Optional[float]:
        """Calculate RSI indicator"""
        if len(prices) < period + 1:
            return None
        
        deltas = np.diff(prices)
        gains = np.where(deltas > 0, deltas, 0)
        losses = np.where(deltas < 0, -deltas, 0)
        
        avg_gain = np.mean(gains[:period])
        avg_loss = np.mean(losses[:period])
        
        if avg_loss == 0:
            return 100.0
        
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        
        return float(rsi)
    
    def calculate_macd(self, prices: List[float], fast: int = 12, 
                      slow: int = 26, signal: int = 9) -> Optional[Dict[str, float]]:
        """Calculate MACD indicator"""
        if len(prices) < slow + signal:
            return None
        
        prices_array = np.array(prices)
        
        # Calculate EMAs for all values to get MACD line history
        macd_values = []
        for i in range(slow, len(prices)):
            ema_fast = self._calculate_ema(prices_array[:i+1], fast)
            ema_slow = self._calculate_ema(prices_array[:i+1], slow)
            
            if ema_fast is not None and ema_slow is not None:
                macd_values.append(ema_fast - ema_slow)
        
        if len(macd_values) < signal:
            return None
        
        # Calculate signal line (EMA of MACD values)
        macd_array = np.array(macd_values)
        signal_line = self._calculate_ema(macd_array, signal)
        
        if signal_line is None:
            return None
        
        # Current MACD line value
        macd_line = macd_values[-1]
        
        # Histogram
        histogram = macd_line - signal_line
        
        return {
            'macd': float(macd_line),
            'signal': float(signal_line),
            'histogram': float(histogram)
        }
    
    def calculate_bollinger_bands(self, prices: List[float], period: int = 20, 
                                 std_dev: float = 2.0) -> Optional[Dict[str, float]]:
        """Calculate Bollinger Bands"""
        if len(prices) < period:
            return None
        
        prices_array = np.array(prices[-period:])
        
        middle_band = np.mean(prices_array)
        std = np.std(prices_array)
        
        upper_band = middle_band + (std_dev * std)
        lower_band = middle_band - (std_dev * std)
        
        current_price = prices[-1]
        position = (current_price - lower_band) / (upper_band - lower_band)
        
        return {
            'upper': float(upper_band),
            'middle': float(middle_band),
            'lower': float(lower_band),
            'position': float(position)  # 0 = at lower band, 1 = at upper band
        }
    
    def calculate_atr(self, high: List[float], low: List[float], 
                     close: List[float], period: int = 14) -> Optional[float]:
        """Calculate Average True Range"""
        if len(high) < period + 1 or len(low) < period + 1 or len(close) < period + 1:
            return None
        
        true_ranges = []
        
        for i in range(1, len(high)):
            hl = high[i] - low[i]
            hc = abs(high[i] - close[i-1])
            lc = abs(low[i] - close[i-1])
            
            true_range = max(hl, hc, lc)
            true_ranges.append(true_range)
        
        if len(true_ranges) < period:
            return None
        
        atr = np.mean(true_ranges[-period:])
        return float(atr)
    
    def calculate_stochastic(self, high: List[float], low: List[float], 
                           close: List[float], k_period: int = 14, 
                           d_period: int = 3) -> Optional[Dict[str, float]]:
        """Calculate Stochastic Oscillator"""
        if len(high) < k_period or len(low) < k_period or len(close) < k_period:
            return None
        
        # %K calculation
        lowest_low = min(low[-k_period:])
        highest_high = max(high[-k_period:])
        current_close = close[-1]
        
        if highest_high == lowest_low:
            k_percent = 50.0
        else:
            k_percent = ((current_close - lowest_low) / (highest_high - lowest_low)) * 100
        
        # %D calculation (SMA of %K)
        # For simplicity, using current %K as %D (in practice, you'd need historical %K values)
        d_percent = k_percent
        
        return {
            'k_percent': float(k_percent),
            'd_percent': float(d_percent)
        }
    
    def _calculate_ema(self, prices: np.ndarray, period: int) -> Optional[float]:
        """Calculate Exponential Moving Average"""
        if len(prices) < period:
            return None
        
        multiplier = 2.0 / (period + 1)
        ema = prices[0]
        
        for price in prices[1:]:
            ema = (price * multiplier) + (ema * (1 - multiplier))
        
        return float(ema)
    
    def get_comprehensive_technical_analysis(self, pair: str) -> Dict[str, Any]:
        """
        Optimized technical analysis for rate limiting optimization
        Reduced to 2 timeframes: 1hour and daily (66% reduction in API calls)
        Maintains analysis quality while preventing rate limit issues
        """
        # Fetch optimized timeframe data (reduced from 4 to 2 timeframes)
        forex_1h = data_fetcher.fetch_forex_data(pair, '1hour')
        forex_daily = data_fetcher.fetch_forex_data(pair, 'daily')
        
        if not forex_1h and not forex_daily:
            return {'error': f'No forex data available for {pair} from any timeframe'}
        
        # At least one timeframe required for analysis
        available_timeframes = []
        if forex_1h: available_timeframes.append('1hour')
        if forex_daily: available_timeframes.append('daily')
        
        analysis_result = {
            'pair': pair,
            'timestamp': datetime.now().isoformat(),
            'available_timeframes': available_timeframes,
            'candlestick_patterns_daily': [],
            'candlestick_patterns_1h': [],
            'technical_indicators': {},
            'signal_summary': {},
            'multi_timeframe_signals': {},
            'average_weekly_range': None
        }
        
        # Optimized timeframe patterns (reduced from 4 to 2 timeframes)
        # Daily patterns (highest weight - long term trends)
        if forex_daily:
            patterns_daily = self.analyze_4h_candlesticks(forex_daily)
            analysis_result['candlestick_patterns_daily'] = [
                {
                    'name': p.name,
                    'signal_type': p.signal_type,
                    'strength': p.strength * 1.2,  # Increased weight for daily patterns
                    'timestamp': p.timestamp,
                    'description': f"Daily {p.description}",
                    'timeframe': 'daily'
                } for p in patterns_daily
            ]
        
        # 1H patterns (medium weight for intraday signals)
        if forex_1h:
            patterns_1h = self.analyze_4h_candlesticks(forex_1h)  # Same patterns, different timeframe
            analysis_result['candlestick_patterns_1h'] = [
                {
                    'name': p.name,
                    'signal_type': p.signal_type,
                    'strength': p.strength * 0.8,  # Standard weight for 1h timeframe
                    'timestamp': p.timestamp,
                    'description': f"1H {p.description}",
                    'timeframe': '1hour'
                } for p in patterns_1h
            ]
        
        # Optimized technical indicators (2 timeframes only)
        indicators = {}
        multi_timeframe_signals = {}
        
        # Define optimized timeframes and their data
        timeframe_data = {}
        if forex_1h:
            timeframe_data['1hour'] = {
                'prices': [item['close'] for item in forex_1h['data']],
                'highs': [item['high'] for item in forex_1h['data']],
                'lows': [item['low'] for item in forex_1h['data']]
            }
        if forex_daily:
            timeframe_data['daily'] = {
                'prices': [item['close'] for item in forex_daily['data']],
                'highs': [item['high'] for item in forex_daily['data']],
                'lows': [item['low'] for item in forex_daily['data']]
            }
        
        # Calculate indicators for each timeframe
        for timeframe, data in timeframe_data.items():
            tf_indicators = {}
            tf_signals = {}
            
            prices = data['prices']
            highs = data['highs']
            lows = data['lows']
            
            # RSI (key for intraday signals)
            rsi = self.calculate_rsi(prices, 14)
            if rsi is not None:
                tf_indicators[f'rsi_{timeframe}'] = rsi
                # Generate RSI signals
                if rsi < 30:
                    tf_signals['rsi'] = {'signal': 'bullish', 'strength': (30 - rsi) / 30}
                elif rsi > 70:
                    tf_signals['rsi'] = {'signal': 'bearish', 'strength': (rsi - 70) / 30}
            
            # MACD (trend detection)
            macd = self.calculate_macd(prices)
            if macd:
                tf_indicators[f'macd_{timeframe}'] = macd
                # MACD signal
                if 'histogram' in macd and macd['histogram'] > 0:
                    tf_signals['macd'] = {'signal': 'bullish', 'strength': min(abs(macd['histogram']) * 1000, 1.0)}
                elif 'histogram' in macd and macd['histogram'] < 0:
                    tf_signals['macd'] = {'signal': 'bearish', 'strength': min(abs(macd['histogram']) * 1000, 1.0)}
            
            # Bollinger Bands (volatility breakouts)
            bb = self.calculate_bollinger_bands(prices, 20)
            if bb:
                tf_indicators[f'bollinger_{timeframe}'] = bb
                # Bollinger Band signals
                if 'position' in bb:
                    if bb['position'] < 0.2:
                        tf_signals['bollinger'] = {'signal': 'bullish', 'strength': (0.2 - bb['position']) / 0.2}
                    elif bb['position'] > 0.8:
                        tf_signals['bollinger'] = {'signal': 'bearish', 'strength': (bb['position'] - 0.8) / 0.2}
            
            # Moving averages for trend
            if len(prices) >= 20:
                ema_20 = self._calculate_ema(np.array(prices), 20)
                if ema_20:
                    tf_indicators[f'ema_20_{timeframe}'] = ema_20
                    # Price vs EMA signal
                    if prices[-1] > ema_20:
                        tf_signals['ema_trend'] = {'signal': 'bullish', 'strength': 0.5}
                    else:
                        tf_signals['ema_trend'] = {'signal': 'bearish', 'strength': 0.5}
            
            # ATR for volatility
            atr = self.calculate_atr(highs, lows, prices, 14)
            if atr:
                tf_indicators[f'atr_{timeframe}'] = atr
            
            # Stochastic for momentum
            stoch = self.calculate_stochastic(highs, lows, prices)
            if stoch:
                tf_indicators[f'stochastic_{timeframe}'] = stoch
                # Stochastic signals
                if stoch['k_percent'] < 20:
                    tf_signals['stochastic'] = {'signal': 'bullish', 'strength': (20 - stoch['k_percent']) / 20}
                elif stoch['k_percent'] > 80:
                    tf_signals['stochastic'] = {'signal': 'bearish', 'strength': (stoch['k_percent'] - 80) / 20}
            
            # Store timeframe-specific indicators and signals
            indicators.update(tf_indicators)
            multi_timeframe_signals[timeframe] = tf_signals
        
        analysis_result['technical_indicators'] = indicators
        analysis_result['multi_timeframe_signals'] = multi_timeframe_signals
        
        # Calculate Average Weekly Range for target setting using daily data
        if forex_daily and 'daily' in timeframe_data:
            highs_daily = timeframe_data['daily']['highs']
            lows_daily = timeframe_data['daily']['lows']
            
            if len(highs_daily) >= 7:  # 7 daily candles = 1 week
                weekly_ranges = []
                for i in range(0, len(highs_daily) - 7, 7):
                    week_high = max(highs_daily[i:i+7])
                    week_low = min(lows_daily[i:i+7])
                    weekly_range = week_high - week_low
                    weekly_ranges.append(weekly_range)
                
                if weekly_ranges:
                    analysis_result['average_weekly_range'] = float(np.mean(weekly_ranges))
        
        # Add short-term pattern detection for intraday signals
        short_term_signals = self._detect_short_term_patterns(timeframe_data, multi_timeframe_signals)
        analysis_result['short_term_signals'] = short_term_signals
        
        # Generate enhanced signal summary with short-term patterns
        # Generate signal summary with available patterns
        daily_patterns = analysis_result.get('candlestick_patterns_daily', [])
        analysis_result['signal_summary'] = self._generate_signal_summary(daily_patterns, indicators, short_term_signals)
        
        return analysis_result
    
    def _detect_short_term_patterns(self, timeframe_data: Dict, multi_timeframe_signals: Dict) -> Dict[str, Any]:
        """
        Detect short-term patterns for intraday trading signals
        Focus on momentum shifts, breakouts, and volatility expansions
        """
        short_term_signals = {
            'momentum_shifts': [],
            'volatility_breakouts': [],
            'trend_continuations': [],
            'reversal_patterns': [],
            'overall_signal': 'neutral',
            'confidence': 0.0
        }
        
        try:
            # Process 30min and 1hour data for short-term patterns
            for timeframe in ['30min', '1hour']:
                if timeframe not in timeframe_data:
                    continue
                
                data = timeframe_data[timeframe]
                prices = data['prices']
                highs = data['highs']
                lows = data['lows']
                
                if len(prices) < 20:  # Need minimum data
                    continue
                
                # 1. Momentum Shift Detection
                momentum_signals = self._detect_momentum_shifts(prices, timeframe)
                short_term_signals['momentum_shifts'].extend(momentum_signals)
                
                # 2. Volatility Breakout Detection
                breakout_signals = self._detect_volatility_breakouts(highs, lows, prices, timeframe)
                short_term_signals['volatility_breakouts'].extend(breakout_signals)
                
                # 3. Trend Continuation Patterns
                continuation_signals = self._detect_trend_continuations(prices, timeframe)
                short_term_signals['trend_continuations'].extend(continuation_signals)
                
                # 4. Quick Reversal Patterns
                reversal_signals = self._detect_quick_reversals(prices, highs, lows, timeframe)
                short_term_signals['reversal_patterns'].extend(reversal_signals)
            
            # Calculate overall short-term signal
            all_signals = (short_term_signals['momentum_shifts'] + 
                          short_term_signals['volatility_breakouts'] + 
                          short_term_signals['trend_continuations'] + 
                          short_term_signals['reversal_patterns'])
            
            if all_signals:
                bullish_signals = [s for s in all_signals if s['signal'] == 'bullish']
                bearish_signals = [s for s in all_signals if s['signal'] == 'bearish']
                
                # Determine overall signal
                if len(bullish_signals) > len(bearish_signals):
                    short_term_signals['overall_signal'] = 'bullish'
                    short_term_signals['confidence'] = len(bullish_signals) / len(all_signals)
                elif len(bearish_signals) > len(bullish_signals):
                    short_term_signals['overall_signal'] = 'bearish'
                    short_term_signals['confidence'] = len(bearish_signals) / len(all_signals)
                else:
                    short_term_signals['overall_signal'] = 'neutral'
                    short_term_signals['confidence'] = 0.5
            
        except Exception as e:
            logger.error(f"Error detecting short-term patterns: {e}")
        
        return short_term_signals
    
    def _detect_momentum_shifts(self, prices: List[float], timeframe: str) -> List[Dict]:
        """Detect momentum shifts using price velocity changes"""
        signals = []
        if len(prices) < 10:
            return signals
        
        try:
            # Calculate price momentum (rate of change)
            momentum_period = 5
            momentum_values = []
            
            for i in range(momentum_period, len(prices)):
                momentum = (prices[i] - prices[i - momentum_period]) / prices[i - momentum_period] * 100
                momentum_values.append(momentum)
            
            if len(momentum_values) >= 3:
                # Recent momentum vs previous momentum
                recent_momentum = np.mean(momentum_values[-3:])
                previous_momentum = np.mean(momentum_values[-6:-3]) if len(momentum_values) >= 6 else 0
                
                momentum_change = recent_momentum - previous_momentum
                
                # Significant momentum shift detected
                if abs(momentum_change) > 0.01:  # 1% momentum change
                    signal_strength = min(abs(momentum_change) * 10, 1.0)
                    
                    signals.append({
                        'pattern': 'momentum_shift',
                        'signal': 'bullish' if momentum_change > 0 else 'bearish',
                        'strength': signal_strength,
                        'timeframe': timeframe,
                        'description': f"Momentum shift {'accelerating' if momentum_change > 0 else 'decelerating'}"
                    })
        
        except Exception as e:
            logger.error(f"Error detecting momentum shifts: {e}")
        
        return signals
    
    def _detect_volatility_breakouts(self, highs: List[float], lows: List[float], 
                                   prices: List[float], timeframe: str) -> List[Dict]:
        """Detect volatility expansion breakouts"""
        signals = []
        if len(prices) < 20:
            return signals
        
        try:
            # Calculate recent volatility vs historical volatility
            recent_range = max(highs[-5:]) - min(lows[-5:])  # Last 5 periods
            historical_range = np.mean([max(highs[i:i+5]) - min(lows[i:i+5]) 
                                      for i in range(0, len(highs)-5, 5)])
            
            volatility_expansion = recent_range / historical_range if historical_range > 0 else 1.0
            
            # Detect breakout direction
            if volatility_expansion > 1.5:  # 50% expansion
                recent_prices = prices[-5:]
                trend_direction = 'bullish' if recent_prices[-1] > recent_prices[0] else 'bearish'
                
                signals.append({
                    'pattern': 'volatility_breakout',
                    'signal': trend_direction,
                    'strength': min((volatility_expansion - 1.0) / 2.0, 1.0),
                    'timeframe': timeframe,
                    'description': f"Volatility breakout {trend_direction} ({volatility_expansion:.1f}x expansion)"
                })
        
        except Exception as e:
            logger.error(f"Error detecting volatility breakouts: {e}")
        
        return signals
    
    def _detect_trend_continuations(self, prices: List[float], timeframe: str) -> List[Dict]:
        """Detect trend continuation patterns"""
        signals = []
        if len(prices) < 15:
            return signals
        
        try:
            # Calculate moving averages for trend detection
            short_ma = np.mean(prices[-5:])
            medium_ma = np.mean(prices[-10:])
            long_ma = np.mean(prices[-15:])
            
            # Strong trend continuation: all MAs aligned + price action confirms
            if short_ma > medium_ma > long_ma:  # Uptrend
                trend_strength = (short_ma - long_ma) / long_ma
                if trend_strength > 0.002:  # 0.2% trend strength
                    signals.append({
                        'pattern': 'trend_continuation',
                        'signal': 'bullish',
                        'strength': min(trend_strength * 100, 1.0),
                        'timeframe': timeframe,
                        'description': f"Strong uptrend continuation"
                    })
            
            elif short_ma < medium_ma < long_ma:  # Downtrend
                trend_strength = (long_ma - short_ma) / long_ma
                if trend_strength > 0.002:
                    signals.append({
                        'pattern': 'trend_continuation',
                        'signal': 'bearish',
                        'strength': min(trend_strength * 100, 1.0),
                        'timeframe': timeframe,
                        'description': f"Strong downtrend continuation"
                    })
        
        except Exception as e:
            logger.error(f"Error detecting trend continuations: {e}")
        
        return signals
    
    def _detect_quick_reversals(self, prices: List[float], highs: List[float], 
                              lows: List[float], timeframe: str) -> List[Dict]:
        """Detect quick reversal patterns for intraday trading"""
        signals = []
        if len(prices) < 10:
            return signals
        
        try:
            # V-shaped reversal detection
            for i in range(5, len(prices) - 3):
                # Look for V-bottom (bullish reversal)
                if (prices[i] < prices[i-1] < prices[i-2] and
                    prices[i] < prices[i+1] < prices[i+2]):
                    
                    reversal_strength = (prices[i+2] - prices[i]) / prices[i]
                    if reversal_strength > 0.001:  # 0.1% reversal
                        signals.append({
                            'pattern': 'v_reversal',
                            'signal': 'bullish',
                            'strength': min(reversal_strength * 50, 1.0),
                            'timeframe': timeframe,
                            'description': f"V-bottom reversal pattern"
                        })
                
                # Look for inverted V-top (bearish reversal)
                elif (prices[i] > prices[i-1] > prices[i-2] and
                      prices[i] > prices[i+1] > prices[i+2]):
                    
                    reversal_strength = (prices[i] - prices[i+2]) / prices[i]
                    if reversal_strength > 0.001:
                        signals.append({
                            'pattern': 'inverted_v_reversal',
                            'signal': 'bearish',
                            'strength': min(reversal_strength * 50, 1.0),
                            'timeframe': timeframe,
                            'description': f"Inverted V-top reversal pattern"
                        })
        
        except Exception as e:
            logger.error(f"Error detecting quick reversals: {e}")
        
        return signals
    
    def _generate_signal_summary(self, patterns: List[CandlestickPattern], 
                               indicators: Dict, short_term_signals: Dict = None) -> Dict[str, Any]:
        """Generate overall technical signal summary"""
        bullish_signals = 0
        bearish_signals = 0
        signal_strength = 0.0
        
        # Candlestick pattern signals (higher weight)
        for pattern in patterns[:3]:  # Top 3 most recent patterns
            if pattern.signal_type == 'bullish':
                bullish_signals += 1
                signal_strength += pattern.strength * 2.0  # Higher weight for patterns
            elif pattern.signal_type == 'bearish':
                bearish_signals += 1
                signal_strength -= pattern.strength * 2.0
        
        # RSI signals
        if indicators.get('rsi_4h'):
            rsi = indicators['rsi_4h']
            if rsi < 30:
                bullish_signals += 1
                signal_strength += 0.5
            elif rsi > 70:
                bearish_signals += 1
                signal_strength -= 0.5
        
        # MACD signals
        if indicators.get('macd_4h'):
            macd = indicators['macd_4h']
            if macd['histogram'] > 0:
                bullish_signals += 1
                signal_strength += 0.3
            else:
                bearish_signals += 1
                signal_strength -= 0.3
        
        # Bollinger Bands signals
        if indicators.get('bollinger_4h'):
            bb = indicators['bollinger_4h']
            if bb['position'] < 0.2:  # Near lower band
                bullish_signals += 1
                signal_strength += 0.4
            elif bb['position'] > 0.8:  # Near upper band
                bearish_signals += 1
                signal_strength -= 0.4
        
        # Overall signal determination
        if bullish_signals > bearish_signals:
            overall_signal = 'bullish'
        elif bearish_signals > bullish_signals:
            overall_signal = 'bearish'
        else:
            overall_signal = 'neutral'
        
        return {
            'overall_signal': overall_signal,
            'bullish_signals_count': bullish_signals,
            'bearish_signals_count': bearish_signals,
            'signal_strength': float(np.clip(signal_strength, -1.0, 1.0)),
            'confidence': float(abs(signal_strength) / max(bullish_signals + bearish_signals, 1))
        }

# Global technical analyzer instance
technical_analyzer = TechnicalAnalyzer()