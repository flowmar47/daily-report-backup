"""
Unit tests for economic analysis functionality
Tests use mock data structures that match real FRED API responses
"""
import pytest
import numpy as np
from unittest.mock import Mock, patch
from datetime import datetime
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.economic_analyzer import (
    EconomicAnalyzer, EconomicIndicatorScore, CurrencyStrength, economic_analyzer
)

class TestEconomicAnalyzer:
    """Test economic analysis functionality"""
    
    def setup_method(self):
        """Setup test environment"""
        self.analyzer = EconomicAnalyzer()
    
    def test_initialization(self):
        """Test EconomicAnalyzer initialization"""
        assert self.analyzer.indicator_weights is not None
        assert self.analyzer.scoring_factors is not None
        assert len(self.analyzer.indicator_weights) > 0
        assert len(self.analyzer.scoring_factors) > 0
    
    def test_score_interest_rate(self):
        """Test interest rate scoring"""
        # High interest rate should score positively
        score_high = self.analyzer._score_interest_rate(5.5, 5.0, 10.0)  # Rising rates
        assert score_high > 0
        
        # Low interest rate should score negatively
        score_low = self.analyzer._score_interest_rate(0.5, 1.0, -50.0)  # Falling rates
        assert score_low < 0
        
        # Score should be within bounds
        assert -1.0 <= score_high <= 1.0
        assert -1.0 <= score_low <= 1.0
    
    def test_score_gdp_growth(self):
        """Test GDP growth scoring"""
        # High GDP growth should score positively
        score_high = self.analyzer._score_gdp_growth(3.5, 3.0, 16.7)
        assert score_high > 0
        
        # Negative GDP growth should score negatively
        score_negative = self.analyzer._score_gdp_growth(-1.0, 0.5, -300.0)
        assert score_negative < 0
        
        # Score should be within bounds
        assert -1.0 <= score_high <= 1.0
        assert -1.0 <= score_negative <= 1.0
    
    def test_score_inflation(self):
        """Test inflation scoring"""
        # Inflation near 2% target should score well
        score_target = self.analyzer._score_inflation(2.1, 2.0, 5.0)
        assert score_target > 0
        
        # Very high inflation should score poorly
        score_high = self.analyzer._score_inflation(8.0, 7.5, 6.7)
        assert score_high < 0
        
        # Score should be within bounds
        assert -1.0 <= score_target <= 1.0
        assert -1.0 <= score_high <= 1.0
    
    def test_score_unemployment(self):
        """Test unemployment scoring"""
        # Low unemployment should score positively
        score_low = self.analyzer._score_unemployment(3.0, 3.5, -14.3)  # Falling unemployment
        assert score_low > 0
        
        # High unemployment should score negatively
        score_high = self.analyzer._score_unemployment(12.0, 11.0, 9.1)  # Rising unemployment
        assert score_high < 0
        
        # Score should be within bounds
        assert -1.0 <= score_low <= 1.0
        assert -1.0 <= score_high <= 1.0
    
    def test_score_generic(self):
        """Test generic indicator scoring"""
        # Positive change should generally score positively
        score_pos = self.analyzer._score_generic(100.0, 95.0, 5.3)
        assert score_pos >= 0
        
        # Large negative change should score negatively
        score_neg = self.analyzer._score_generic(90.0, 100.0, -10.0)
        assert score_neg < 0
        
        # Score should be within bounds
        assert -1.0 <= score_pos <= 1.0
        assert -1.0 <= score_neg <= 1.0
    
    @patch('src.economic_analyzer.data_fetcher')
    def test_analyze_indicator_success(self, mock_data_fetcher):
        """Test successful indicator analysis"""
        # Mock FRED data response
        mock_fred_data = {
            'series_id': 'DFF',
            'data': [
                {'date': '2024-01-01', 'value': 5.25},
                {'date': '2023-12-01', 'value': 5.00}
            ],
            'source': 'fred',
            'last_updated': '2024-01-01T00:00:00'
        }
        mock_data_fetcher.fetch_fred_data.return_value = mock_fred_data
        
        result = self.analyzer._analyze_indicator('DFF', 'USD')
        
        assert result is not None
        assert result.indicator == 'DFF'
        assert result.current_value == 5.25
        assert result.previous_value == 5.00
        assert result.change_percent == 5.0  # (5.25-5.00)/5.00 * 100
        assert -1.0 <= result.score <= 1.0
        assert result.impact_weight > 0
    
    @patch('src.economic_analyzer.data_fetcher')
    def test_analyze_indicator_no_data(self, mock_data_fetcher):
        """Test indicator analysis with no data"""
        mock_data_fetcher.fetch_fred_data.return_value = None
        
        result = self.analyzer._analyze_indicator('INVALID', 'USD')
        
        assert result is None
    
    @patch('src.economic_analyzer.data_fetcher')
    def test_analyze_currency_strength_success(self, mock_data_fetcher):
        """Test successful currency strength analysis"""
        # Mock FRED data for multiple indicators
        def mock_fetch_fred_data(indicator_id):
            fred_responses = {
                'DFF': {
                    'series_id': 'DFF',
                    'data': [
                        {'date': '2024-01-01', 'value': 5.25},
                        {'date': '2023-12-01', 'value': 5.00}
                    ]
                },
                'UNRATE': {
                    'series_id': 'UNRATE',
                    'data': [
                        {'date': '2024-01-01', 'value': 3.8},
                        {'date': '2023-12-01', 'value': 4.1}
                    ]
                },
                'CPIAUCSL': {
                    'series_id': 'CPIAUCSL',
                    'data': [
                        {'date': '2024-01-01', 'value': 2.5},
                        {'date': '2023-12-01', 'value': 2.8}
                    ]
                }
            }
            return fred_responses.get(indicator_id)
        
        mock_data_fetcher.fetch_fred_data.side_effect = mock_fetch_fred_data
        
        result = self.analyzer.analyze_currency_strength('USD')
        
        assert result is not None
        assert result.currency == 'USD'
        assert -1.0 <= result.overall_score <= 1.0
        assert len(result.indicator_scores) > 0
        assert 0.0 <= result.confidence_level <= 1.0
        assert result.interest_rate == 5.25
        assert result.unemployment_rate == 3.8
        assert result.inflation_rate == 2.5
    
    def test_analyze_currency_strength_invalid_currency(self):
        """Test currency strength analysis with invalid currency"""
        result = self.analyzer.analyze_currency_strength('INVALID')
        assert result is None
    
    def test_calculate_overall_score(self):
        """Test overall score calculation"""
        indicator_scores = [
            EconomicIndicatorScore(
                indicator='DFF',
                current_value=5.25,
                previous_value=5.00,
                change_percent=5.0,
                score=0.8,
                impact_weight=0.3,
                last_updated='2024-01-01'
            ),
            EconomicIndicatorScore(
                indicator='UNRATE',
                current_value=3.8,
                previous_value=4.1,
                change_percent=-7.3,
                score=0.6,
                impact_weight=0.2,
                last_updated='2024-01-01'
            )
        ]
        
        overall_score = self.analyzer._calculate_overall_score(indicator_scores)
        
        assert -1.0 <= overall_score <= 1.0
        # Should be weighted average: (0.8*0.3 + 0.6*0.2) / (0.3+0.2) = 0.72
        expected = (0.8 * 0.3 + 0.6 * 0.2) / (0.3 + 0.2)
        assert abs(overall_score - expected) < 0.01
    
    def test_calculate_confidence(self):
        """Test confidence calculation"""
        # Recent data should have high confidence
        recent_scores = [
            EconomicIndicatorScore(
                indicator='DFF',
                current_value=5.25,
                previous_value=5.00,
                change_percent=5.0,
                score=0.8,
                impact_weight=0.3,
                last_updated='2024-01-01'
            )
        ]
        
        confidence = self.analyzer._calculate_confidence(recent_scores)
        assert 0.0 <= confidence <= 1.0
        
        # Empty scores should have zero confidence
        empty_confidence = self.analyzer._calculate_confidence([])
        assert empty_confidence == 0.0
    
    def test_extract_key_metrics(self):
        """Test extraction of key economic metrics"""
        indicator_scores = [
            EconomicIndicatorScore(
                indicator='DFF',
                current_value=5.25,
                previous_value=None,
                change_percent=None,
                score=0.8,
                impact_weight=0.3,
                last_updated='2024-01-01'
            ),
            EconomicIndicatorScore(
                indicator='GDP',
                current_value=2.5,
                previous_value=None,
                change_percent=None,
                score=0.6,
                impact_weight=0.25,
                last_updated='2024-01-01'
            ),
            EconomicIndicatorScore(
                indicator='CPIAUCSL',
                current_value=2.8,
                previous_value=None,
                change_percent=None,
                score=0.4,
                impact_weight=0.25,
                last_updated='2024-01-01'
            ),
            EconomicIndicatorScore(
                indicator='UNRATE',
                current_value=3.8,
                previous_value=None,
                change_percent=None,
                score=0.7,
                impact_weight=0.2,
                last_updated='2024-01-01'
            )
        ]
        
        interest_rate = self.analyzer._extract_interest_rate(indicator_scores)
        gdp_growth = self.analyzer._extract_gdp_growth(indicator_scores)
        inflation_rate = self.analyzer._extract_inflation_rate(indicator_scores)
        unemployment_rate = self.analyzer._extract_unemployment_rate(indicator_scores)
        
        assert interest_rate == 5.25
        assert gdp_growth == 2.5
        assert inflation_rate == 2.8
        assert unemployment_rate == 3.8
    
    @patch('src.economic_analyzer.data_fetcher')
    def test_calculate_currency_differential_success(self, mock_data_fetcher):
        """Test currency differential calculation"""
        # Mock analyzer methods
        with patch.object(self.analyzer, 'analyze_currency_strength') as mock_analyze:
            mock_usd_strength = CurrencyStrength(
                currency='USD',
                overall_score=0.6,
                indicator_scores=[],
                interest_rate=5.25,
                gdp_growth=2.5,
                inflation_rate=2.8,
                unemployment_rate=3.8,
                confidence_level=0.8
            )
            
            mock_eur_strength = CurrencyStrength(
                currency='EUR',
                overall_score=0.2,
                indicator_scores=[],
                interest_rate=3.75,
                gdp_growth=1.8,
                inflation_rate=2.2,
                unemployment_rate=6.5,
                confidence_level=0.7
            )
            
            mock_analyze.side_effect = [mock_usd_strength, mock_eur_strength]
            
            # Mock calendar data
            mock_data_fetcher.fetch_finnhub_economic_calendar.return_value = [
                {
                    'date': '2024-01-01T14:00:00Z',
                    'country': 'US',
                    'event': 'Non-Farm Payrolls',
                    'impact': 'high'
                }
            ]
            
            result = self.analyzer.calculate_currency_differential('USD', 'EUR')
            
            assert 'error' not in result
            assert result['pair'] == 'USDEUR'
            assert result['base_currency'] == 'USD'
            assert result['quote_currency'] == 'EUR'
            assert abs(result['overall_differential'] - 0.4) < 1e-10  # 0.6 - 0.2
            assert abs(result['differentials']['interest_rate'] - 1.5) < 1e-10  # 5.25 - 3.75
            assert abs(result['differentials']['gdp_growth'] - 0.7) < 1e-10  # 2.5 - 1.8
            assert 'calendar_impact' in result
    
    @patch('src.economic_analyzer.data_fetcher')
    def test_calculate_currency_differential_insufficient_data(self, mock_data_fetcher):
        """Test currency differential with insufficient data"""
        with patch.object(self.analyzer, 'analyze_currency_strength') as mock_analyze:
            mock_analyze.return_value = None
            
            result = self.analyzer.calculate_currency_differential('USD', 'EUR')
            
            assert 'error' in result
            assert 'Insufficient economic data' in result['error']
    
    def test_calculate_signal_strength(self):
        """Test signal strength calculation"""
        # Strong positive differentials should give strong positive signal
        signal_strong = self.analyzer._calculate_signal_strength(
            overall_diff=0.6,
            ir_diff=2.0,
            gdp_diff=1.0,
            inf_diff=-0.5,
            unemp_diff=2.0
        )
        assert signal_strong > 0.5
        assert -1.0 <= signal_strong <= 1.0
        
        # Strong negative differentials should give strong negative signal
        signal_weak = self.analyzer._calculate_signal_strength(
            overall_diff=-0.6,
            ir_diff=-2.0,
            gdp_diff=-1.0,
            inf_diff=0.5,
            unemp_diff=-2.0
        )
        assert signal_weak < -0.5
        assert -1.0 <= signal_weak <= 1.0
    
    @patch('src.economic_analyzer.data_fetcher')
    def test_analyze_calendar_impact(self, mock_data_fetcher):
        """Test economic calendar impact analysis"""
        mock_calendar_events = [
            {
                'date': '2024-01-01T14:00:00Z',
                'country': 'US',
                'event': 'Non-Farm Payrolls',
                'impact': 'high'
            },
            {
                'date': '2024-01-01T15:00:00Z',
                'country': 'EU',
                'event': 'GDP Growth',
                'impact': 'high'
            },
            {
                'date': '2024-01-01T16:00:00Z',
                'country': 'JP',
                'event': 'Inflation Data',
                'impact': 'medium'
            }
        ]
        
        mock_data_fetcher.fetch_finnhub_economic_calendar.return_value = mock_calendar_events
        
        result = self.analyzer._analyze_calendar_impact('USD', 'EUR')
        
        assert 'events' in result
        assert 'impact_score' in result
        assert len(result['events']) >= 2  # Should include USD and EUR events
        assert -1.0 <= result['impact_score'] <= 1.0
    
    @patch('src.economic_analyzer.data_fetcher')
    def test_analyze_calendar_impact_no_events(self, mock_data_fetcher):
        """Test calendar impact analysis with no events"""
        mock_data_fetcher.fetch_finnhub_economic_calendar.return_value = None
        
        result = self.analyzer._analyze_calendar_impact('USD', 'EUR')
        
        assert result['events'] == []
        assert result['impact_score'] == 0.0

class TestEconomicIndicatorScore:
    """Test EconomicIndicatorScore dataclass"""
    
    def test_economic_indicator_score_creation(self):
        """Test creating an economic indicator score"""
        score = EconomicIndicatorScore(
            indicator='DFF',
            current_value=5.25,
            previous_value=5.00,
            change_percent=5.0,
            score=0.8,
            impact_weight=0.3,
            last_updated='2024-01-01'
        )
        
        assert score.indicator == 'DFF'
        assert score.current_value == 5.25
        assert score.previous_value == 5.00
        assert score.change_percent == 5.0
        assert score.score == 0.8
        assert score.impact_weight == 0.3
        assert score.last_updated == '2024-01-01'

class TestCurrencyStrength:
    """Test CurrencyStrength dataclass"""
    
    def test_currency_strength_creation(self):
        """Test creating a currency strength assessment"""
        indicator_score = EconomicIndicatorScore(
            indicator='DFF',
            current_value=5.25,
            previous_value=5.00,
            change_percent=5.0,
            score=0.8,
            impact_weight=0.3,
            last_updated='2024-01-01'
        )
        
        strength = CurrencyStrength(
            currency='USD',
            overall_score=0.6,
            indicator_scores=[indicator_score],
            interest_rate=5.25,
            gdp_growth=2.5,
            inflation_rate=2.8,
            unemployment_rate=3.8,
            confidence_level=0.8
        )
        
        assert strength.currency == 'USD'
        assert strength.overall_score == 0.6
        assert len(strength.indicator_scores) == 1
        assert strength.interest_rate == 5.25
        assert strength.gdp_growth == 2.5
        assert strength.inflation_rate == 2.8
        assert strength.unemployment_rate == 3.8
        assert strength.confidence_level == 0.8

class TestGlobalEconomicAnalyzer:
    """Test global economic analyzer instance"""
    
    def test_global_instance_exists(self):
        """Test that global economic analyzer instance exists"""
        assert economic_analyzer is not None
        assert isinstance(economic_analyzer, EconomicAnalyzer)
    
    def test_global_instance_has_weights(self):
        """Test global instance has indicator weights"""
        assert economic_analyzer.indicator_weights is not None
        assert isinstance(economic_analyzer.indicator_weights, dict)
        assert len(economic_analyzer.indicator_weights) > 0
    
    def test_global_instance_has_scoring_factors(self):
        """Test global instance has scoring factors"""
        assert economic_analyzer.scoring_factors is not None
        assert isinstance(economic_analyzer.scoring_factors, dict)
        assert len(economic_analyzer.scoring_factors) > 0

class TestIntegration:
    """Integration tests for economic analysis"""
    
    def test_score_indicator_type_detection(self):
        """Test that indicators are properly categorized and scored"""
        analyzer = EconomicAnalyzer()
        
        # Test interest rate indicator
        ir_score = analyzer._score_indicator('DFF', 5.25, 5.00, 5.0)
        assert -1.0 <= ir_score <= 1.0
        
        # Test GDP indicator
        gdp_score = analyzer._score_indicator('GDP', 2.5, 2.0, 25.0)
        assert -1.0 <= gdp_score <= 1.0
        
        # Test CPI indicator
        cpi_score = analyzer._score_indicator('CPIAUCSL', 2.8, 3.2, -12.5)
        assert -1.0 <= cpi_score <= 1.0
        
        # Test unemployment indicator
        unemp_score = analyzer._score_indicator('UNRATE', 3.8, 4.1, -7.3)
        assert -1.0 <= unemp_score <= 1.0
    
    def test_edge_cases_handling(self):
        """Test handling of edge cases"""
        analyzer = EconomicAnalyzer()
        
        # Test with zero previous value (division by zero protection)
        score = analyzer._score_indicator('DFF', 5.0, 0.0, None)
        assert -1.0 <= score <= 1.0
        
        # Test with None values
        score_none = analyzer._score_indicator('GDP', 2.0, None, None)
        assert -1.0 <= score_none <= 1.0
        
        # Test empty indicator scores list
        overall_score = analyzer._calculate_overall_score([])
        assert overall_score == 0.0