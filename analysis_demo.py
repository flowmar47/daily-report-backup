#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Analysis Demo Script
Demonstrates API forex data analysis without sending messages
Shows the technical/economic/geopolitical analysis pipeline in action
"""

import asyncio
import sys
import os
import logging
from datetime import datetime
from typing import Dict, Any

# Set encoding for stdout
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
elif hasattr(sys.stdout, 'buffer'):
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Add Signals directory to path
signals_path = os.path.join(os.path.dirname(__file__), 'Signals')
if signals_path not in sys.path:
    sys.path.append(signals_path)

from forex_signal_integration import ForexSignalIntegration

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('logs/analysis_demo.log')
    ]
)
logger = logging.getLogger(__name__)

class AnalysisDemo:
    """Demonstrates forex signal analysis without messaging"""
    
    def __init__(self):
        """Initialize the analysis demo"""
        self.signal_integration = ForexSignalIntegration()
        
    def format_analysis_details(self, signal_data: Dict[str, Any]) -> str:
        """Format detailed analysis information for display"""
        if not signal_data or not signal_data.get('signals'):
            return "❌ No valid signals generated"
        
        output_lines = []
        output_lines.append("=" * 80)
        output_lines.append("🔍 FOREX SIGNAL ANALYSIS DEMONSTRATION")
        output_lines.append("=" * 80)
        output_lines.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S PST')}")
        output_lines.append(f"Data Sources: {', '.join(signal_data.get('data_sources', []))}")
        output_lines.append(f"Analysis Status: {'✅ SUCCESSFUL' if signal_data.get('has_real_data') else '❌ NO REAL DATA'}")
        output_lines.append("")
        
        # Display each signal with detailed breakdown
        for signal in signal_data['signals']:
            pair = signal.get('pair', 'Unknown')
            action = signal.get('action', 'Unknown')
            entry = signal.get('entry_price', 0)
            target = signal.get('target_price', 0)
            confidence = signal.get('confidence', 0)
            
            output_lines.append(f"📊 ANALYSIS FOR {pair}")
            output_lines.append("-" * 50)
            output_lines.append(f"Current Price: {entry:.5f}")
            output_lines.append(f"Signal Action: {action}")
            output_lines.append(f"Target Price: {target:.5f}")
            output_lines.append(f"Overall Confidence: {confidence:.2f}")
            output_lines.append("")
            
            # Technical Analysis Details
            if 'analysis_breakdown' in signal:
                breakdown = signal['analysis_breakdown']
                
                if 'technical' in breakdown:
                    tech = breakdown['technical']
                    output_lines.append("🔧 TECHNICAL ANALYSIS (75% weight):")
                    output_lines.append(f"  • RSI Score: {tech.get('rsi_score', 'N/A')}")
                    output_lines.append(f"  • MACD Score: {tech.get('macd_score', 'N/A')}")
                    output_lines.append(f"  • Bollinger Score: {tech.get('bollinger_score', 'N/A')}")
                    output_lines.append(f"  • Pattern Score: {tech.get('pattern_score', 'N/A')}")
                    output_lines.append(f"  • Overall Technical: {tech.get('overall_score', 'N/A')}")
                    output_lines.append("")
                
                if 'economic' in breakdown:
                    econ = breakdown['economic']
                    output_lines.append("💰 ECONOMIC ANALYSIS (20% weight):")
                    output_lines.append(f"  • Interest Rate Differential: {econ.get('rate_differential', 'N/A')}")
                    output_lines.append(f"  • Economic Calendar Impact: {econ.get('calendar_impact', 'N/A')}")
                    output_lines.append(f"  • Central Bank Sentiment: {econ.get('cb_sentiment', 'N/A')}")
                    output_lines.append(f"  • Overall Economic: {econ.get('overall_score', 'N/A')}")
                    output_lines.append("")
                
                if 'geopolitical' in breakdown:
                    geo = breakdown['geopolitical']
                    output_lines.append("🌍 GEOPOLITICAL ANALYSIS (5% weight):")
                    output_lines.append(f"  • Event Impact: {geo.get('event_impact', 'N/A')}")
                    output_lines.append(f"  • Regional Stability: {geo.get('stability', 'N/A')}")
                    output_lines.append(f"  • Overall Geopolitical: {geo.get('overall_score', 'N/A')}")
                    output_lines.append("")
            
            # Risk Management
            if 'risk_management' in signal:
                risk = signal['risk_management']
                output_lines.append("⚖️ RISK MANAGEMENT:")
                output_lines.append(f"  • Stop Loss: {risk.get('stop_loss', 'N/A')} pips")
                output_lines.append(f"  • Take Profit: {risk.get('take_profit', 'N/A')} pips")
                output_lines.append(f"  • Risk/Reward Ratio: {risk.get('risk_reward_ratio', 'N/A')}")
                output_lines.append("")
            
            output_lines.append("=" * 50)
            output_lines.append("")
        
        # System Health Information
        output_lines.append("🏥 SYSTEM HEALTH:")
        output_lines.append(f"  • Setup Status: {'✅ OK' if self.signal_integration.setup_successful else '❌ FAILED'}")
        output_lines.append(f"  • API Connectivity: {len(signal_data.get('data_sources', []))} sources active")
        output_lines.append(f"  • Data Freshness: {signal_data.get('data_freshness', 'Unknown')}")
        output_lines.append("")
        
        output_lines.append("=" * 80)
        return "\n".join(output_lines)
    
    async def run_analysis_demo(self) -> bool:
        """Run the analysis demonstration"""
        try:
            print("🚀 Starting Forex Signal Analysis Demo...")
            print("📡 This will demonstrate API data analysis without sending messages")
            print("")
            
            # Check system setup
            if not self.signal_integration.setup_successful:
                print("❌ System setup failed - cannot run analysis demo")
                return False
            
            print("✅ System setup successful")
            print("🔄 Generating forex signals with analysis breakdown...")
            print("")
            
            # Generate signals with full analysis
            signal_data = await self.signal_integration.generate_forex_signals()
            
            if not signal_data:
                print("❌ Signal generation failed - no data returned")
                return False
            
            # Display detailed analysis
            analysis_display = self.format_analysis_details(signal_data)
            print(analysis_display)
            
            # Save to file for review
            with open('logs/latest_analysis_demo.txt', 'w') as f:
                f.write(analysis_display)
            
            print("📄 Analysis saved to logs/latest_analysis_demo.txt")
            print("")
            print("✅ Analysis demo completed successfully!")
            
            return True
            
        except Exception as e:
            logger.error(f"Analysis demo failed: {e}")
            print(f"❌ Analysis demo failed: {e}")
            return False

async def main():
    """Main entry point"""
    print("🔍 Forex Signal Analysis Demo")
    print("Demonstrates API-based analysis pipeline")
    print("")
    
    # Create demo instance
    demo = AnalysisDemo()
    
    # Run the demonstration
    success = await demo.run_analysis_demo()
    
    if success:
        print("Demo completed successfully!")
        print("")
        print("🎯 Next steps:")
        print("1. Review the analysis output above")
        print("2. Check logs/latest_analysis_demo.txt for details")
        print("3. Verify the technical/economic analysis is working")
        print("4. If satisfied, proceed with live system testing")
    else:
        print("Demo failed - check logs for details")
        return 1
    
    return 0

if __name__ == "__main__":
    # Create logs directory if needed
    os.makedirs('logs', exist_ok=True)
    
    # Run the demo
    exit_code = asyncio.run(main())
    sys.exit(exit_code)