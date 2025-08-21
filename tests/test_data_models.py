#!/usr/bin/env python3
"""
Unit tests for data models
"""

import unittest
from pathlib import Path
import sys

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.data_processors.data_models import (
    ForexSignal, OptionsPlay, EarningsRelease, 
    PremiumSwingTrade, PremiumDayTrade
)


class TestForexSignal(unittest.TestCase):
    """Test ForexSignal data model"""
    
    def test_forex_signal_creation(self):
        """Test creating ForexSignal instance"""
        signal = ForexSignal(
            pair="EURUSD",
            high=1.1158,
            average=1.0742,
            low=1.0238,
            mt4_action="SELL",
            exit_price=1.0850
        )
        
        self.assertEqual(signal.pair, "EURUSD")
        self.assertEqual(signal.high, 1.1158)
        self.assertEqual(signal.average, 1.0742)
        self.assertEqual(signal.low, 1.0238)
        self.assertEqual(signal.mt4_action, "SELL")
        self.assertEqual(signal.exit_price, 1.0850)
        
    def test_forex_signal_format_output(self):
        """Test ForexSignal format_output method"""
        signal = ForexSignal(
            pair="EURUSD",
            high=1.11587654,
            average=1.07429999,
            low=1.02381111,
            mt4_action="SELL",
            exit_price=1.08504444
        )
        
        output = signal.format_output()
        
        # Verify format
        self.assertIn("Pair: EURUSD", output)
        self.assertIn("High: 1.1159", output)  # 4 decimal places
        self.assertIn("Average: 1.0743", output)
        self.assertIn("Low: 1.0238", output)
        self.assertIn("MT4 Action: SELL", output)
        self.assertIn("Exit: 1.0850", output)
        
        # Verify NO emojis
        self.assertNotIn("🔴", output)
        self.assertNotIn("🟢", output)
        
    def test_forex_signal_optional_exit(self):
        """Test ForexSignal with optional exit price"""
        signal = ForexSignal(
            pair="GBPUSD",
            high=1.2500,
            average=1.2000,
            low=1.1500,
            mt4_action="BUY",
            exit_price=None
        )
        
        output = signal.format_output()
        
        # Exit line should not appear if None
        self.assertNotIn("Exit:", output)


class TestOptionsPlay(unittest.TestCase):
    """Test OptionsPlay data model"""
    
    def test_options_play_creation(self):
        """Test creating OptionsPlay instance"""
        play = OptionsPlay(
            symbol="QQQ",
            week_52_high=480.92,
            week_52_low=478.13,
            call_threshold=521.68,
            put_threshold=None,
            status="TRADE IN PROFIT"
        )
        
        self.assertEqual(play.symbol, "QQQ")
        self.assertEqual(play.week_52_high, 480.92)
        self.assertEqual(play.week_52_low, 478.13)
        self.assertEqual(play.call_threshold, 521.68)
        self.assertIsNone(play.put_threshold)
        self.assertEqual(play.status, "TRADE IN PROFIT")
        
    def test_options_play_format_output(self):
        """Test OptionsPlay format_output method"""
        play = OptionsPlay(
            symbol="SPY",
            week_52_high=450.00,
            week_52_low=400.00,
            call_threshold=460.00,
            put_threshold=390.00,
            status="WATCHING"
        )
        
        output = play.format_output()
        
        # Verify format
        self.assertIn("Symbol: SPY", output)
        self.assertIn("52 Week High: 450.00", output)
        self.assertIn("52 Week Low: 400.00", output)
        self.assertIn("CALL > 460.00", output)
        self.assertIn("PUT < 390.00", output)
        self.assertIn("Status: WATCHING", output)
        
        # Verify NO emojis
        self.assertNotIn("📈", output)
        self.assertNotIn("💹", output)
        
    def test_options_play_partial_thresholds(self):
        """Test OptionsPlay with partial thresholds"""
        # Only call threshold
        play1 = OptionsPlay(
            symbol="AAPL",
            week_52_high=200.00,
            week_52_low=150.00,
            call_threshold=210.00,
            put_threshold=None,
            status=None
        )
        
        output1 = play1.format_output()
        self.assertIn("CALL > 210.00", output1)
        self.assertIn("PUT < N/A", output1)
        self.assertNotIn("Status:", output1)
        
        # Only put threshold
        play2 = OptionsPlay(
            symbol="MSFT",
            week_52_high=380.00,
            week_52_low=320.00,
            call_threshold=None,
            put_threshold=310.00,
            status=None
        )
        
        output2 = play2.format_output()
        self.assertIn("CALL > N/A", output2)
        self.assertIn("PUT < 310.00", output2)


class TestEarningsRelease(unittest.TestCase):
    """Test EarningsRelease data model"""
    
    def test_earnings_release_creation(self):
        """Test creating EarningsRelease instance"""
        release = EarningsRelease(
            ticker="AAPL",
            company_name="Apple Inc.",
            release_date="2025-01-20",
            release_time="After Market Close",
            estimate=2.15,
            previous=2.10
        )
        
        self.assertEqual(release.ticker, "AAPL")
        self.assertEqual(release.company_name, "Apple Inc.")
        self.assertEqual(release.release_date, "2025-01-20")
        self.assertEqual(release.release_time, "After Market Close")
        self.assertEqual(release.estimate, 2.15)
        self.assertEqual(release.previous, 2.10)
        
    def test_earnings_release_format_output(self):
        """Test EarningsRelease format_output method"""
        release = EarningsRelease(
            ticker="GOOGL",
            company_name="Alphabet Inc.",
            release_date="2025-01-21",
            release_time="Before Market Open",
            estimate=1.85,
            previous=1.80
        )
        
        output = release.format_output()
        
        # Verify format
        self.assertIn("GOOGL - Alphabet Inc.", output)
        self.assertIn("Date: January 21, 2025", output)
        self.assertIn("Time: Before Market Open", output)
        self.assertIn("Estimate: $1.85", output)
        self.assertIn("Previous: $1.80", output)
        
        # Verify NO emojis
        self.assertNotIn("📅", output)
        self.assertNotIn("📊", output)
        
    def test_earnings_release_optional_fields(self):
        """Test EarningsRelease with optional fields"""
        release = EarningsRelease(
            ticker="TSLA",
            company_name="Tesla Inc.",
            release_date="2025-01-22",
            release_time=None,
            estimate=None,
            previous=3.50
        )
        
        output = release.format_output()
        
        # Time should not appear if None
        self.assertNotIn("Time:", output)
        # Estimate should show N/A
        self.assertIn("Estimate: N/A", output)
        self.assertIn("Previous: $3.50", output)


class TestPremiumTrades(unittest.TestCase):
    """Test Premium Trade data models"""
    
    def test_premium_swing_trade_creation(self):
        """Test creating PremiumSwingTrade instance"""
        trade = PremiumSwingTrade(
            ticker="JOYY",
            company_name="JOYY Inc.",
            earnings_date="May 26, 2025",
            current_price=47.67,
            rationale="Strong earnings momentum expected based on sector trends"
        )
        
        self.assertEqual(trade.ticker, "JOYY")
        self.assertEqual(trade.company_name, "JOYY Inc.")
        self.assertEqual(trade.earnings_date, "May 26, 2025")
        self.assertEqual(trade.current_price, 47.67)
        self.assertIn("Strong earnings momentum", trade.rationale)
        
    def test_premium_swing_trade_format_output(self):
        """Test PremiumSwingTrade format_output method"""
        trade = PremiumSwingTrade(
            ticker="ROKU",
            company_name="Roku Inc.",
            earnings_date="February 15, 2025",
            current_price=65.50,
            rationale="Streaming growth continues"
        )
        
        output = trade.format_output()
        
        # Verify format
        self.assertIn("Roku Inc. (ROKU)", output)
        self.assertIn("Earnings Report: February 15, 2025", output)
        self.assertIn("Current Price: $65.50", output)
        self.assertIn("Rationale: Streaming growth continues", output)
        
        # Verify NO emojis
        self.assertNotIn("💼", output)
        
    def test_premium_day_trade_creation(self):
        """Test creating PremiumDayTrade instance"""
        trade = PremiumDayTrade(
            ticker="TSLA",
            company_name="Tesla Inc.",
            current_price=250.00,
            rationale="Breaking key resistance at 248",
            updated_date="January 20, 2025"
        )
        
        self.assertEqual(trade.ticker, "TSLA")
        self.assertEqual(trade.company_name, "Tesla Inc.")
        self.assertEqual(trade.current_price, 250.00)
        self.assertEqual(trade.rationale, "Breaking key resistance at 248")
        self.assertEqual(trade.updated_date, "January 20, 2025")
        
    def test_premium_day_trade_format_output(self):
        """Test PremiumDayTrade format_output method"""
        trade = PremiumDayTrade(
            ticker="NVDA",
            company_name="NVIDIA Corporation",
            current_price=550.75,
            rationale="AI momentum continues with strong volume",
            updated_date="January 21, 2025"
        )
        
        output = trade.format_output()
        
        # Verify format
        self.assertIn("NVIDIA Corporation (NVDA)", output)
        self.assertIn("Current Price: $550.75", output)
        self.assertIn("Rationale: AI momentum continues", output)
        self.assertIn("Updated: January 21, 2025", output)
        
        # Verify NO emojis
        self.assertNotIn("🎯", output)
        self.assertNotIn("📈", output)


class TestDataModelIntegration(unittest.TestCase):
    """Test integration between data models"""
    
    def test_all_models_no_emojis(self):
        """Verify all models produce emoji-free output"""
        # Create instances of all models
        models = [
            ForexSignal("EURUSD", 1.1, 1.05, 1.0, "BUY", 1.08),
            OptionsPlay("QQQ", 480, 470, 490, None, "WATCHING"),
            EarningsRelease("AAPL", "Apple", "2025-01-20", "AMC", 2.15, 2.10),
            PremiumSwingTrade("JOYY", "JOYY Inc.", "May 26", 47.67, "Earnings play"),
            PremiumDayTrade("TSLA", "Tesla", 250, "Momentum", "Jan 20")
        ]
        
        # Common emojis to check for
        emojis = ["🔴", "🟢", "📊", "📈", "💹", "📅", "💼", "🎯", "🚀", "💰", "🏦", "💵"]
        
        # Verify no emojis in any output
        for model in models:
            output = model.format_output()
            for emoji in emojis:
                self.assertNotIn(emoji, output, 
                    f"Found emoji {emoji} in {model.__class__.__name__} output")
                
    def test_all_models_have_format_output(self):
        """Verify all models implement format_output method"""
        models = [
            ForexSignal("TEST", 1, 1, 1, "BUY", 1),
            OptionsPlay("TEST", 1, 1, 1, 1, "TEST"),
            EarningsRelease("TEST", "Test", "2025-01-01", "BMO", 1, 1),
            PremiumSwingTrade("TEST", "Test", "Jan 1", 1, "Test"),
            PremiumDayTrade("TEST", "Test", 1, "Test", "Jan 1")
        ]
        
        for model in models:
            self.assertTrue(hasattr(model, 'format_output'), 
                f"{model.__class__.__name__} missing format_output method")
            self.assertTrue(callable(getattr(model, 'format_output')),
                f"{model.__class__.__name__}.format_output is not callable")


if __name__ == '__main__':
    unittest.main()