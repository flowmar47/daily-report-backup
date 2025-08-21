#!/usr/bin/env python3
"""
Complete test of the fixed Telegram system with structured data.
"""

import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from src.notifiers.telegram_service import TelegramNotificationService
from src.data_processors.data_models import (
    ForexForecast, OptionsTrade, EarningsReport,
    StructuredFinancialReport
)


async def test_complete_system():
    """Test the complete system with structured data."""
    print("🧪 Testing Complete Fixed System...")
    
    telegram = TelegramNotificationService()
    
    if not telegram.is_configured:
        print("❌ Telegram not configured")
        return False
    
    # Create sample structured data
    forex_forecasts = [
        ForexForecast(
            pair="EURUSD",
            high="1.0850",
            average="1.0825", 
            low="1.0800",
            fourteen_day_average="50 PIPS",
            trade_type="MT4 SELL < 1.0820",
            exit="1.0790",
            trade_status="TRADE IN PROFIT"
        ),
        ForexForecast(
            pair="NZDJPY",
            high="91.68",
            average="88.29",
            low="84.00", 
            fourteen_day_average="80 - 140 PIPS",
            trade_type="MT4 BUY < 81.99",
            exit="86.54",
            trade_status="TRADE IN PROFIT",
            special_badge="NEW!"
        )
    ]
    
    options_trades = [
        OptionsTrade(
            ticker="TSLA",
            fifty_two_week_high="479.70",
            fifty_two_week_low="258.35",
            call_strike="CALL > 352.42",
            put_strike="PUT < 345.45", 
            trade_status="trade in profit",
            special_badge="NEW!"
        ),
        OptionsTrade(
            ticker="QQQ",
            fifty_two_week_high="425.30",
            fifty_two_week_low="305.15",
            call_strike="CALL > 415.00",
            put_strike="PUT < 410.00",
            trade_status="trade in profit"
        )
    ]
    
    earnings_reports = [
        EarningsReport(
            company="Apple Inc",
            ticker="AAPL",
            earnings_date="2024-01-20",
            current_price="$185.25",
            rationale="iPhone 15 sales momentum and services growth expected to exceed expectations."
        )
    ]
    
    # Create structured report
    report = StructuredFinancialReport(
        forex_forecasts=forex_forecasts,
        options_trades=options_trades,
        earnings_reports=earnings_reports
    )
    
    # Generate the exact format you specified
    print("\n📊 Testing Structured Output Format...")
    formatted_output = report.format_complete_report()
    print("Sample of formatted output:")
    print(formatted_output[:500] + "...")
    
    # Test 1: Send complete structured report
    print("\n🧪 Test 1: Complete structured report...")
    success1 = await telegram.send_formatted_financial_report(formatted_output)
    print(f"Result: {'✅ SUCCESS' if success1 else '❌ FAILED'}")
    
    # Test 2: Send individual forex format
    print("\n🧪 Test 2: Individual Forex format...")
    forex_example = forex_forecasts[1].format_output()  # NZDJPY with NEW! badge
    success2 = await telegram.send_message(f"📊 Individual Forex Example:\n\n{forex_example}", parse_mode=None)
    print(f"Result: {'✅ SUCCESS' if success2 else '❌ FAILED'}")
    
    # Test 3: Send individual options format  
    print("\n🧪 Test 3: Individual Options format...")
    options_example = options_trades[0].format_output()  # TSLA with NEW! badge
    success3 = await telegram.send_message(f"📈 Individual Options Example:\n\n{options_example}", parse_mode=None)
    print(f"Result: {'✅ SUCCESS' if success3 else '❌ FAILED'}")
    
    # Test 4: Send earnings format
    print("\n🧪 Test 4: Individual Earnings format...")
    earnings_example = earnings_reports[0].format_output()
    success4 = await telegram.send_message(f"📅 Individual Earnings Example:\n\n{earnings_example}", parse_mode=None)
    print(f"Result: {'✅ SUCCESS' if success4 else '❌ FAILED'}")
    
    # Get summary stats
    stats = report.get_summary_stats()
    print(f"\n📊 Report Statistics:")
    print(f"   Forex Forecasts: {stats['forex_forecasts']}")
    print(f"   Options Trades: {stats['options_trades']}")
    print(f"   Earnings Reports: {stats['earnings_reports']}")
    print(f"   Total Entries: {stats['total_entries']}")
    
    # Overall result
    all_success = success1 and success2 and success3 and success4
    print(f"\n🎯 Complete System Test: {'✅ ALL PASSED' if all_success else '❌ SOME FAILED'}")
    
    return all_success


async def main():
    """Run complete system test."""
    print("🚀 Testing Complete Fixed Financial Alerts System")
    print("=" * 60)
    
    success = await test_complete_system()
    
    if success:
        print("\n🎉 COMPLETE SYSTEM IS WORKING PERFECTLY!")
        print("✅ Telegram messaging: FIXED")
        print("✅ Structured data models: WORKING") 
        print("✅ Exact format output: IMPLEMENTED")
        print("✅ Ready for production use!")
        print("\nYou can now run:")
        print("  python main_structured.py run")
    else:
        print("\n❌ Some tests failed")
        print("Please check the error messages above")
    
    return success


if __name__ == "__main__":
    result = asyncio.run(main())
    sys.exit(0 if result else 1)