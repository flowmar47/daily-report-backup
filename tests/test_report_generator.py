"""
Unit tests for report generation functionality
Tests use mock data structures that match real signal generation results
"""
import pytest
import json
import os
import tempfile
from unittest.mock import Mock, patch
from datetime import datetime
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.report_generator import (
    ReportGenerator, SignalReport, report_generator
)
from src.signal_generator import TradingSignal, SignalComponent

class TestReportGenerator:
    """Test report generation functionality"""
    
    def setup_method(self):
        """Setup test environment"""
        self.generator = ReportGenerator()
    
    def test_initialization(self):
        """Test ReportGenerator initialization"""
        assert self.generator.risk_disclaimer is not None
        assert len(self.generator.risk_disclaimer) > 0
        assert isinstance(self.generator.decimal_precision, dict)
        assert 'EURUSD' in self.generator.decimal_precision
        assert 'USDJPY' in self.generator.decimal_precision
    
    def test_format_price(self):
        """Test price formatting with appropriate decimal places"""
        # EUR/USD should have 5 decimal places
        price_eur = self.generator._format_price('EURUSD', 1.10505)
        assert price_eur == '1.10505'
        
        # USD/JPY should have 3 decimal places
        price_jpy = self.generator._format_price('USDJPY', 150.123456)
        assert price_jpy == '150.123'
        
        # None price should return N/A
        price_none = self.generator._format_price('EURUSD', None)
        assert price_none == 'N/A'
        
        # Unknown pair should default to 5 decimal places
        price_unknown = self.generator._format_price('UNKNOWN', 1.23456789)
        assert price_unknown == '1.23457'
    
    def test_format_datetime(self):
        """Test datetime formatting"""
        iso_string = '2024-01-01T12:00:00'
        formatted = self.generator._format_datetime(iso_string)
        assert '2024-01-01' in formatted
        assert 'UTC' in formatted
        
        # Test with invalid format
        invalid_formatted = self.generator._format_datetime('invalid')
        assert invalid_formatted == 'invalid'
    
    def test_get_score_indicator(self):
        """Test score indicator generation"""
        # Strong positive
        indicator_strong = self.generator._get_score_indicator(0.8)
        assert 'Strong' in indicator_strong
        assert '📈' in indicator_strong
        
        # Moderate positive
        indicator_moderate = self.generator._get_score_indicator(0.2)
        assert 'Moderate' in indicator_moderate
        
        # Neutral
        indicator_neutral = self.generator._get_score_indicator(0.0)
        assert 'Neutral' in indicator_neutral
        
        # Weak negative
        indicator_weak = self.generator._get_score_indicator(-0.2)
        assert 'Weak' in indicator_weak
        
        # Very weak
        indicator_very_weak = self.generator._get_score_indicator(-0.5)
        assert 'Very Weak' in indicator_very_weak
    
    def test_generate_report_id(self):
        """Test report ID generation"""
        import time
        report_id = self.generator._generate_report_id()
        assert report_id.startswith('FSR_')
        assert len(report_id) > 10
        
        # Multiple calls should generate different IDs
        time.sleep(0.001)  # Small delay to ensure different timestamps
        report_id2 = self.generator._generate_report_id()
        assert report_id != report_id2
    
    def test_get_next_friday(self):
        """Test next Friday calculation"""
        friday = self.generator._get_next_friday()
        assert friday.weekday() == 4  # Friday is 4
        assert friday.date() >= datetime.now().date()
    
    def test_create_market_overview(self):
        """Test market overview creation"""
        # Create test signals
        signals = {
            'EURUSD': TradingSignal(
                pair='EURUSD',
                action='BUY',
                entry_price=1.1050,
                exit_price=1.1200,
                stop_loss=1.0900,
                take_profit=1.1200,
                target_pips=150.0,
                confidence=0.8,
                signal_strength=0.6,
                days_to_target=4,
                weekly_achievement_probability=0.75,
                components={},
                analysis_timestamp='2024-01-01T00:00:00',
                expiry_date='2024-01-05T00:00:00'
            ),
            'GBPUSD': TradingSignal(
                pair='GBPUSD',
                action='SELL',
                entry_price=1.2500,
                exit_price=1.2350,
                stop_loss=1.2650,
                take_profit=1.2350,
                target_pips=150.0,
                confidence=0.6,
                signal_strength=-0.4,
                days_to_target=4,
                weekly_achievement_probability=0.65,
                components={},
                analysis_timestamp='2024-01-01T00:00:00',
                expiry_date='2024-01-05T00:00:00'
            ),
            'USDCAD': TradingSignal(
                pair='USDCAD',
                action='HOLD',
                entry_price=None,
                exit_price=None,
                stop_loss=None,
                take_profit=None,
                target_pips=None,
                confidence=0.2,
                signal_strength=0.1,
                days_to_target=None,
                weekly_achievement_probability=0.0,
                components={},
                analysis_timestamp='2024-01-01T00:00:00',
                expiry_date='2024-01-05T00:00:00'
            )
        }
        
        overview = self.generator._create_market_overview(signals)
        
        assert overview['total_pairs'] == 3
        assert overview['active_signals'] == 2  # BUY and SELL
        assert overview['hold_signals'] == 1    # HOLD
        assert 0.0 <= overview['avg_confidence'] <= 1.0
        assert overview['market_sentiment'] in ['bullish', 'bearish', 'neutral']
    
    def test_create_signal_components(self):
        """Test signal with components for detailed testing"""
        technical_component = SignalComponent(
            component='technical',
            score=0.7,
            confidence=0.8,
            weight=0.35,
            details={'candlestick_score': 0.6, 'indicator_score': 0.5}
        )
        
        economic_component = SignalComponent(
            component='economic',
            score=0.4,
            confidence=0.7,
            weight=0.25,
            details={'interest_rate_diff': 1.5}
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
            signal_strength=0.6,
            days_to_target=4,
            weekly_achievement_probability=0.75,
            components={
                'technical': technical_component,
                'economic': economic_component
            },
            analysis_timestamp='2024-01-01T00:00:00',
            expiry_date='2024-01-05T00:00:00'
        )
        
        return {'EURUSD': signal}
    
    def test_format_text_report(self):
        """Test text report formatting"""
        signals = self.test_create_signal_components()
        overview = self.generator._create_market_overview(signals)
        
        report = SignalReport(
            report_id='TEST_001',
            generation_timestamp='2024-01-01T00:00:00',
            signals=signals,
            market_overview=overview,
            risk_disclaimer=self.generator.risk_disclaimer,
            expiry_timestamp='2024-01-05T00:00:00'
        )
        
        text_report = self.generator._format_text_report(report)
        
        assert 'FOREX TRADING SIGNALS REPORT' in text_report
        assert 'TEST_001' in text_report
        assert 'EURUSD' in text_report
        assert 'BUY' in text_report
        assert '1.10500' in text_report  # Entry price
        assert '1.12000' in text_report  # Exit price
        assert 'RISK DISCLAIMER' in text_report
        assert 'Technical' in text_report
        assert 'Economic' in text_report
    
    def test_format_json_report(self):
        """Test JSON report formatting"""
        signals = self.test_create_signal_components()
        overview = self.generator._create_market_overview(signals)
        
        report = SignalReport(
            report_id='TEST_001',
            generation_timestamp='2024-01-01T00:00:00',
            signals=signals,
            market_overview=overview,
            risk_disclaimer=self.generator.risk_disclaimer,
            expiry_timestamp='2024-01-05T00:00:00'
        )
        
        json_report = self.generator._format_json_report(report)
        
        # Should be valid JSON
        parsed_json = json.loads(json_report)
        
        assert parsed_json['report_id'] == 'TEST_001'
        assert 'EURUSD' in parsed_json['signals']
        assert parsed_json['signals']['EURUSD']['action'] == 'BUY'
        assert parsed_json['signals']['EURUSD']['entry_price'] == 1.1050
        assert 'market_overview' in parsed_json
        assert 'risk_disclaimer' in parsed_json
    
    def test_format_csv_report(self):
        """Test CSV report formatting"""
        signals = self.test_create_signal_components()
        overview = self.generator._create_market_overview(signals)
        
        report = SignalReport(
            report_id='TEST_001',
            generation_timestamp='2024-01-01T00:00:00',
            signals=signals,
            market_overview=overview,
            risk_disclaimer=self.generator.risk_disclaimer,
            expiry_timestamp='2024-01-05T00:00:00'
        )
        
        csv_report = self.generator._format_csv_report(report)
        
        lines = csv_report.split('\n')
        
        # Check header
        header = lines[0]
        assert 'Pair' in header
        assert 'Action' in header
        assert 'Entry_Price' in header
        assert 'Confidence' in header
        
        # Check data row
        data_row = lines[1]
        assert 'EURUSD' in data_row
        assert 'BUY' in data_row
        assert '1.105' in data_row
    
    def test_format_html_report(self):
        """Test HTML report formatting"""
        signals = self.test_create_signal_components()
        overview = self.generator._create_market_overview(signals)
        
        report = SignalReport(
            report_id='TEST_001',
            generation_timestamp='2024-01-01T00:00:00',
            signals=signals,
            market_overview=overview,
            risk_disclaimer=self.generator.risk_disclaimer,
            expiry_timestamp='2024-01-05T00:00:00'
        )
        
        html_report = self.generator._format_html_report(report)
        
        assert '<!DOCTYPE html>' in html_report
        assert '<title>Forex Trading Signals Report</title>' in html_report
        assert 'TEST_001' in html_report
        assert 'EURUSD' in html_report
        assert 'BUY' in html_report
        assert '1.10500' in html_report
        assert 'Risk Disclaimer' in html_report
    
    def test_generate_comprehensive_report_text(self):
        """Test comprehensive report generation in text format"""
        signals = self.test_create_signal_components()
        
        report = self.generator.generate_comprehensive_report(signals, 'txt')
        
        assert isinstance(report, str)
        assert 'FOREX TRADING SIGNALS REPORT' in report
        assert 'EURUSD' in report
        assert 'BUY' in report
        assert 'RISK DISCLAIMER' in report
    
    def test_generate_comprehensive_report_json(self):
        """Test comprehensive report generation in JSON format"""
        signals = self.test_create_signal_components()
        
        report = self.generator.generate_comprehensive_report(signals, 'json')
        
        # Should be valid JSON
        parsed_json = json.loads(report)
        assert 'report_id' in parsed_json
        assert 'signals' in parsed_json
        assert 'EURUSD' in parsed_json['signals']
    
    def test_generate_comprehensive_report_csv(self):
        """Test comprehensive report generation in CSV format"""
        signals = self.test_create_signal_components()
        
        report = self.generator.generate_comprehensive_report(signals, 'csv')
        
        lines = report.split('\n')
        assert len(lines) >= 2  # Header + at least one data row
        assert 'Pair' in lines[0]
        assert 'EURUSD' in lines[1]
    
    def test_generate_comprehensive_report_html(self):
        """Test comprehensive report generation in HTML format"""
        signals = self.test_create_signal_components()
        
        report = self.generator.generate_comprehensive_report(signals, 'html')
        
        assert '<!DOCTYPE html>' in report
        assert 'EURUSD' in report
        assert 'BUY' in report
    
    def test_generate_comprehensive_report_invalid_format(self):
        """Test report generation with invalid format"""
        signals = self.test_create_signal_components()
        
        report = self.generator.generate_comprehensive_report(signals, 'invalid')
        
        assert 'ERROR GENERATING' in report
        assert 'Unsupported output format' in report
    
    def test_save_report(self):
        """Test saving report to file"""
        with tempfile.TemporaryDirectory() as temp_dir:
            report_content = "Test forex report content"
            
            filepath = self.generator.save_report(
                report_content, 'txt', temp_dir
            )
            
            assert os.path.exists(filepath)
            assert filepath.endswith('.txt')
            
            # Check file content
            with open(filepath, 'r') as f:
                content = f.read()
            assert content == report_content
    
    def test_format_signal_text_buy(self):
        """Test individual signal text formatting for BUY signal"""
        signal = TradingSignal(
            pair='EURUSD',
            action='BUY',
            entry_price=1.1050,
            exit_price=1.1200,
            stop_loss=1.0900,
            take_profit=1.1200,
            target_pips=150.0,
            confidence=0.8,
            signal_strength=0.6,
            days_to_target=4,
            weekly_achievement_probability=0.75,
            components={
                'technical': SignalComponent('technical', 0.7, 0.8, 0.35, {}),
                'economic': SignalComponent('economic', 0.4, 0.7, 0.25, {})
            },
            analysis_timestamp='2024-01-01T00:00:00',
            expiry_date='2024-01-05T00:00:00'
        )
        
        formatted_lines = self.generator._format_signal_text('EURUSD', signal)
        formatted_text = '\n'.join(formatted_lines)
        
        assert 'EURUSD - BUY' in formatted_text
        assert '📈' in formatted_text
        assert 'Entry Price:' in formatted_text
        assert '1.10500' in formatted_text
        assert 'Exit Target:' in formatted_text
        assert '1.12000' in formatted_text
        assert 'Stop Loss:' in formatted_text
        assert 'RISK/REWARD ANALYSIS:' in formatted_text
        assert 'Technical' in formatted_text
        assert 'Economic' in formatted_text
    
    def test_format_signal_text_hold(self):
        """Test individual signal text formatting for HOLD signal"""
        signal = TradingSignal(
            pair='USDCAD',
            action='HOLD',
            entry_price=None,
            exit_price=None,
            stop_loss=None,
            take_profit=None,
            target_pips=None,
            confidence=0.2,
            signal_strength=0.1,
            days_to_target=None,
            weekly_achievement_probability=0.0,
            components={
                'technical': SignalComponent('technical', 0.1, 0.3, 0.35, {'reason': 'Weak signal'})
            },
            analysis_timestamp='2024-01-01T00:00:00',
            expiry_date='2024-01-05T00:00:00'
        )
        
        formatted_lines = self.generator._format_signal_text('USDCAD', signal)
        formatted_text = '\n'.join(formatted_lines)
        
        assert 'USDCAD - HOLD' in formatted_text
        assert '⏸️' in formatted_text
        assert 'HOLD RECOMMENDATION:' in formatted_text
        assert 'signal too weak' in formatted_text.lower()
    
    def test_get_pip_value(self):
        """Test pip value retrieval"""
        # Should use config pip values
        pip_value_eur = self.generator._get_pip_value('EURUSD')
        assert pip_value_eur > 0
        
        # Unknown pair should default to 0.0001
        pip_value_unknown = self.generator._get_pip_value('UNKNOWN')
        assert pip_value_unknown == 0.0001
    
    def test_create_error_report(self):
        """Test error report creation"""
        error_msg = "Test error message"
        error_report = self.generator._create_error_report(error_msg)
        
        assert 'ERROR GENERATING' in error_report
        assert 'Test error message' in error_report
        assert datetime.now().strftime('%Y-%m-%d') in error_report

class TestSignalReport:
    """Test SignalReport dataclass"""
    
    def test_signal_report_creation(self):
        """Test creating a signal report"""
        signal = TradingSignal(
            pair='EURUSD',
            action='BUY',
            entry_price=1.1050,
            exit_price=1.1200,
            stop_loss=1.0900,
            take_profit=1.1200,
            target_pips=150.0,
            confidence=0.8,
            signal_strength=0.6,
            days_to_target=4,
            weekly_achievement_probability=0.75,
            components={},
            analysis_timestamp='2024-01-01T00:00:00',
            expiry_date='2024-01-05T00:00:00'
        )
        
        market_overview = {
            'total_pairs': 1,
            'active_signals': 1,
            'hold_signals': 0,
            'avg_confidence': 0.8,
            'market_sentiment': 'bullish'
        }
        
        report = SignalReport(
            report_id='TEST_001',
            generation_timestamp='2024-01-01T00:00:00',
            signals={'EURUSD': signal},
            market_overview=market_overview,
            risk_disclaimer='Test disclaimer',
            expiry_timestamp='2024-01-05T00:00:00'
        )
        
        assert report.report_id == 'TEST_001'
        assert 'EURUSD' in report.signals
        assert report.market_overview['total_pairs'] == 1
        assert report.risk_disclaimer == 'Test disclaimer'

class TestGlobalReportGenerator:
    """Test global report generator instance"""
    
    def test_global_instance_exists(self):
        """Test that global report generator instance exists"""
        assert report_generator is not None
        assert isinstance(report_generator, ReportGenerator)
    
    def test_global_instance_has_disclaimer(self):
        """Test global instance has risk disclaimer"""
        assert report_generator.risk_disclaimer is not None
        assert len(report_generator.risk_disclaimer) > 0
    
    def test_global_instance_has_precision_config(self):
        """Test global instance has decimal precision configuration"""
        assert report_generator.decimal_precision is not None
        assert isinstance(report_generator.decimal_precision, dict)
        assert len(report_generator.decimal_precision) > 0

class TestIntegration:
    """Integration tests for report generation"""
    
    def test_full_report_generation_workflow(self):
        """Test complete report generation workflow"""
        generator = ReportGenerator()
        
        # Create comprehensive test signals
        signals = {
            'EURUSD': TradingSignal(
                pair='EURUSD',
                action='BUY',
                entry_price=1.1050,
                exit_price=1.1200,
                stop_loss=1.0900,
                take_profit=1.1200,
                target_pips=150.0,
                confidence=0.8,
                signal_strength=0.6,
                days_to_target=4,
                weekly_achievement_probability=0.75,
                components={
                    'technical': SignalComponent('technical', 0.7, 0.8, 0.35, {}),
                    'economic': SignalComponent('economic', 0.4, 0.7, 0.25, {}),
                    'sentiment': SignalComponent('sentiment', 0.3, 0.6, 0.20, {}),
                    'geopolitical': SignalComponent('geopolitical', 0.1, 0.4, 0.10, {})
                },
                analysis_timestamp='2024-01-01T00:00:00',
                expiry_date='2024-01-05T00:00:00'
            ),
            'GBPUSD': TradingSignal(
                pair='GBPUSD',
                action='SELL',
                entry_price=1.2500,
                exit_price=1.2350,
                stop_loss=1.2650,
                take_profit=1.2350,
                target_pips=150.0,
                confidence=0.6,
                signal_strength=-0.4,
                days_to_target=4,
                weekly_achievement_probability=0.65,
                components={
                    'technical': SignalComponent('technical', -0.5, 0.7, 0.35, {}),
                    'economic': SignalComponent('economic', -0.3, 0.6, 0.25, {}),
                    'sentiment': SignalComponent('sentiment', -0.2, 0.5, 0.20, {}),
                    'geopolitical': SignalComponent('geopolitical', -0.1, 0.3, 0.10, {})
                },
                analysis_timestamp='2024-01-01T00:00:00',
                expiry_date='2024-01-05T00:00:00'
            ),
            'USDCAD': TradingSignal(
                pair='USDCAD',
                action='HOLD',
                entry_price=None,
                exit_price=None,
                stop_loss=None,
                take_profit=None,
                target_pips=None,
                confidence=0.2,
                signal_strength=0.1,
                days_to_target=None,
                weekly_achievement_probability=0.0,
                components={
                    'technical': SignalComponent('technical', 0.1, 0.3, 0.35, {}),
                    'economic': SignalComponent('economic', 0.0, 0.2, 0.25, {}),
                    'sentiment': SignalComponent('sentiment', 0.05, 0.1, 0.20, {}),
                    'geopolitical': SignalComponent('geopolitical', 0.0, 0.1, 0.10, {})
                },
                analysis_timestamp='2024-01-01T00:00:00',
                expiry_date='2024-01-05T00:00:00'
            )
        }
        
        # Test all output formats
        formats = ['txt', 'json', 'csv', 'html']
        
        for output_format in formats:
            report = generator.generate_comprehensive_report(signals, output_format)
            
            assert isinstance(report, str)
            assert len(report) > 0
            
            # Each format should contain signal data
            if output_format == 'json':
                # JSON should be parseable
                parsed = json.loads(report)
                assert 'signals' in parsed
                assert 'EURUSD' in parsed['signals']
            else:
                # Other formats should contain pair names
                assert 'EURUSD' in report
                assert 'GBPUSD' in report
                assert 'USDCAD' in report
    
    def test_report_consistency_across_formats(self):
        """Test that all formats contain consistent information"""
        generator = ReportGenerator()
        
        signal = TradingSignal(
            pair='EURUSD',
            action='BUY',
            entry_price=1.1050,
            exit_price=1.1200,
            stop_loss=1.0900,
            take_profit=1.1200,
            target_pips=150.0,
            confidence=0.8,
            signal_strength=0.6,
            days_to_target=4,
            weekly_achievement_probability=0.75,
            components={},
            analysis_timestamp='2024-01-01T00:00:00',
            expiry_date='2024-01-05T00:00:00'
        )
        
        signals = {'EURUSD': signal}
        
        # Generate all formats
        txt_report = generator.generate_comprehensive_report(signals, 'txt')
        json_report = generator.generate_comprehensive_report(signals, 'json')
        csv_report = generator.generate_comprehensive_report(signals, 'csv')
        html_report = generator.generate_comprehensive_report(signals, 'html')
        
        # All should contain key information
        key_info = ['EURUSD', 'BUY', '1.10500', '1.12000']
        
        for info in key_info:
            assert info in txt_report
            assert info in html_report
            # CSV uses different formatting
            if info != '1.10500' and info != '1.12000':
                assert info in csv_report
        
        # JSON should have structured data
        json_data = json.loads(json_report)
        assert json_data['signals']['EURUSD']['action'] == 'BUY'
        assert json_data['signals']['EURUSD']['entry_price'] == 1.1050
    
    def test_error_handling_robustness(self):
        """Test error handling in various scenarios"""
        generator = ReportGenerator()
        
        # Test with empty signals
        empty_report = generator.generate_comprehensive_report({}, 'txt')
        assert isinstance(empty_report, str)
        assert len(empty_report) > 0
        
        # Test with invalid format
        invalid_report = generator.generate_comprehensive_report({}, 'invalid')
        assert 'ERROR GENERATING' in invalid_report
        
        # Test saving to invalid directory
        with pytest.raises(Exception):
            generator.save_report("test", 'txt', '/invalid/path/that/does/not/exist')
    
    def test_price_formatting_edge_cases(self):
        """Test price formatting with edge cases"""
        generator = ReportGenerator()
        
        # Test very small prices
        small_price = generator._format_price('EURUSD', 0.00001)
        assert '0.00001' == small_price
        
        # Test very large prices
        large_price = generator._format_price('USDJPY', 999.999)
        assert '999.999' == large_price
        
        # Test zero price
        zero_price = generator._format_price('EURUSD', 0.0)
        assert '0.00000' == zero_price
        
        # Test negative price (shouldn't happen in real forex but test robustness)
        neg_price = generator._format_price('EURUSD', -1.1050)
        assert '-1.10500' == neg_price