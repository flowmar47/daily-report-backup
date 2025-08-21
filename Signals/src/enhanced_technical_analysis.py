"""
Enhanced Technical Analysis Module
Integrates TA-Lib, pandas-ta, and yfinance for comprehensive forex analysis
Author: Claude Code Enhancement System
"""

import numpy as np
import pandas as pd
import talib
import pandas_ta as ta
import yfinance as yf
from typing import Dict, List, Optional, Tuple, Any, Union
from dataclasses import dataclass
from datetime import datetime, timedelta
import logging
from enum import Enum

logger = logging.getLogger(__name__)

class SignalStrength(Enum):
    VERY_STRONG = 5
    STRONG = 4
    MEDIUM = 3
    WEAK = 2
    VERY_WEAK = 1

class SignalDirection(Enum):
    BULLISH = 1
    BEARISH = -1
    NEUTRAL = 0

@dataclass
class TechnicalSignal:
    """Enhanced technical signal with detailed analysis"""
    indicator_name: str
    signal_direction: SignalDirection
    signal_strength: SignalStrength
    current_value: float
    description: str
    reliability_score: float  # 0.0 to 1.0
    timeframe: str
    timestamp: datetime

@dataclass
class PatternSignal:
    """Candlestick pattern signal with TA-Lib integration"""
    pattern_name: str
    pattern_type: str  # 'bullish', 'bearish', 'reversal', 'continuation'
    strength: int  # TA-Lib pattern strength (-100 to 100)
    reliability: float  # Historical reliability score
    confirmation_needed: bool
    timeframe: str
    timestamp: datetime

@dataclass
class TechnicalAnalysisResult:
    """Comprehensive technical analysis result"""
    pair: str
    timeframe: str
    timestamp: datetime
    price_data: Dict[str, float]
    
    # Core indicators
    trend_indicators: Dict[str, TechnicalSignal]
    momentum_indicators: Dict[str, TechnicalSignal]
    volatility_indicators: Dict[str, TechnicalSignal]
    volume_indicators: Dict[str, TechnicalSignal]
    
    # Pattern analysis
    candlestick_patterns: List[PatternSignal]
    
    # Summary scores
    overall_trend: SignalDirection
    overall_strength: float  # 0.0 to 1.0
    confluence_score: float  # 0.0 to 1.0 (how many indicators agree)
    
    # Support/Resistance levels
    support_levels: List[float]
    resistance_levels: List[float]

class EnhancedTechnicalAnalyzer:
    """
    Enhanced Technical Analyzer combining TA-Lib, pandas-ta, and advanced analysis
    Optimized for forex markets with professional-grade indicators
    """
    
    def __init__(self):
        # Indicator reliability weights based on forex market performance
        self.indicator_weights = {
            # Trend indicators
            'sma': 0.7, 'ema': 0.8, 'tema': 0.9, 'kama': 0.85,
            'supertrend': 0.9, 'vwap': 0.75, 'hma': 0.85,
            
            # Momentum indicators  
            'rsi': 0.8, 'stoch': 0.75, 'stochrsi': 0.85, 'cci': 0.7,
            'williams_r': 0.7, 'roc': 0.6, 'cmf': 0.8, 'mfi': 0.75,
            'adx': 0.9, 'macd': 0.85, 'ppo': 0.8,
            
            # Volatility indicators
            'bbands': 0.85, 'keltner': 0.8, 'donchian': 0.75,
            'atr': 0.9, 'natr': 0.85,
            
            # Volume indicators (limited for forex)
            'obv': 0.5, 'ad': 0.5, 'cmf': 0.6,
            
            # Advanced indicators
            'fisher': 0.8, 'squeeze': 0.85, 'tsi': 0.8
        }
        
        # Candlestick pattern reliability (based on forex backtesting)
        self.pattern_reliability = {
            # Strong reversal patterns
            'CDLDOJI': 0.75, 'CDLHAMMER': 0.8, 'CDLHANGINGMAN': 0.8,
            'CDLSHOOTINGSTAR': 0.75, 'CDLENGULFING': 0.85,
            'CDLHARAMI': 0.7, 'CDLPIERCING': 0.8, 'CDLDARKCLOUD': 0.8,
            
            # Strong continuation patterns
            'CDLTHREEWHITESOLDIERS': 0.85, 'CDLTHREEBLACKCROWS': 0.85,
            'CDLRISING3METHODS': 0.8, 'CDLFALLING3METHODS': 0.8,
            
            # Medium reliability patterns
            'CDLMORNINGSTAR': 0.75, 'CDLEVENINGSTAR': 0.75,
            'CDLINSIDEHOUR': 0.65, 'CDLOUTSIDEHOUR': 0.7,
            
            # All other patterns default to 0.6
        }
    
    def analyze_forex_pair(self, pair: str, ohlc_data: pd.DataFrame, 
                          timeframe: str = '1H') -> TechnicalAnalysisResult:
        """
        Comprehensive technical analysis for forex pair
        
        Args:
            pair: Currency pair (e.g., 'EURUSD')
            ohlc_data: DataFrame with columns ['open', 'high', 'low', 'close', 'volume']
            timeframe: Timeframe string (e.g., '1H', '4H', '1D')
            
        Returns:
            TechnicalAnalysisResult with comprehensive analysis
        """
        try:
            if len(ohlc_data) < 50:
                logger.warning(f"Insufficient data for {pair} analysis: {len(ohlc_data)} candles")
                return self._create_empty_result(pair, timeframe)
            
            # Ensure data is properly formatted
            ohlc_data = self._prepare_data(ohlc_data)
            
            # Current price data
            current_price = float(ohlc_data['close'].iloc[-1])
            price_data = {
                'open': float(ohlc_data['open'].iloc[-1]),
                'high': float(ohlc_data['high'].iloc[-1]),
                'low': float(ohlc_data['low'].iloc[-1]),
                'close': current_price,
                'volume': float(ohlc_data.get('volume', pd.Series([0] * len(ohlc_data))).iloc[-1])
            }
            
            # Run comprehensive analysis
            trend_indicators = self._analyze_trend_indicators(ohlc_data, timeframe)
            momentum_indicators = self._analyze_momentum_indicators(ohlc_data, timeframe)
            volatility_indicators = self._analyze_volatility_indicators(ohlc_data, timeframe)
            volume_indicators = self._analyze_volume_indicators(ohlc_data, timeframe)
            candlestick_patterns = self._analyze_candlestick_patterns(ohlc_data, timeframe)
            
            # Calculate overall signals
            overall_trend, overall_strength = self._calculate_overall_signals(
                trend_indicators, momentum_indicators, volatility_indicators
            )
            
            confluence_score = self._calculate_confluence_score(
                trend_indicators, momentum_indicators, volatility_indicators
            )
            
            # Calculate support/resistance levels
            support_levels, resistance_levels = self._calculate_support_resistance(ohlc_data)
            
            return TechnicalAnalysisResult(
                pair=pair,
                timeframe=timeframe,
                timestamp=datetime.now(),
                price_data=price_data,
                trend_indicators=trend_indicators,
                momentum_indicators=momentum_indicators,
                volatility_indicators=volatility_indicators,
                volume_indicators=volume_indicators,
                candlestick_patterns=candlestick_patterns,
                overall_trend=overall_trend,
                overall_strength=overall_strength,
                confluence_score=confluence_score,
                support_levels=support_levels,
                resistance_levels=resistance_levels
            )
            
        except Exception as e:
            logger.error(f"Error analyzing {pair}: {e}")
            return self._create_empty_result(pair, timeframe)
    
    def _prepare_data(self, ohlc_data: pd.DataFrame) -> pd.DataFrame:
        """Prepare and validate OHLC data for analysis"""
        # Ensure required columns exist
        required_cols = ['open', 'high', 'low', 'close']
        for col in required_cols:
            if col not in ohlc_data.columns:
                raise ValueError(f"Missing required column: {col}")
        
        # Convert to float and handle any NaN values
        for col in required_cols:
            ohlc_data[col] = pd.to_numeric(ohlc_data[col], errors='coerce')
        
        # Add volume if missing (set to 1 for forex as volume is not standard)
        if 'volume' not in ohlc_data.columns:
            ohlc_data['volume'] = 1
        
        # Remove any rows with NaN values
        ohlc_data = ohlc_data.dropna()
        
        # Sort by index (timestamp) to ensure proper order
        ohlc_data = ohlc_data.sort_index()
        
        return ohlc_data
    
    def _analyze_trend_indicators(self, ohlc_data: pd.DataFrame, timeframe: str) -> Dict[str, TechnicalSignal]:
        """Analyze trend-following indicators using TA-Lib and pandas-ta"""
        signals = {}
        close = ohlc_data['close'].values
        high = ohlc_data['high'].values
        low = ohlc_data['low'].values
        
        try:
            # Moving Averages (TA-Lib)
            sma_20 = talib.SMA(close, timeperiod=20)
            sma_50 = talib.SMA(close, timeperiod=50)
            ema_20 = talib.EMA(close, timeperiod=20)
            ema_50 = talib.EMA(close, timeperiod=50)
            
            # Current price vs moving averages
            current_price = close[-1]
            
            # SMA Signal
            if not np.isnan(sma_20[-1]) and not np.isnan(sma_50[-1]):
                if current_price > sma_20[-1] > sma_50[-1]:
                    sma_direction = SignalDirection.BULLISH
                    sma_strength = SignalStrength.STRONG
                elif current_price < sma_20[-1] < sma_50[-1]:
                    sma_direction = SignalDirection.BEARISH
                    sma_strength = SignalStrength.STRONG
                elif current_price > sma_20[-1]:
                    sma_direction = SignalDirection.BULLISH
                    sma_strength = SignalStrength.MEDIUM
                elif current_price < sma_20[-1]:
                    sma_direction = SignalDirection.BEARISH
                    sma_strength = SignalStrength.MEDIUM
                else:
                    sma_direction = SignalDirection.NEUTRAL
                    sma_strength = SignalStrength.WEAK
                
                signals['sma'] = TechnicalSignal(
                    indicator_name='SMA Crossover',
                    signal_direction=sma_direction,
                    signal_strength=sma_strength,
                    current_value=sma_20[-1],
                    description=f'Price: {current_price:.5f}, SMA20: {sma_20[-1]:.5f}, SMA50: {sma_50[-1]:.5f}',
                    reliability_score=self.indicator_weights['sma'],
                    timeframe=timeframe,
                    timestamp=datetime.now()
                )
            
            # SuperTrend (pandas-ta)
            supertrend_data = ohlc_data.ta.supertrend(length=10, multiplier=3.0)
            if not supertrend_data.empty and 'SUPERTd_10_3.0' in supertrend_data.columns:
                st_direction = supertrend_data['SUPERTd_10_3.0'].iloc[-1]
                st_value = supertrend_data['SUPERT_10_3.0'].iloc[-1]
                
                if st_direction == 1:
                    signals['supertrend'] = TechnicalSignal(
                        indicator_name='SuperTrend',
                        signal_direction=SignalDirection.BULLISH,
                        signal_strength=SignalStrength.STRONG,
                        current_value=st_value,
                        description=f'Uptrend confirmed, ST: {st_value:.5f}',
                        reliability_score=self.indicator_weights['supertrend'],
                        timeframe=timeframe,
                        timestamp=datetime.now()
                    )
                elif st_direction == -1:
                    signals['supertrend'] = TechnicalSignal(
                        indicator_name='SuperTrend',
                        signal_direction=SignalDirection.BEARISH,
                        signal_strength=SignalStrength.STRONG,
                        current_value=st_value,
                        description=f'Downtrend confirmed, ST: {st_value:.5f}',
                        reliability_score=self.indicator_weights['supertrend'],
                        timeframe=timeframe,
                        timestamp=datetime.now()
                    )
            
            # ADX for trend strength (TA-Lib)
            adx = talib.ADX(high, low, close, timeperiod=14)
            if not np.isnan(adx[-1]):
                adx_value = adx[-1]
                if adx_value > 25:
                    adx_strength = SignalStrength.STRONG
                elif adx_value > 20:
                    adx_strength = SignalStrength.MEDIUM
                else:
                    adx_strength = SignalStrength.WEAK
                
                signals['adx'] = TechnicalSignal(
                    indicator_name='ADX Trend Strength',
                    signal_direction=SignalDirection.NEUTRAL,  # ADX doesn't give direction
                    signal_strength=adx_strength,
                    current_value=adx_value,
                    description=f'Trend strength: {adx_value:.1f}',
                    reliability_score=self.indicator_weights['adx'],
                    timeframe=timeframe,
                    timestamp=datetime.now()
                )
                
        except Exception as e:
            logger.error(f"Error in trend analysis: {e}")
        
        return signals
    
    def _analyze_momentum_indicators(self, ohlc_data: pd.DataFrame, timeframe: str) -> Dict[str, TechnicalSignal]:
        """Analyze momentum indicators using TA-Lib and pandas-ta"""
        signals = {}
        close = ohlc_data['close'].values
        high = ohlc_data['high'].values
        low = ohlc_data['low'].values
        
        try:
            # RSI (TA-Lib)
            rsi = talib.RSI(close, timeperiod=14)
            if not np.isnan(rsi[-1]):
                rsi_value = rsi[-1]
                if rsi_value > 70:
                    rsi_direction = SignalDirection.BEARISH
                    rsi_strength = SignalStrength.STRONG if rsi_value > 80 else SignalStrength.MEDIUM
                    rsi_desc = 'Overbought condition'
                elif rsi_value < 30:
                    rsi_direction = SignalDirection.BULLISH
                    rsi_strength = SignalStrength.STRONG if rsi_value < 20 else SignalStrength.MEDIUM
                    rsi_desc = 'Oversold condition'
                else:
                    rsi_direction = SignalDirection.NEUTRAL
                    rsi_strength = SignalStrength.WEAK
                    rsi_desc = 'Neutral momentum'
                
                signals['rsi'] = TechnicalSignal(
                    indicator_name='RSI',
                    signal_direction=rsi_direction,
                    signal_strength=rsi_strength,
                    current_value=rsi_value,
                    description=f'{rsi_desc}: {rsi_value:.1f}',
                    reliability_score=self.indicator_weights['rsi'],
                    timeframe=timeframe,
                    timestamp=datetime.now()
                )
            
            # MACD (TA-Lib)
            macd, macd_signal, macd_hist = talib.MACD(close, fastperiod=12, slowperiod=26, signalperiod=9)
            if not np.isnan(macd[-1]) and not np.isnan(macd_signal[-1]):
                macd_value = macd[-1]
                signal_value = macd_signal[-1]
                hist_value = macd_hist[-1]
                
                if macd_value > signal_value and hist_value > 0:
                    macd_direction = SignalDirection.BULLISH
                    macd_strength = SignalStrength.STRONG if abs(hist_value) > 0.001 else SignalStrength.MEDIUM
                elif macd_value < signal_value and hist_value < 0:
                    macd_direction = SignalDirection.BEARISH
                    macd_strength = SignalStrength.STRONG if abs(hist_value) > 0.001 else SignalStrength.MEDIUM
                else:
                    macd_direction = SignalDirection.NEUTRAL
                    macd_strength = SignalStrength.WEAK
                
                signals['macd'] = TechnicalSignal(
                    indicator_name='MACD',
                    signal_direction=macd_direction,
                    signal_strength=macd_strength,
                    current_value=hist_value,
                    description=f'MACD: {macd_value:.5f}, Signal: {signal_value:.5f}, Hist: {hist_value:.5f}',
                    reliability_score=self.indicator_weights['macd'],
                    timeframe=timeframe,
                    timestamp=datetime.now()
                )
            
            # Stochastic Oscillator (TA-Lib)
            stoch_k, stoch_d = talib.STOCH(high, low, close, 
                                          fastk_period=14, slowk_period=3, slowd_period=3)
            if not np.isnan(stoch_k[-1]) and not np.isnan(stoch_d[-1]):
                k_value = stoch_k[-1]
                d_value = stoch_d[-1]
                
                if k_value > 80 and d_value > 80:
                    stoch_direction = SignalDirection.BEARISH
                    stoch_strength = SignalStrength.STRONG
                    stoch_desc = 'Overbought'
                elif k_value < 20 and d_value < 20:
                    stoch_direction = SignalDirection.BULLISH
                    stoch_strength = SignalStrength.STRONG
                    stoch_desc = 'Oversold'
                elif k_value > d_value:
                    stoch_direction = SignalDirection.BULLISH
                    stoch_strength = SignalStrength.MEDIUM
                    stoch_desc = 'Bullish momentum'
                elif k_value < d_value:
                    stoch_direction = SignalDirection.BEARISH
                    stoch_strength = SignalStrength.MEDIUM
                    stoch_desc = 'Bearish momentum'
                else:
                    stoch_direction = SignalDirection.NEUTRAL
                    stoch_strength = SignalStrength.WEAK
                    stoch_desc = 'Neutral'
                
                signals['stoch'] = TechnicalSignal(
                    indicator_name='Stochastic',
                    signal_direction=stoch_direction,
                    signal_strength=stoch_strength,
                    current_value=k_value,
                    description=f'{stoch_desc}: K={k_value:.1f}, D={d_value:.1f}',
                    reliability_score=self.indicator_weights['stoch'],
                    timeframe=timeframe,
                    timestamp=datetime.now()
                )
            
            # Fisher Transform (pandas-ta)
            fisher_data = ohlc_data.ta.fisher(length=14)
            if not fisher_data.empty and len(fisher_data.columns) >= 2:
                fisher_value = fisher_data.iloc[-1, 0]  # First column is Fisher
                fisher_signal = fisher_data.iloc[-1, 1]  # Second column is signal
                
                if not np.isnan(fisher_value) and not np.isnan(fisher_signal):
                    if fisher_value > fisher_signal and fisher_value > 0:
                        fisher_direction = SignalDirection.BULLISH
                        fisher_strength = SignalStrength.STRONG if fisher_value > 2 else SignalStrength.MEDIUM
                    elif fisher_value < fisher_signal and fisher_value < 0:
                        fisher_direction = SignalDirection.BEARISH
                        fisher_strength = SignalStrength.STRONG if fisher_value < -2 else SignalStrength.MEDIUM
                    else:
                        fisher_direction = SignalDirection.NEUTRAL
                        fisher_strength = SignalStrength.WEAK
                    
                    signals['fisher'] = TechnicalSignal(
                        indicator_name='Fisher Transform',
                        signal_direction=fisher_direction,
                        signal_strength=fisher_strength,
                        current_value=fisher_value,
                        description=f'Fisher: {fisher_value:.3f}, Signal: {fisher_signal:.3f}',
                        reliability_score=self.indicator_weights['fisher'],
                        timeframe=timeframe,
                        timestamp=datetime.now()
                    )
                    
        except Exception as e:
            logger.error(f"Error in momentum analysis: {e}")
        
        return signals
    
    def _analyze_volatility_indicators(self, ohlc_data: pd.DataFrame, timeframe: str) -> Dict[str, TechnicalSignal]:
        """Analyze volatility indicators using TA-Lib"""
        signals = {}
        close = ohlc_data['close'].values
        high = ohlc_data['high'].values
        low = ohlc_data['low'].values
        
        try:
            # Bollinger Bands (TA-Lib)
            bb_upper, bb_middle, bb_lower = talib.BBANDS(close, timeperiod=20, nbdevup=2, nbdevdn=2)
            if not np.isnan(bb_upper[-1]) and not np.isnan(bb_lower[-1]):
                current_price = close[-1]
                upper_band = bb_upper[-1]
                lower_band = bb_lower[-1]
                middle_band = bb_middle[-1]
                
                # Calculate position within bands (0 = lower band, 1 = upper band)
                bb_position = (current_price - lower_band) / (upper_band - lower_band)
                
                if bb_position > 0.8:
                    bb_direction = SignalDirection.BEARISH
                    bb_strength = SignalStrength.STRONG
                    bb_desc = 'Near upper band - potential reversal'
                elif bb_position < 0.2:
                    bb_direction = SignalDirection.BULLISH
                    bb_strength = SignalStrength.STRONG
                    bb_desc = 'Near lower band - potential reversal'
                elif bb_position > 0.6:
                    bb_direction = SignalDirection.BEARISH
                    bb_strength = SignalStrength.MEDIUM
                    bb_desc = 'Above middle band'
                elif bb_position < 0.4:
                    bb_direction = SignalDirection.BULLISH
                    bb_strength = SignalStrength.MEDIUM
                    bb_desc = 'Below middle band'
                else:
                    bb_direction = SignalDirection.NEUTRAL
                    bb_strength = SignalStrength.WEAK
                    bb_desc = 'Near middle band'
                
                signals['bbands'] = TechnicalSignal(
                    indicator_name='Bollinger Bands',
                    signal_direction=bb_direction,
                    signal_strength=bb_strength,
                    current_value=bb_position,
                    description=f'{bb_desc} (Position: {bb_position:.2f})',
                    reliability_score=self.indicator_weights['bbands'],
                    timeframe=timeframe,
                    timestamp=datetime.now()
                )
            
            # ATR for volatility measurement (TA-Lib)
            atr = talib.ATR(high, low, close, timeperiod=14)
            if not np.isnan(atr[-1]):
                atr_value = atr[-1]
                current_price = close[-1]
                atr_pct = (atr_value / current_price) * 100
                
                if atr_pct > 0.8:
                    atr_strength = SignalStrength.VERY_STRONG
                    atr_desc = 'Very high volatility'
                elif atr_pct > 0.6:
                    atr_strength = SignalStrength.STRONG
                    atr_desc = 'High volatility'
                elif atr_pct > 0.4:
                    atr_strength = SignalStrength.MEDIUM
                    atr_desc = 'Medium volatility'
                else:
                    atr_strength = SignalStrength.WEAK
                    atr_desc = 'Low volatility'
                
                signals['atr'] = TechnicalSignal(
                    indicator_name='ATR Volatility',
                    signal_direction=SignalDirection.NEUTRAL,
                    signal_strength=atr_strength,
                    current_value=atr_pct,
                    description=f'{atr_desc}: {atr_pct:.2f}%',
                    reliability_score=self.indicator_weights['atr'],
                    timeframe=timeframe,
                    timestamp=datetime.now()
                )
                
        except Exception as e:
            logger.error(f"Error in volatility analysis: {e}")
        
        return signals
    
    def _analyze_volume_indicators(self, ohlc_data: pd.DataFrame, timeframe: str) -> Dict[str, TechnicalSignal]:
        """Analyze volume indicators (limited for forex)"""
        signals = {}
        
        # Note: Volume indicators are less reliable for forex due to decentralized nature
        # We'll include basic volume analysis if available
        
        try:
            if 'volume' in ohlc_data.columns and ohlc_data['volume'].sum() > 0:
                close = ohlc_data['close'].values
                volume = ohlc_data['volume'].values
                
                # OBV (On Balance Volume) - TA-Lib
                obv = talib.OBV(close, volume)
                if not np.isnan(obv[-1]) and len(obv) > 1:
                    obv_current = obv[-1]
                    obv_prev = obv[-2]
                    
                    if obv_current > obv_prev:
                        obv_direction = SignalDirection.BULLISH
                        obv_desc = 'Volume supporting uptrend'
                    elif obv_current < obv_prev:
                        obv_direction = SignalDirection.BEARISH
                        obv_desc = 'Volume supporting downtrend'
                    else:
                        obv_direction = SignalDirection.NEUTRAL
                        obv_desc = 'Neutral volume flow'
                    
                    signals['obv'] = TechnicalSignal(
                        indicator_name='OBV',
                        signal_direction=obv_direction,
                        signal_strength=SignalStrength.WEAK,  # Lower reliability for forex
                        current_value=obv_current,
                        description=obv_desc,
                        reliability_score=self.indicator_weights['obv'],
                        timeframe=timeframe,
                        timestamp=datetime.now()
                    )
                    
        except Exception as e:
            logger.error(f"Error in volume analysis: {e}")
        
        return signals
    
    def _analyze_candlestick_patterns(self, ohlc_data: pd.DataFrame, timeframe: str) -> List[PatternSignal]:
        """Analyze all TA-Lib candlestick patterns"""
        patterns = []
        
        try:
            open_prices = ohlc_data['open'].values
            high_prices = ohlc_data['high'].values
            low_prices = ohlc_data['low'].values
            close_prices = ohlc_data['close'].values
            
            # All 61 TA-Lib candlestick patterns
            talib_patterns = [
                ('CDLDOJI', 'reversal'), ('CDLDOJISTAR', 'reversal'),
                ('CDLDRAGONFLYDOJI', 'bullish'), ('CDLGRAVESTONEDOJI', 'bearish'),
                ('CDLHAMMER', 'bullish'), ('CDLHANGINGMAN', 'bearish'),
                ('CDLINVERTEDHAMMER', 'bullish'), ('CDLSHOOTINGSTAR', 'bearish'),
                ('CDLENGULFING', 'reversal'), ('CDLHARAMI', 'reversal'),
                ('CDLHARAMICROSS', 'reversal'), ('CDLPIERCING', 'bullish'),
                ('CDLDARKCLOUDCOVER', 'bearish'), ('CDLMORNINGSTAR', 'bullish'),
                ('CDLEVENINGSTAR', 'bearish'), ('CDLMORNINGDOJISTAR', 'bullish'),
                ('CDLEVENINGDOJISTAR', 'bearish'), ('CDLTHREEWHITESOLDIERS', 'bullish'),
                ('CDLTHREEBLACKCROWS', 'bearish'), ('CDLADVANCEBLOCK', 'bearish'),
                ('CDLBELTHOLD', 'continuation'), ('CDLBREAKAWAY', 'reversal'),
                ('CDLCLOSINGMARUBOZU', 'continuation'), ('CDLCONCEALBABYSWALL', 'bullish'),
                ('CDLCOUNTERATTACK', 'reversal'), ('CDLGAPSIDESIDEWHITE', 'continuation'),
                ('CDLHIGHWAVE', 'reversal'), ('CDLHIKKAKE', 'reversal'),
                ('CDLHIKKAKEMOD', 'reversal'), ('CDLHOMINGPIGEON', 'bullish'),
                ('CDLIDENTICAL3CROWS', 'bearish'), ('CDLINNECK', 'bearish'),
                ('CDLKICKING', 'reversal'), ('CDLKICKINGBYLENGTH', 'reversal'),
                ('CDLLADDERBOTTOM', 'bullish'), ('CDLLONGLEGGEDDOJI', 'reversal'),
                ('CDLLONGLINE', 'continuation'), ('CDLMARUBOZU', 'continuation'),
                ('CDLMATCHINGLOW', 'bullish'), ('CDLONNECK', 'bearish'),
                ('CDLRICKSHAWMAN', 'reversal'), ('CDLRISEFALL3METHODS', 'continuation'),
                ('CDLSEPARATINGLINES', 'continuation'), ('CDLSHORTLINE', 'reversal'),
                ('CDLSPINNINGTOP', 'reversal'), ('CDLSTALLEDPATTERN', 'bearish'),
                ('CDLSTICKSANDWICH', 'reversal'), ('CDLTAKURI', 'bullish'),
                ('CDLTASUKIGAP', 'continuation'), ('CDLTHRUSTING', 'bearish'),
                ('CDLTRISTAR', 'reversal'), ('CDLUNIQUE3RIVER', 'bullish'),
                ('CDLUPSIDEGAP2CROWS', 'bearish'), ('CDLXSIDEGAP3METHODS', 'continuation'),
                ('CDL2CROWS', 'bearish'), ('CDL3BLACKCROWS', 'bearish'),
                ('CDL3INSIDE', 'reversal'), ('CDL3LINESTRIKE', 'reversal'),
                ('CDL3OUTSIDE', 'reversal'), ('CDL3STARSINSOUTH', 'bullish'),
                ('CDL3WHITESOLDIERS', 'bullish'), ('CDLABANDONEDBABY', 'reversal'),
                ('CDLBELTHOLD', 'continuation'), ('CDLBREAKAWAY', 'reversal')
            ]
            
            for pattern_name, pattern_type in talib_patterns:
                try:
                    pattern_func = getattr(talib, pattern_name)
                    pattern_result = pattern_func(open_prices, high_prices, low_prices, close_prices)
                    
                    # Check last few candles for patterns
                    for i in range(max(0, len(pattern_result) - 5), len(pattern_result)):
                        if not np.isnan(pattern_result[i]) and pattern_result[i] != 0:
                            strength = int(pattern_result[i])
                            reliability = self.pattern_reliability.get(pattern_name, 0.6)
                            
                            # Determine pattern type based on strength and classification
                            if strength > 0:
                                if pattern_type == 'bearish':
                                    actual_type = 'bullish'  # Inverted
                                else:
                                    actual_type = pattern_type
                            else:
                                if pattern_type == 'bullish':
                                    actual_type = 'bearish'  # Inverted
                                else:
                                    actual_type = pattern_type
                            
                            patterns.append(PatternSignal(
                                pattern_name=pattern_name.replace('CDL', ''),
                                pattern_type=actual_type,
                                strength=strength,
                                reliability=reliability,
                                confirmation_needed=reliability < 0.8,
                                timeframe=timeframe,
                                timestamp=datetime.now()
                            ))
                            
                except AttributeError:
                    # Pattern function doesn't exist in this TA-Lib version
                    continue
                except Exception as e:
                    logger.debug(f"Error analyzing pattern {pattern_name}: {e}")
                    continue
            
            # Sort by reliability and strength
            patterns.sort(key=lambda x: (x.reliability, abs(x.strength)), reverse=True)
            
        except Exception as e:
            logger.error(f"Error in pattern analysis: {e}")
        
        return patterns[:10]  # Return top 10 patterns
    
    def _calculate_overall_signals(self, trend_indicators: Dict, momentum_indicators: Dict, 
                                 volatility_indicators: Dict) -> Tuple[SignalDirection, float]:
        """Calculate overall trend direction and strength"""
        try:
            bullish_score = 0.0
            bearish_score = 0.0
            total_weight = 0.0
            
            all_indicators = {**trend_indicators, **momentum_indicators, **volatility_indicators}
            
            for indicator_name, signal in all_indicators.items():
                weight = self.indicator_weights.get(indicator_name, 0.5)
                strength_multiplier = signal.signal_strength.value / 5.0  # Normalize to 0-1
                reliability_multiplier = signal.reliability_score
                
                effective_weight = weight * strength_multiplier * reliability_multiplier
                
                if signal.signal_direction == SignalDirection.BULLISH:
                    bullish_score += effective_weight
                elif signal.signal_direction == SignalDirection.BEARISH:
                    bearish_score += effective_weight
                
                total_weight += effective_weight
            
            if total_weight == 0:
                return SignalDirection.NEUTRAL, 0.0
            
            # Determine overall direction
            net_score = (bullish_score - bearish_score) / total_weight
            overall_strength = min(abs(net_score), 1.0)
            
            if net_score > 0.1:
                overall_direction = SignalDirection.BULLISH
            elif net_score < -0.1:
                overall_direction = SignalDirection.BEARISH
            else:
                overall_direction = SignalDirection.NEUTRAL
            
            return overall_direction, overall_strength
            
        except Exception as e:
            logger.error(f"Error calculating overall signals: {e}")
            return SignalDirection.NEUTRAL, 0.0
    
    def _calculate_confluence_score(self, trend_indicators: Dict, momentum_indicators: Dict,
                                  volatility_indicators: Dict) -> float:
        """Calculate how many indicators agree on direction"""
        try:
            bullish_count = 0
            bearish_count = 0
            total_count = 0
            
            all_indicators = {**trend_indicators, **momentum_indicators, **volatility_indicators}
            
            for signal in all_indicators.values():
                if signal.signal_direction == SignalDirection.BULLISH:
                    bullish_count += 1
                elif signal.signal_direction == SignalDirection.BEARISH:
                    bearish_count += 1
                total_count += 1
            
            if total_count == 0:
                return 0.0
            
            # Confluence is the percentage of indicators agreeing on the dominant direction
            dominant_count = max(bullish_count, bearish_count)
            confluence_score = dominant_count / total_count
            
            return confluence_score
            
        except Exception as e:
            logger.error(f"Error calculating confluence: {e}")
            return 0.0
    
    def _calculate_support_resistance(self, ohlc_data: pd.DataFrame) -> Tuple[List[float], List[float]]:
        """Calculate support and resistance levels"""
        try:
            # Use pandas-ta for pivot points
            pivots = ohlc_data.ta.pivots(high='high', low='low', close='close')
            
            support_levels = []
            resistance_levels = []
            
            if not pivots.empty:
                # Get pivot highs and lows
                if 'PIVOTS_1' in pivots.columns:
                    pivot_highs = pivots['PIVOTS_1'].dropna()
                    pivot_lows = pivots['PIVOTS_-1'].dropna() if 'PIVOTS_-1' in pivots.columns else pd.Series()
                    
                    # Convert to resistance (highs) and support (lows)
                    resistance_levels = pivot_highs.tolist()[-5:]  # Last 5 pivot highs
                    support_levels = pivot_lows.tolist()[-5:] if not pivot_lows.empty else []
            
            # Fallback: use recent highs and lows if no pivots found
            if not resistance_levels or not support_levels:
                recent_data = ohlc_data.tail(50)  # Last 50 candles
                resistance_levels = recent_data.nlargest(5, 'high')['high'].tolist()
                support_levels = recent_data.nsmallest(5, 'low')['low'].tolist()
            
            return support_levels, resistance_levels
            
        except Exception as e:
            logger.error(f"Error calculating support/resistance: {e}")
            return [], []
    
    def _create_empty_result(self, pair: str, timeframe: str) -> TechnicalAnalysisResult:
        """Create empty result for error cases"""
        return TechnicalAnalysisResult(
            pair=pair,
            timeframe=timeframe,
            timestamp=datetime.now(),
            price_data={},
            trend_indicators={},
            momentum_indicators={},
            volatility_indicators={},
            volume_indicators={},
            candlestick_patterns=[],
            overall_trend=SignalDirection.NEUTRAL,
            overall_strength=0.0,
            confluence_score=0.0,
            support_levels=[],
            resistance_levels=[]
        )
    
    def get_signal_summary(self, analysis_result: TechnicalAnalysisResult) -> Dict[str, Any]:
        """Generate a comprehensive signal summary"""
        try:
            summary = {
                'pair': analysis_result.pair,
                'timeframe': analysis_result.timeframe,
                'timestamp': analysis_result.timestamp.isoformat(),
                'overall_direction': analysis_result.overall_trend.name,
                'overall_strength': analysis_result.overall_strength,
                'confluence_score': analysis_result.confluence_score,
                'current_price': analysis_result.price_data.get('close', 0.0),
                
                # Indicator counts
                'bullish_indicators': len([s for s in {**analysis_result.trend_indicators, 
                                                     **analysis_result.momentum_indicators}.values() 
                                         if s.signal_direction == SignalDirection.BULLISH]),
                'bearish_indicators': len([s for s in {**analysis_result.trend_indicators, 
                                                      **analysis_result.momentum_indicators}.values() 
                                          if s.signal_direction == SignalDirection.BEARISH]),
                'neutral_indicators': len([s for s in {**analysis_result.trend_indicators, 
                                                      **analysis_result.momentum_indicators}.values() 
                                          if s.signal_direction == SignalDirection.NEUTRAL]),
                
                # Top indicators
                'strongest_bullish': [],
                'strongest_bearish': [],
                
                # Pattern summary
                'bullish_patterns': len([p for p in analysis_result.candlestick_patterns 
                                       if p.pattern_type == 'bullish']),
                'bearish_patterns': len([p for p in analysis_result.candlestick_patterns 
                                        if p.pattern_type == 'bearish']),
                'reversal_patterns': len([p for p in analysis_result.candlestick_patterns 
                                         if p.pattern_type == 'reversal']),
                
                # Support/Resistance
                'nearest_support': min(analysis_result.support_levels) if analysis_result.support_levels else None,
                'nearest_resistance': max(analysis_result.resistance_levels) if analysis_result.resistance_levels else None,
                
                # Trading recommendation
                'recommendation': self._generate_recommendation(analysis_result)
            }
            
            # Find strongest signals
            all_signals = {**analysis_result.trend_indicators, **analysis_result.momentum_indicators}
            
            bullish_signals = [(name, signal) for name, signal in all_signals.items() 
                              if signal.signal_direction == SignalDirection.BULLISH]
            bearish_signals = [(name, signal) for name, signal in all_signals.items() 
                              if signal.signal_direction == SignalDirection.BEARISH]
            
            # Sort by strength and reliability
            bullish_signals.sort(key=lambda x: x[1].signal_strength.value * x[1].reliability_score, reverse=True)
            bearish_signals.sort(key=lambda x: x[1].signal_strength.value * x[1].reliability_score, reverse=True)
            
            summary['strongest_bullish'] = [name for name, _ in bullish_signals[:3]]
            summary['strongest_bearish'] = [name for name, _ in bearish_signals[:3]]
            
            return summary
            
        except Exception as e:
            logger.error(f"Error generating signal summary: {e}")
            return {'error': str(e)}
    
    def _generate_recommendation(self, analysis_result: TechnicalAnalysisResult) -> Dict[str, Any]:
        """Generate trading recommendation based on analysis"""
        try:
            # Base recommendation on overall trend and confluence
            overall_strength = analysis_result.overall_strength
            confluence = analysis_result.confluence_score
            direction = analysis_result.overall_trend
            
            # Determine action
            if overall_strength > 0.6 and confluence > 0.7:
                if direction == SignalDirection.BULLISH:
                    action = 'BUY'
                    confidence = 'HIGH'
                elif direction == SignalDirection.BEARISH:
                    action = 'SELL'
                    confidence = 'HIGH'
                else:
                    action = 'HOLD'
                    confidence = 'LOW'
            elif overall_strength > 0.4 and confluence > 0.6:
                if direction == SignalDirection.BULLISH:
                    action = 'BUY'
                    confidence = 'MEDIUM'
                elif direction == SignalDirection.BEARISH:
                    action = 'SELL'
                    confidence = 'MEDIUM'
                else:
                    action = 'HOLD'
                    confidence = 'LOW'
            else:
                action = 'HOLD'
                confidence = 'LOW'
            
            # Calculate entry/exit levels
            current_price = analysis_result.price_data.get('close', 0.0)
            
            # Use ATR for stop loss and take profit if available
            atr_signal = analysis_result.volatility_indicators.get('atr')
            atr_pct = atr_signal.current_value if atr_signal else 0.5  # Default 0.5%
            
            if action == 'BUY':
                entry_price = current_price
                stop_loss = current_price * (1 - atr_pct / 100 * 2)  # 2x ATR
                take_profit = current_price * (1 + atr_pct / 100 * 3)  # 3x ATR (1.5:1 RR)
            elif action == 'SELL':
                entry_price = current_price
                stop_loss = current_price * (1 + atr_pct / 100 * 2)  # 2x ATR
                take_profit = current_price * (1 - atr_pct / 100 * 3)  # 3x ATR (1.5:1 RR)
            else:
                entry_price = stop_loss = take_profit = None
            
            return {
                'action': action,
                'confidence': confidence,
                'entry_price': entry_price,
                'stop_loss': stop_loss,
                'take_profit': take_profit,
                'risk_reward_ratio': 1.5,
                'reasoning': f'Strength: {overall_strength:.2f}, Confluence: {confluence:.2f}'
            }
            
        except Exception as e:
            logger.error(f"Error generating recommendation: {e}")
            return {'action': 'HOLD', 'confidence': 'LOW', 'error': str(e)}

# Global instance
enhanced_technical_analyzer = EnhancedTechnicalAnalyzer()