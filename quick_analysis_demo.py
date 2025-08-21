#!/usr/bin/env python3
"""
Quick Analysis Demo - Single Pair Analysis
Shows the technical/economic analysis breakdown for one pair
"""

import asyncio
import sys
import os
from datetime import datetime

# Add Signals directory to path
signals_path = os.path.join(os.path.dirname(__file__), 'Signals')
if signals_path not in sys.path:
    sys.path.append(signals_path)

from forex_signal_integration import ForexSignalIntegration

async def quick_analysis_demo():
    """Quick demo with just one currency pair to avoid rate limits"""
    print("🔍 Quick Forex Analysis Demo")
    print("=" * 50)
    
    try:
        # Initialize system
        fsi = ForexSignalIntegration()
        if not fsi.setup_successful:
            print("❌ System setup failed")
            return False
        
        print("✅ System initialized successfully")
        
        # Test with just USDJPY to avoid rate limits
        fsi.currency_pairs = ['USDJPY']
        print("📊 Analyzing USDJPY...")
        print()
        
        # Generate signal
        result = await fsi.generate_forex_signals()
        
        if not result or not result.get('signals'):
            print("❌ No signals generated")
            return False
        
        # Display the signal
        signal = result['signals'][0]
        
        print("📈 ANALYSIS RESULTS:")
        print("=" * 30)
        print(f"Pair: {signal.get('pair', 'Unknown')}")
        print(f"Action: {signal.get('action', 'Unknown')}")
        print(f"Entry Price: {signal.get('entry_price', 0):.5f}")
        print(f"Target Price: {signal.get('target_price', 0):.5f}")
        print(f"Confidence: {signal.get('confidence', 0):.2f}")
        print()
        
        # Show analysis breakdown if available
        if 'analysis_breakdown' in signal:
            breakdown = signal['analysis_breakdown']
            print("🔧 ANALYSIS BREAKDOWN:")
            
            if 'technical' in breakdown:
                tech = breakdown['technical']
                print(f"  Technical Score: {tech.get('overall_score', 'N/A')}")
            
            if 'economic' in breakdown:
                econ = breakdown['economic']
                print(f"  Economic Score: {econ.get('overall_score', 'N/A')}")
            
            if 'geopolitical' in breakdown:
                geo = breakdown['geopolitical']
                print(f"  Geopolitical Score: {geo.get('overall_score', 'N/A')}")
        
        print()
        print("✅ Analysis completed successfully!")
        
        # Show system status
        print()
        print("📊 SYSTEM STATUS:")
        print(f"Data Sources: {len(result.get('data_sources', []))} active")
        print(f"Has Real Data: {result.get('has_real_data', False)}")
        print(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        return True
        
    except Exception as e:
        print(f"❌ Demo failed: {e}")
        return False

if __name__ == "__main__":
    success = asyncio.run(quick_analysis_demo())
    if success:
        print("\n🎯 Demo completed successfully!")
    else:
        print("\n❌ Demo failed!")