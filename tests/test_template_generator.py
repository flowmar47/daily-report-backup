#!/usr/bin/env python3
"""
Unit tests for StructuredTemplateGenerator
"""

import unittest
from pathlib import Path
import sys

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.data_processors.template_generator import StructuredTemplateGenerator
from src.data_processors.data_models import (
    ForexSignal, OptionsPlay, EarningsRelease, 
    PremiumSwingTrade, PremiumDayTrade
)


class TestStructuredTemplateGenerator(unittest.TestCase):
    """Test StructuredTemplateGenerator functionality"""
    
    def setUp(self):
        """Set up test environment"""
        self.generator = StructuredTemplateGenerator()
        
    def test_initialization(self):
        """Test StructuredTemplateGenerator initialization"""
        self.assertIsInstance(self.generator, StructuredTemplateGenerator)
        
    def test_generate_forex_section(self):
        """Test forex section generation"""
        # Create test forex signals
        signals = [
            ForexSignal(
                pair="EURUSD",
                high=1.1158,
                average=1.0742,
                low=1.0238,
                mt4_action="SELL",
                exit_price=1.0850
            ),
            ForexSignal(
                pair="GBPUSD",
                high=1.2500,
                average=1.2000,
                low=1.1500,
                mt4_action="BUY",
                exit_price=1.2200
            )
        ]
        
        section = self.generator._generate_forex_section(signals)
        
        # Verify section content
        self.assertIn("FOREX PAIRS", section)
        self.assertIn("EURUSD", section)
        self.assertIn("GBPUSD", section)
        self.assertIn("MT4 Action: SELL", section)
        self.assertIn("MT4 Action: BUY", section)
        
        # Verify NO emojis
        self.assertNotIn("🔴", section)
        self.assertNotIn("🟢", section)
        self.assertNotIn("📊", section)
        
    def test_generate_options_section(self):
        """Test options section generation"""
        # Create test options plays
        plays = [
            OptionsPlay(
                symbol="QQQ",
                week_52_high=480.92,
                week_52_low=478.13,
                call_threshold=521.68,
                put_threshold=None,
                status="TRADE IN PROFIT"
            ),
            OptionsPlay(
                symbol="SPY",
                week_52_high=450.00,
                week_52_low=400.00,
                call_threshold=None,
                put_threshold=380.00,
                status="WATCHING"
            )
        ]
        
        section = self.generator._generate_options_section(plays)
        
        # Verify section content
        self.assertIn("EQUITIES AND OPTIONS", section)
        self.assertIn("Symbol: QQQ", section)
        self.assertIn("Symbol: SPY", section)
        self.assertIn("CALL > 521.68", section)
        self.assertIn("PUT < 380.00", section)
        self.assertIn("Status: TRADE IN PROFIT", section)
        
        # Verify NO emojis
        self.assertNotIn("📈", section)
        self.assertNotIn("💹", section)
        
    def test_generate_earnings_section(self):
        """Test earnings section generation"""
        # Create test earnings releases
        releases = [
            EarningsRelease(
                ticker="AAPL",
                company_name="Apple Inc.",
                release_date="2025-01-20",
                release_time="After Market Close",
                estimate=2.15,
                previous=2.10
            ),
            EarningsRelease(
                ticker="GOOGL",
                company_name="Alphabet Inc.",
                release_date="2025-01-21",
                release_time="Before Market Open",
                estimate=1.85,
                previous=1.80
            )
        ]
        
        section = self.generator._generate_earnings_section(releases)
        
        # Verify section content
        self.assertIn("EARNINGS RELEASES THIS WEEK", section)
        self.assertIn("AAPL - Apple Inc.", section)
        self.assertIn("GOOGL - Alphabet Inc.", section)
        self.assertIn("After Market Close", section)
        self.assertIn("Before Market Open", section)
        
        # Verify NO emojis
        self.assertNotIn("📅", section)
        self.assertNotIn("📊", section)
        
    def test_generate_premium_trades_section(self):
        """Test premium trades section generation"""
        # Create test premium trades
        swing_trade = PremiumSwingTrade(
            ticker="JOYY",
            company_name="JOYY Inc.",
            earnings_date="May 26, 2025",
            current_price=47.67,
            rationale="Strong earnings momentum expected"
        )
        
        day_trade = PremiumDayTrade(
            ticker="TSLA",
            company_name="Tesla Inc.",
            current_price=250.00,
            rationale="Breaking key resistance level",
            updated_date="January 20, 2025"
        )
        
        trades = [swing_trade, day_trade]
        section = self.generator._generate_premium_trades_section(trades, [swing_trade], [day_trade])
        
        # Verify section content
        self.assertIn("PREMIUM SWING TRADES", section)
        self.assertIn("PREMIUM DAY TRADES", section)
        self.assertIn("JOYY Inc. (JOYY)", section)
        self.assertIn("Tesla Inc. (TSLA)", section)
        self.assertIn("Current Price: $47.67", section)
        self.assertIn("Current Price: $250.00", section)
        
        # Verify NO emojis
        self.assertNotIn("💼", section)
        self.assertNotIn("🎯", section)
        
    def test_generate_report_full(self):
        """Test full report generation"""
        # Create comprehensive test data
        data = {
            'forex_signals': [
                ForexSignal(
                    pair="EURUSD",
                    high=1.1158,
                    average=1.0742,
                    low=1.0238,
                    mt4_action="SELL",
                    exit_price=1.0850
                )
            ],
            'options_plays': [
                OptionsPlay(
                    symbol="QQQ",
                    week_52_high=480.92,
                    week_52_low=478.13,
                    call_threshold=521.68,
                    put_threshold=None,
                    status="TRADE IN PROFIT"
                )
            ],
            'earnings_releases': [
                EarningsRelease(
                    ticker="AAPL",
                    company_name="Apple Inc.",
                    release_date="2025-01-20",
                    release_time="After Market Close",
                    estimate=2.15,
                    previous=2.10
                )
            ],
            'premium_trades': [
                PremiumSwingTrade(
                    ticker="JOYY",
                    company_name="JOYY Inc.",
                    earnings_date="May 26, 2025",
                    current_price=47.67,
                    rationale="Strong earnings momentum"
                )
            ]
        }
        
        report = self.generator.generate_report(data)
        
        # Verify all sections present
        self.assertIn("FOREX PAIRS", report)
        self.assertIn("EQUITIES AND OPTIONS", report)
        self.assertIn("EARNINGS RELEASES THIS WEEK", report)
        self.assertIn("PREMIUM SWING TRADES", report)
        
        # Verify NO emojis anywhere
        emoji_list = ["🔴", "🟢", "📊", "📈", "💹", "📅", "💼", "🎯", "🚀", "💰"]
        for emoji in emoji_list:
            self.assertNotIn(emoji, report)
            
    def test_empty_data_handling(self):
        """Test handling of empty data"""
        # Empty data dict
        empty_data = {
            'forex_signals': [],
            'options_plays': [],
            'earnings_releases': [],
            'premium_trades': []
        }
        
        report = self.generator.generate_report(empty_data)
        
        # Should still have section headers
        self.assertIn("FOREX PAIRS", report)
        self.assertIn("No forex signals available", report)
        
    def test_partial_data_handling(self):
        """Test handling of partial data"""
        # Only forex data
        partial_data = {
            'forex_signals': [
                ForexSignal(
                    pair="EURUSD",
                    high=1.1158,
                    average=1.0742,
                    low=1.0238,
                    mt4_action="SELL",
                    exit_price=1.0850
                )
            ]
        }
        
        report = self.generator.generate_report(partial_data)
        
        # Should have forex data
        self.assertIn("EURUSD", report)
        
        # Should handle missing sections gracefully
        self.assertIn("No options plays available", report)
        self.assertIn("No earnings releases", report)
        
    def test_data_formatting_precision(self):
        """Test numerical data formatting precision"""
        signal = ForexSignal(
            pair="EURUSD",
            high=1.11587654,  # Extra decimal places
            average=1.07429999,
            low=1.02381111,
            mt4_action="SELL",
            exit_price=1.08504444
        )
        
        section = self.generator._generate_forex_section([signal])
        
        # Verify proper decimal formatting (4 decimal places for forex)
        self.assertIn("High: 1.1159", section)
        self.assertIn("Average: 1.0743", section)
        self.assertIn("Low: 1.0238", section)
        self.assertIn("Exit: 1.0850", section)
        
    def test_status_formatting(self):
        """Test status field formatting"""
        plays = [
            OptionsPlay(
                symbol="QQQ",
                week_52_high=480.92,
                week_52_low=478.13,
                call_threshold=521.68,
                put_threshold=None,
                status="TRADE IN PROFIT"
            ),
            OptionsPlay(
                symbol="SPY",
                week_52_high=450.00,
                week_52_low=400.00,
                call_threshold=None,
                put_threshold=380.00,
                status=None  # No status
            )
        ]
        
        section = self.generator._generate_options_section(plays)
        
        # Verify status handling
        self.assertIn("Status: TRADE IN PROFIT", section)
        
        # Should not have "Status: None" for second play
        lines = section.split('\n')
        spy_section = '\n'.join([l for l in lines if 'SPY' in l or l.startswith('52 Week') or l.startswith('Strike') or l.startswith('CALL') or l.startswith('PUT')])
        self.assertNotIn("Status:", spy_section)


if __name__ == '__main__':
    unittest.main()