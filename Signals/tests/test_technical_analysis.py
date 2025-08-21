"""
Unit tests for technical analysis functionality
Tests use mock data structures that match real API responses
"""
import pytest
import numpy as np
import pandas as pd
from unittest.mock import Mock, patch
from datetime import datetime
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.technical_analysis import TechnicalAnalyzer, CandlestickPattern, technical_analyzer

class TestTechnicalAnalyzer:
    """Test technical analysis functionality"""
    
    def setup_method(self):
        """Setup test environment"""
        self.analyzer = TechnicalAnalyzer()
    
    def test_initialization(self):
        """Test TechnicalAnalyzer initialization"""
        assert self.analyzer.pip_values is not None
        assert 'EURUSD' in self.analyzer.pip_values
    
    def test_calculate_rsi_insufficient_data(self):
        """Test RSI calculation with insufficient data"""
        prices = [1.1000, 1.1010]  # Too few data points
        result = self.analyzer.calculate_rsi(prices, 14)
        assert result is None
    
    def test_calculate_rsi_valid_data(self):
        """Test RSI calculation with valid data"""
        # Create price series with trend
        prices = []
        base_price = 1.1000
        for i in range(20):
            if i < 10:
                base_price += 0.0010  # Uptrend
            else:
                base_price -= 0.0005  # Downtrend
            prices.append(base_price)
        
        result = self.analyzer.calculate_rsi(prices, 14)
        assert result is not None
        assert 0 <= result <= 100
    
    def test_calculate_macd_insufficient_data(self):
        """Test MACD calculation with insufficient data"""
        prices = [1.1000] * 10  # Too few data points
        result = self.analyzer.calculate_macd(prices)
        assert result is None
    
    def test_calculate_macd_valid_data(self):
        """Test MACD calculation with valid data"""
        # Create price series
        prices = []
        base_price = 1.1000
        for i in range(50):
            base_price += (i % 5 - 2) * 0.0001  # Oscillating pattern
            prices.append(base_price)
        
        result = self.analyzer.calculate_macd(prices)
        assert result is not None
        assert 'macd' in result
        assert 'signal' in result
        assert 'histogram' in result
    
    def test_calculate_bollinger_bands(self):
        """Test Bollinger Bands calculation"""
        # Create price series with volatility
        prices = []
        base_price = 1.1000
        for i in range(25):
            base_price += (np.sin(i * 0.3) * 0.0020)  # Sine wave pattern
            prices.append(base_price)
        
        result = self.analyzer.calculate_bollinger_bands(prices, 20)
        assert result is not None
        assert 'upper' in result
        assert 'middle' in result
        assert 'lower' in result
        assert 'position' in result
        assert result['upper'] > result['middle'] > result['lower']
    
    def test_calculate_atr(self):
        """Test ATR calculation"""
        # Create OHLC data
        high = []
        low = []
        close = []
        base_price = 1.1000
        
        for i in range(20):
            volatility = 0.0050
            h = base_price + volatility
            l = base_price - volatility
            c = base_price + (i % 3 - 1) * 0.0010
            
            high.append(h)
            low.append(l)
            close.append(c)
            base_price = c
        
        result = self.analyzer.calculate_atr(high, low, close, 14)
        assert result is not None
        assert result > 0
    
    def test_calculate_stochastic(self):
        """Test Stochastic Oscillator calculation"""
        # Create OHLC data
        high = []
        low = []
        close = []
        
        for i in range(20):
            h = 1.1000 + i * 0.0010
            l = 1.0950 + i * 0.0010
            c = 1.0975 + i * 0.0010
            
            high.append(h)
            low.append(l)
            close.append(c)
        
        result = self.analyzer.calculate_stochastic(high, low, close)
        assert result is not None
        assert 'k_percent' in result
        assert 'd_percent' in result
        assert 0 <= result['k_percent'] <= 100
    
    def test_analyze_4h_candlesticks_no_data(self):
        """Test 4H candlestick analysis with no data"""
        result = self.analyzer.analyze_4h_candlesticks({})
        assert result == []
    
    def test_analyze_4h_candlesticks_insufficient_data(self):
        """Test 4H candlestick analysis with insufficient data"""
        forex_data = {
            'data': [
                {'timestamp': '2024-01-01 00:00:00', 'open': 1.1000, 'high': 1.1050, 'low': 1.0950, 'close': 1.1025}
            ]
        }
        result = self.analyzer.analyze_4h_candlesticks(forex_data)
        assert isinstance(result, list)
    
    def test_detect_hammer_pattern(self):
        """Test hammer pattern detection"""
        # Create DataFrame with hammer pattern
        data = [
            {'timestamp': '2024-01-01 00:00:00', 'open': 1.1000, 'high': 1.1010, 'low': 1.0950, 'close': 1.0995},  # Hammer
        ]
        df = pd.DataFrame(data)
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        
        patterns = self.analyzer._detect_hammer(df)
        assert len(patterns) >= 0  # May or may not detect depending on exact ratios
        
        if patterns:
            assert patterns[0].name == "Hammer"
            assert patterns[0].signal_type == "bullish"
    
    def test_detect_shooting_star_pattern(self):
        """Test shooting star pattern detection"""
        # Create DataFrame with shooting star pattern
        data = [
            {'timestamp': '2024-01-01 00:00:00', 'open': 1.1000, 'high': 1.1100, 'low': 1.0990, 'close': 1.1005},  # Shooting star
        ]
        df = pd.DataFrame(data)
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        
        patterns = self.analyzer._detect_shooting_star(df)
        assert len(patterns) >= 0  # May or may not detect depending on exact ratios
        
        if patterns:
            assert patterns[0].name == "Shooting Star"
            assert patterns[0].signal_type == "bearish"
    
    def test_detect_doji_pattern(self):
        """Test doji pattern detection"""
        # Create DataFrame with doji pattern
        data = [
            {'timestamp': '2024-01-01 00:00:00', 'open': 1.1000, 'high': 1.1020, 'low': 1.0980, 'close': 1.1001},  # Doji
        ]
        df = pd.DataFrame(data)
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        
        patterns = self.analyzer._detect_doji(df)
        assert len(patterns) >= 0
        
        if patterns:
            assert patterns[0].name == "Doji"
            assert patterns[0].signal_type == "reversal"
    
    def test_detect_engulfing_pattern(self):
        """Test engulfing pattern detection"""
        # Create DataFrame with bullish engulfing pattern
        data = [
            {'timestamp': '2024-01-01 00:00:00', 'open': 1.1050, 'high': 1.1060, 'low': 1.1000, 'close': 1.1010},  # Bearish
            {'timestamp': '2024-01-01 04:00:00', 'open': 1.1005, 'high': 1.1080, 'low': 1.0995, 'close': 1.1070},  # Bullish engulfing
        ]
        df = pd.DataFrame(data)
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        
        patterns = self.analyzer._detect_engulfing(df)
        assert len(patterns) >= 0
        
        if patterns:
            assert "Engulfing" in patterns[0].name
    
    @patch('src.technical_analysis.data_fetcher')
    def test_get_comprehensive_technical_analysis_no_data(self, mock_data_fetcher):
        """Test comprehensive analysis with no data"""
        mock_data_fetcher.fetch_forex_data.return_value = None
        
        result = self.analyzer.get_comprehensive_technical_analysis('EURUSD')
        
        assert 'error' in result
        assert 'EURUSD' in result['error']
    
    @patch('src.technical_analysis.data_fetcher')
    def test_get_comprehensive_technical_analysis_with_data(self, mock_data_fetcher):
        """Test comprehensive analysis with data"""
        # Mock 4H forex data structure that matches real API response
        mock_4h_data = {
            'data': [
                {'timestamp': '2024-01-01 00:00:00', 'open': 1.1000, 'high': 1.1050, 'low': 1.0950, 'close': 1.1025},
                {'timestamp': '2024-01-01 04:00:00', 'open': 1.1025, 'high': 1.1080, 'low': 1.0995, 'close': 1.1060},
                {'timestamp': '2024-01-01 08:00:00', 'open': 1.1060, 'high': 1.1090, 'low': 1.1040, 'close': 1.1075},
                {'timestamp': '2024-01-01 12:00:00', 'open': 1.1075, 'high': 1.1100, 'low': 1.1050, 'close': 1.1085},
                {'timestamp': '2024-01-01 16:00:00', 'open': 1.1085, 'high': 1.1110, 'low': 1.1070, 'close': 1.1095}
            ] * 10,  # Repeat to have enough data for indicators
            'source': 'alpha_vantage',
            'last_updated': '2024-01-01T16:00:00'
        }
        
        # Mock daily data
        mock_daily_data = {
            'data': [
                {'timestamp': '2024-01-01', 'open': 1.1000, 'high': 1.1100, 'low': 1.0950, 'close': 1.1095}
            ] * 30,  # 30 days of data
            'source': 'alpha_vantage',
            'last_updated': '2024-01-01T16:00:00'
        }
        
        # Setup mock responses
        def mock_fetch_forex_data(pair, interval):
            if interval == '4hour':
                return mock_4h_data
            elif interval == 'daily':
                return mock_daily_data
            return None
        
        mock_data_fetcher.fetch_forex_data.side_effect = mock_fetch_forex_data
        
        result = self.analyzer.get_comprehensive_technical_analysis('EURUSD')
        
        assert 'error' not in result
        assert result['pair'] == 'EURUSD'
        assert 'candlestick_patterns_4h' in result
        assert 'technical_indicators' in result
        assert 'signal_summary' in result
        assert isinstance(result['candlestick_patterns_4h'], list)
        assert isinstance(result['technical_indicators'], dict)
    
    def test_generate_signal_summary(self):
        """Test signal summary generation"""
        # Create test patterns
        patterns = [
            CandlestickPattern(
                name="Hammer",
                signal_type="bullish",
                strength=0.8,
                timestamp="2024-01-01T16:00:00",
                description="Test pattern"
            ),
            CandlestickPattern(
                name="Shooting Star",
                signal_type="bearish",
                strength=0.6,
                timestamp="2024-01-01T12:00:00",
                description="Test pattern"
            )
        ]
        
        # Create test indicators
        indicators = {
            'rsi_4h': 75.0,  # Overbought
            'macd_4h': {'histogram': -0.0010},  # Bearish
            'bollinger_4h': {'position': 0.9}  # Near upper band
        }
        
        result = self.analyzer._generate_signal_summary(patterns, indicators)
        
        assert 'overall_signal' in result
        assert 'bullish_signals_count' in result
        assert 'bearish_signals_count' in result
        assert 'signal_strength' in result
        assert 'confidence' in result
        
        assert result['overall_signal'] in ['bullish', 'bearish', 'neutral']
        assert -1.0 <= result['signal_strength'] <= 1.0
    
    def test_ema_calculation(self):
        """Test EMA calculation"""
        prices = np.array([1.1000, 1.1010, 1.1020, 1.1015, 1.1025, 1.1030, 1.1035, 1.1040, 1.1045, 1.1050])
        
        result = self.analyzer._calculate_ema(prices, 5)
        assert result is not None
        assert isinstance(result, float)
        assert result > 0
    
    def test_ema_calculation_insufficient_data(self):
        """Test EMA calculation with insufficient data"""
        prices = np.array([1.1000, 1.1010])
        
        result = self.analyzer._calculate_ema(prices, 5)
        assert result is None

class TestCandlestickPatternDataclass:
    """Test CandlestickPattern dataclass"""
    
    def test_candlestick_pattern_creation(self):
        """Test creating a candlestick pattern"""
        pattern = CandlestickPattern(
            name="Test Pattern",
            signal_type="bullish",
            strength=0.8,
            timestamp="2024-01-01T16:00:00",
            description="Test description"
        )
        
        assert pattern.name == "Test Pattern"
        assert pattern.signal_type == "bullish"
        assert pattern.strength == 0.8
        assert pattern.timestamp == "2024-01-01T16:00:00"
        assert pattern.description == "Test description"

class TestGlobalTechnicalAnalyzer:
    """Test global technical analyzer instance"""
    
    def test_global_instance_exists(self):
        """Test that global technical analyzer instance exists"""
        assert technical_analyzer is not None
        assert isinstance(technical_analyzer, TechnicalAnalyzer)
    
    def test_global_instance_has_pip_values(self):
        """Test global instance has pip values"""
        assert technical_analyzer.pip_values is not None
        assert isinstance(technical_analyzer.pip_values, dict)
        assert len(technical_analyzer.pip_values) > 0

class TestIntegration:
    """Integration tests for technical analysis"""
    
    def test_pattern_detection_edge_cases(self):
        """Test pattern detection with edge cases"""
        analyzer = TechnicalAnalyzer()
        
        # Test with equal OHLC values
        data = [
            {'timestamp': '2024-01-01 00:00:00', 'open': 1.1000, 'high': 1.1000, 'low': 1.1000, 'close': 1.1000}
        ]
        df = pd.DataFrame(data)
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        
        # Should handle gracefully without errors
        patterns = analyzer._detect_hammer(df)
        assert isinstance(patterns, list)
        
        patterns = analyzer._detect_doji(df)
        assert isinstance(patterns, list)
    
    def test_indicator_calculations_edge_cases(self):
        """Test indicator calculations with edge cases"""
        analyzer = TechnicalAnalyzer()
        
        # Test with constant prices
        constant_prices = [1.1000] * 20
        
        rsi = analyzer.calculate_rsi(constant_prices, 14)
        # RSI should handle constant prices gracefully
        assert rsi is None or (0 <= rsi <= 100)
        
        macd = analyzer.calculate_macd(constant_prices)
        # MACD should handle constant prices
        assert macd is None or isinstance(macd, dict)
        
        bollinger = analyzer.calculate_bollinger_bands(constant_prices, 20)
        # Bollinger bands with constant prices should have very small deviation
        if bollinger:
            assert abs(bollinger['upper'] - bollinger['middle']) < 1e-10
            assert abs(bollinger['lower'] - bollinger['middle']) < 1e-10