"""
Unit tests for signal generation functionality
Tests use mock data structures that match real analysis results
"""
import pytest
import numpy as np
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.signal_generator import (
    SignalGenerator, SignalComponent, TradingSignal, signal_generator
)

class TestSignalGenerator:
    """Test signal generation functionality"""
    
    def setup_method(self):
        """Setup test environment"""
        self.generator = SignalGenerator()
    
    def test_initialization(self):
        """Test SignalGenerator initialization"""
        assert self.generator.pip_values is not None
        assert self.generator.base_weights is not None
        assert self.generator.signal_thresholds is not None
        assert self.generator.risk_params is not None
        
        # Check weight structure
        assert 'technical' in self.generator.base_weights
        assert 'economic' in self.generator.base_weights
        assert 'sentiment' in self.generator.base_weights
        assert 'geopolitical' in self.generator.base_weights
        assert 'candlestick_4h' in self.generator.base_weights
        
        # Weights should sum to approximately 1.0
        total_weight = sum(self.generator.base_weights.values())
        assert 0.95 <= total_weight <= 1.05
    
    def test_determine_trading_action(self):
        """Test trading action determination"""
        # High confidence, strong signal -> BUY
        action = self.generator._determine_trading_action(0.8, 0.9)
        assert action == 'BUY'
        
        # High confidence, strong negative signal -> SELL
        action = self.generator._determine_trading_action(-0.8, 0.9)
        assert action == 'SELL'
        
        # Low confidence -> HOLD
        action = self.generator._determine_trading_action(0.8, 0.2)
        assert action == 'HOLD'
        
        # Weak signal -> HOLD
        action = self.generator._determine_trading_action(0.1, 0.8)
        assert action == 'HOLD'
    
    def test_calculate_composite_signal(self):
        """Test composite signal calculation"""
        components = {
            'technical': SignalComponent(
                component='technical',
                score=0.8,
                confidence=0.9,
                weight=0.35,
                details={}
            ),
            'economic': SignalComponent(
                component='economic',
                score=0.6,
                confidence=0.7,
                weight=0.25,
                details={}
            ),
            'sentiment': SignalComponent(
                component='sentiment',
                score=-0.2,
                confidence=0.5,
                weight=0.20,
                details={}
            ),
            'geopolitical': SignalComponent(
                component='geopolitical',
                score=0.3,
                confidence=0.6,
                weight=0.10,
                details={}
            )
        }
        
        composite_score, overall_confidence = self.generator._calculate_composite_signal(components)
        
        assert -1.0 <= composite_score <= 1.0
        assert 0.0 <= overall_confidence <= 1.0
        assert composite_score > 0  # Should be positive overall
    
    def test_calculate_composite_signal_empty(self):
        """Test composite signal calculation with empty components"""
        composite_score, overall_confidence = self.generator._calculate_composite_signal({})
        
        assert composite_score == 0.0
        assert overall_confidence == 0.0
    
    def test_calculate_achievement_probability(self):
        """Test achievement probability calculation"""
        # Easy target (50% of AWR)
        prob_easy = self.generator._calculate_achievement_probability(
            target_pips=100, days_remaining=4, confidence=0.8, awr=0.0200, pip_value=0.0001
        )
        assert prob_easy > 0.6
        
        # Difficult target (150% of AWR)
        prob_hard = self.generator._calculate_achievement_probability(
            target_pips=300, days_remaining=2, confidence=0.5, awr=0.0200, pip_value=0.0001
        )
        assert prob_hard < 0.4
        
        # All probabilities should be in valid range
        assert 0.0 <= prob_easy <= 1.0
        assert 0.0 <= prob_hard <= 1.0
    
    def test_get_friday_date(self):
        """Test Friday date calculation"""
        friday_date = self.generator._get_friday_date()
        
        assert isinstance(friday_date, datetime)
        assert friday_date.weekday() == 4  # Friday is 4
        assert friday_date.date() >= datetime.now().date()
    
    def test_create_hold_signal(self):
        """Test hold signal creation"""
        hold_details = self.generator._create_hold_signal('EURUSD', 0.1, 0.2)
        
        assert hold_details['entry_price'] is None
        assert hold_details['exit_price'] is None
        assert hold_details['stop_loss'] is None
        assert hold_details['take_profit'] is None
        assert hold_details['target_pips'] is None
        assert hold_details['achievement_probability'] == 0.0
        assert 'reason' in hold_details
    
    def test_create_error_signal(self):
        """Test error signal creation"""
        error_signal = self.generator._create_error_signal('EURUSD', 'Test error')
        
        assert isinstance(error_signal, TradingSignal)
        assert error_signal.pair == 'EURUSD'
        assert error_signal.action == 'HOLD'
        assert error_signal.confidence == 0.0
        assert error_signal.signal_strength == 0.0
    
    @patch('src.signal_generator.technical_analyzer')
    def test_analyze_technical_signals_success(self, mock_tech_analyzer):
        """Test successful technical signal analysis"""
        mock_tech_analysis = {
            'candlestick_patterns_4h': [
                {
                    'name': 'Hammer',
                    'signal_type': 'bullish',
                    'strength': 0.8,
                    'timestamp': '2024-01-01T16:00:00'
                }
            ],
            'technical_indicators': {
                'rsi_4h': 25.0,  # Oversold
                'macd_4h': {'histogram': 0.001},  # Positive
                'bollinger_4h': {'position': 0.1}  # Near lower band
            },
            'average_weekly_range': 0.0150
        }
        
        mock_tech_analyzer.get_comprehensive_technical_analysis.return_value = mock_tech_analysis
        
        result = self.generator._analyze_technical_signals('EURUSD')
        
        assert isinstance(result, SignalComponent)
        assert result.component == 'technical'
        assert result.score > 0  # Should be bullish
        assert result.confidence > 0
        assert result.weight == self.generator.base_weights['technical']
        assert 'candlestick_score' in result.details
    
    @patch('src.signal_generator.technical_analyzer')
    def test_analyze_technical_signals_error(self, mock_tech_analyzer):
        """Test technical signal analysis with error"""
        mock_tech_analyzer.get_comprehensive_technical_analysis.return_value = {
            'error': 'No data available'
        }
        
        result = self.generator._analyze_technical_signals('EURUSD')
        
        assert result.component == 'technical'
        assert result.score == 0.0
        assert result.confidence == 0.0
        assert 'error' in result.details
    
    @patch('src.signal_generator.economic_analyzer')
    def test_analyze_economic_signals_success(self, mock_econ_analyzer):
        """Test successful economic signal analysis"""
        mock_econ_analysis = {
            'overall_differential': 0.4,
            'signal_strength': 0.6,
            'base_strength': {'confidence': 0.8},
            'quote_strength': {'confidence': 0.7},
            'differentials': {
                'interest_rate': 1.5,
                'gdp_growth': 0.7,
                'inflation': -0.3
            },
            'calendar_impact': {
                'impact_score': 0.3,
                'events': [{'event': 'NFP', 'impact': 'high'}]
            }
        }
        
        mock_econ_analyzer.calculate_currency_differential.return_value = mock_econ_analysis
        
        result = self.generator._analyze_economic_signals('EURUSD')
        
        assert isinstance(result, SignalComponent)
        assert result.component == 'economic'
        assert result.score == 0.6  # signal_strength
        assert result.confidence > 0.7  # Average of base/quote confidence
        assert 'interest_rate_diff' in result.details
    
    @patch('src.signal_generator.sentiment_analyzer')
    def test_analyze_sentiment_signals_success(self, mock_sentiment_analyzer):
        """Test successful sentiment signal analysis"""
        mock_sentiment = Mock()
        mock_sentiment.overall_sentiment = 0.5
        mock_sentiment.confidence_level = 0.7
        mock_sentiment.market_mood = 'bullish'
        mock_sentiment.strength = 'moderate'
        mock_sentiment.sentiment_sources = [Mock(), Mock()]  # 2 sources
        
        mock_sentiment_analyzer.analyze_pair_sentiment.return_value = mock_sentiment
        
        result = self.generator._analyze_sentiment_signals('EURUSD')
        
        assert isinstance(result, SignalComponent)
        assert result.component == 'sentiment'
        assert result.score > 0  # Should be positive
        assert result.confidence == 0.7
        assert result.details['market_mood'] == 'bullish'
        assert result.details['source_count'] == 2
    
    @patch('src.signal_generator.data_fetcher')
    def test_analyze_geopolitical_signals_success(self, mock_data_fetcher):
        """Test successful geopolitical signal analysis"""
        mock_events = [
            {
                'title': 'Economic policy announcement',
                'relevance': 'high',
                'tone': 5.0  # Positive tone
            },
            {
                'title': 'Trade agreement signed',
                'relevance': 'medium',
                'tone': 3.0
            }
        ]
        
        mock_data_fetcher.fetch_gdelt_events.return_value = mock_events
        
        result = self.generator._analyze_geopolitical_signals('EURUSD')
        
        assert isinstance(result, SignalComponent)
        assert result.component == 'geopolitical'
        assert result.score > 0  # Should be positive due to positive tones
        assert result.confidence > 0
        assert result.details['events_analyzed'] == 2
        assert result.details['high_impact_events'] == 1
    
    @patch('src.signal_generator.data_fetcher')
    def test_analyze_geopolitical_signals_no_events(self, mock_data_fetcher):
        """Test geopolitical signal analysis with no events"""
        mock_data_fetcher.fetch_gdelt_events.return_value = None
        
        result = self.generator._analyze_geopolitical_signals('EURUSD')
        
        assert result.component == 'geopolitical'
        assert result.score == 0.0
        assert result.confidence == 0.0
        assert result.details['events'] == []
    
    @patch('src.signal_generator.data_fetcher')
    def test_calculate_weekly_targets_buy(self, mock_data_fetcher):
        """Test weekly targets calculation for BUY signal"""
        mock_data_fetcher.get_current_price.return_value = 1.1050
        
        # Mock technical analysis with AWR
        with patch('src.signal_generator.technical_analyzer') as mock_tech:
            mock_tech.get_comprehensive_technical_analysis.return_value = {
                'average_weekly_range': 0.0150
            }
            
            targets = self.generator._calculate_weekly_targets('EURUSD', 'BUY', 0.7, 0.8)
            
            assert targets['entry_price'] == 1.1050
            assert targets['exit_price'] > targets['entry_price']  # Higher for BUY
            assert targets['stop_loss'] < targets['entry_price']   # Lower for BUY
            assert targets['target_pips'] >= 100  # Minimum target
            assert 0.0 <= targets['achievement_probability'] <= 1.0
    
    @patch('src.signal_generator.data_fetcher')
    def test_calculate_weekly_targets_sell(self, mock_data_fetcher):
        """Test weekly targets calculation for SELL signal"""
        mock_data_fetcher.get_current_price.return_value = 1.1050
        
        with patch('src.signal_generator.technical_analyzer') as mock_tech:
            mock_tech.get_comprehensive_technical_analysis.return_value = {
                'average_weekly_range': 0.0150
            }
            
            targets = self.generator._calculate_weekly_targets('EURUSD', 'SELL', -0.7, 0.8)
            
            assert targets['entry_price'] == 1.1050
            assert targets['exit_price'] < targets['entry_price']  # Lower for SELL
            assert targets['stop_loss'] > targets['entry_price']   # Higher for SELL
            assert targets['target_pips'] >= 100
    
    @patch('src.signal_generator.data_fetcher')
    def test_calculate_weekly_targets_no_price(self, mock_data_fetcher):
        """Test weekly targets calculation with no current price"""
        mock_data_fetcher.get_current_price.return_value = None
        
        targets = self.generator._calculate_weekly_targets('EURUSD', 'BUY', 0.7, 0.8)
        
        assert targets['entry_price'] is None
        assert targets['exit_price'] is None
        assert targets['stop_loss'] is None
    
    @patch('src.signal_generator.technical_analyzer')
    @patch('src.signal_generator.economic_analyzer')
    @patch('src.signal_generator.sentiment_analyzer')
    @patch('src.signal_generator.data_fetcher')
    def test_generate_weekly_signal_comprehensive(self, mock_data_fetcher, mock_sentiment, 
                                                 mock_economic, mock_technical):
        """Test comprehensive weekly signal generation"""
        # Mock all analysis components
        mock_technical.get_comprehensive_technical_analysis.return_value = {
            'candlestick_patterns_4h': [
                {'name': 'Hammer', 'signal_type': 'bullish', 'strength': 0.8}
            ],
            'technical_indicators': {'rsi_4h': 25.0},
            'average_weekly_range': 0.0150
        }
        
        mock_economic.calculate_currency_differential.return_value = {
            'signal_strength': 0.6,
            'base_strength': {'confidence': 0.8},
            'quote_strength': {'confidence': 0.7},
            'differentials': {'interest_rate': 1.5},
            'calendar_impact': {'impact_score': 0.0, 'events': []}
        }
        
        mock_sentiment_result = Mock()
        mock_sentiment_result.overall_sentiment = 0.4
        mock_sentiment_result.confidence_level = 0.6
        mock_sentiment_result.market_mood = 'bullish'
        mock_sentiment_result.strength = 'moderate'
        mock_sentiment_result.sentiment_sources = []
        mock_sentiment.analyze_pair_sentiment.return_value = mock_sentiment_result
        
        mock_data_fetcher.fetch_gdelt_events.return_value = []
        mock_data_fetcher.get_current_price.return_value = 1.1050
        
        result = self.generator.generate_weekly_signal('EURUSD')
        
        assert isinstance(result, TradingSignal)
        assert result.pair == 'EURUSD'
        assert result.action in ['BUY', 'SELL', 'HOLD']
        assert 0.0 <= result.confidence <= 1.0
        assert -1.0 <= result.signal_strength <= 1.0
        assert len(result.components) == 4  # All components analyzed
        
        # Check component structure
        for component_name in ['technical', 'economic', 'sentiment', 'geopolitical']:
            assert component_name in result.components
            component = result.components[component_name]
            assert isinstance(component, SignalComponent)
    
    def test_generate_signals_for_pairs(self):
        """Test signal generation for multiple pairs"""
        pairs = ['EURUSD', 'GBPUSD']
        
        with patch.object(self.generator, 'generate_weekly_signal') as mock_generate:
            mock_signal = Mock()
            mock_signal.action = 'BUY'
            mock_generate.return_value = mock_signal
            
            results = self.generator.generate_signals_for_pairs(pairs)
            
            assert len(results) == len(pairs)
            for pair in pairs:
                assert pair in results
                assert results[pair] == mock_signal
            
            assert mock_generate.call_count == len(pairs)

class TestSignalComponent:
    """Test SignalComponent dataclass"""
    
    def test_signal_component_creation(self):
        """Test creating a signal component"""
        component = SignalComponent(
            component='technical',
            score=0.7,
            confidence=0.8,
            weight=0.35,
            details={'test': 'data'}
        )
        
        assert component.component == 'technical'
        assert component.score == 0.7
        assert component.confidence == 0.8
        assert component.weight == 0.35
        assert component.details == {'test': 'data'}

class TestTradingSignal:
    """Test TradingSignal dataclass"""
    
    def test_trading_signal_creation(self):
        """Test creating a trading signal"""
        signal_component = SignalComponent(
            component='technical',
            score=0.7,
            confidence=0.8,
            weight=0.35,
            details={}
        )
        
        signal = TradingSignal(
            pair='EURUSD',
            action='BUY',
            entry_price=1.1050,
            exit_price=1.1200,
            stop_loss=1.0900,
            take_profit=1.1200,
            target_pips=150.0,
            confidence=0.8,
            signal_strength=0.7,
            days_to_target=4,
            weekly_achievement_probability=0.75,
            components={'technical': signal_component},
            analysis_timestamp='2024-01-01T00:00:00',
            expiry_date='2024-01-05T00:00:00'
        )
        
        assert signal.pair == 'EURUSD'
        assert signal.action == 'BUY'
        assert signal.entry_price == 1.1050
        assert signal.target_pips == 150.0
        assert signal.confidence == 0.8
        assert len(signal.components) == 1

class TestGlobalSignalGenerator:
    """Test global signal generator instance"""
    
    def test_global_instance_exists(self):
        """Test that global signal generator instance exists"""
        assert signal_generator is not None
        assert isinstance(signal_generator, SignalGenerator)
    
    def test_global_instance_has_weights(self):
        """Test global instance has proper weights"""
        assert signal_generator.base_weights is not None
        assert signal_generator.signal_thresholds is not None
        assert signal_generator.risk_params is not None

class TestIntegration:
    """Integration tests for signal generation"""
    
    def test_weight_consistency(self):
        """Test that all weights are consistent and valid"""
        generator = SignalGenerator()
        
        # All weights should be positive
        for weight in generator.base_weights.values():
            assert weight > 0
        
        # Weights should sum to approximately 1.0
        total_weight = sum(generator.base_weights.values())
        assert 0.95 <= total_weight <= 1.05
    
    def test_threshold_ordering(self):
        """Test that signal thresholds are properly ordered"""
        generator = SignalGenerator()
        thresholds = generator.signal_thresholds
        
        assert thresholds['strong'] > thresholds['medium']
        assert thresholds['medium'] > thresholds['weak']
        assert thresholds['weak'] > 0
    
    def test_risk_parameters_validity(self):
        """Test that risk parameters are valid"""
        generator = SignalGenerator()
        risk_params = generator.risk_params
        
        assert risk_params['max_stop_loss_pips'] > 0
        assert risk_params['min_target_pips'] > 0
        assert risk_params['risk_reward_ratio'] > 1.0  # Should be greater than 1
    
    def test_pip_values_availability(self):
        """Test that pip values are available for all supported pairs"""
        generator = SignalGenerator()
        
        # Should have pip values for standard pairs
        standard_pairs = ['EURUSD', 'GBPUSD', 'USDJPY', 'USDCAD', 'USDCHF']
        for pair in standard_pairs:
            if pair in generator.pip_values:
                assert generator.pip_values[pair] > 0
    
    def test_signal_bounds_enforcement(self):
        """Test that all scores stay within valid bounds"""
        generator = SignalGenerator()
        
        # Test various score combinations
        test_components = {
            'technical': SignalComponent('technical', 1.5, 0.8, 0.35, {}),  # Invalid score > 1
            'economic': SignalComponent('economic', -1.5, 0.7, 0.25, {}),  # Invalid score < -1
            'sentiment': SignalComponent('sentiment', 0.5, 1.2, 0.20, {}),  # Invalid confidence > 1
            'geopolitical': SignalComponent('geopolitical', 0.3, -0.1, 0.10, {})  # Invalid confidence < 0
        }
        
        # Should handle invalid inputs gracefully
        try:
            composite_score, overall_confidence = generator._calculate_composite_signal(test_components)
            assert -1.0 <= composite_score <= 1.0
            assert 0.0 <= overall_confidence <= 1.0
        except Exception as e:
            # Should not raise exceptions for invalid bounds
            pytest.fail(f"Signal calculation should handle invalid bounds gracefully: {e}")