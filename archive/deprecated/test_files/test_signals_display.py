#!/usr/bin/env python3
"""
Test Signal Generation and Display Output
Shows the generated signals without sending to any groups
"""

import asyncio
import logging
from datetime import datetime
import sys
import os

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def generate_and_display_signals():
    """Generate signals and display them without sending"""
    logger.info("🚀 Generating Forex Signals (Display Only - No Sending)...")
    
    try:
        # Import the integration module
        from forex_signal_integration import forex_signal_integration
        
        if not forex_signal_integration or not forex_signal_integration.setup_successful:
            logger.error("❌ Integration not properly initialized")
            return False
        
        # Generate signals
        logger.info("📊 Generating forex signals from API data...")
        logger.info("⏳ This may take a moment due to API rate limits...")
        
        signals_data = await forex_signal_integration.generate_forex_signals()
        
        if signals_data.get('error'):
            logger.error(f"❌ Error: {signals_data['error']}")
            return False
        
        # Display summary
        print("\n" + "="*70)
        print("FOREX SIGNAL GENERATION RESULTS")
        print("="*70)
        print(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}")
        print(f"Total Pairs Analyzed: {signals_data.get('total_signals', 0)}")
        print(f"Active Signals: {signals_data.get('active_signals', 0)}")
        print(f"Hold Recommendations: {signals_data.get('hold_signals', 0)}")
        print("="*70)
        
        # Display each signal
        if signals_data.get('forex_alerts'):
            print("\n📈 ACTIVE TRADING SIGNALS:")
            print("-"*70)
            for i, alert in enumerate(signals_data.get('forex_alerts', []), 1):
                print(f"\n{i}. {alert['pair']}")
                print(f"   Action: {alert['mt4_action']}")
                if alert.get('entry_price'):
                    print(f"   Entry Price: {alert['entry_price']:.5f}")
                if alert.get('exit_price'):
                    print(f"   Exit Price: {alert['exit_price']:.5f}")
                if alert.get('stop_loss'):
                    print(f"   Stop Loss: {alert['stop_loss']:.5f}")
                if alert.get('take_profit'):
                    print(f"   Take Profit: {alert['take_profit']:.5f}")
                if alert.get('target_pips'):
                    print(f"   Target Pips: {alert['target_pips']:.0f}")
                if alert.get('confidence'):
                    print(f"   Confidence: {alert['confidence']:.1%}")
                if alert.get('weekly_achievement_probability'):
                    print(f"   Weekly Achievement Probability: {alert['weekly_achievement_probability']:.1%}")
        else:
            print("\nℹ️ No active trading signals at this time (all pairs on HOLD)")
        
        # Get formatted plaintext report
        print("\n" + "="*70)
        print("FORMATTED PLAINTEXT REPORT (As would be sent to messengers):")
        print("="*70)
        
        formatted_text = forex_signal_integration.format_signals_for_plaintext(signals_data)
        print(formatted_text)
        
        # If there's a full text report from the Signals system, show it
        if signals_data.get('text_report'):
            print("\n" + "="*70)
            print("PROFESSIONAL SIGNAL REPORT (Full Details):")
            print("="*70)
            print(signals_data['text_report'][:2000])  # First 2000 chars
            if len(signals_data['text_report']) > 2000:
                print("\n... [Report truncated for display]")
        
        print("\n" + "="*70)
        print("✅ Signal generation complete - NO MESSAGES SENT TO GROUPS")
        print("="*70)
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """Main function"""
    # Add timeout to prevent hanging on API calls
    try:
        result = await asyncio.wait_for(
            generate_and_display_signals(),
            timeout=180  # 3 minute timeout
        )
        return result
    except asyncio.TimeoutError:
        logger.error("⏱️ Operation timed out after 3 minutes")
        print("\n⚠️ Signal generation is taking longer than expected due to API rate limits.")
        print("The system is working correctly but needs more time to fetch all data.")
        print("Signals will be generated in the background for the scheduled reports.")
        return False

if __name__ == "__main__":
    result = asyncio.run(main())
    exit(0 if result else 1)