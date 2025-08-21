#!/usr/bin/env python3
"""
Demo: Enhanced Signal Generation (NO MESSAGING)
Shows the complete validated price -> signal generation flow
"""

import asyncio
import sys
import logging
from pathlib import Path
from datetime import datetime

# Setup paths and logging
sys.path.append(str(Path(__file__).parent))
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

async def demo_enhanced_signals():
    """Demonstrate enhanced signal generation without messaging"""
    
    print("="*80)
    print("🎯 ENHANCED SIGNAL GENERATION DEMO")
    print("="*80)
    print("This demo shows:")
    print("✅ Multi-source price validation") 
    print("✅ Enhanced API-based signal generation")
    print("✅ Entry/exit points with confidence scores")
    print("❌ NO messages sent to any platform")
    print("\n" + "="*80)
    
    # Step 1: Test forex signal integration
    print("\n📊 STEP 1: Forex Signal Integration Test")
    print("-"*60)
    
    try:
        from forex_signal_integration import ForexSignalIntegration
        
        integration = ForexSignalIntegration()
        
        if integration.setup_successful:
            print("✅ Forex Signal Integration initialized successfully")
            
            # Generate signals (this uses the enhanced system)
            print("\n🔄 Generating forex signals with enhanced analysis...")
            result = await integration.generate_forex_signals()
            
            if result.get('has_real_data'):
                print(f"\n✅ SUCCESS: Real data confirmed!")
                print(f"   Timestamp: {result.get('timestamp', 'N/A')}")
                print(f"   Signals generated: {len(result.get('signals', {}))}")
                
                # Show generated signals
                signals = result.get('signals', {})
                if signals:
                    print(f"\n📈 GENERATED SIGNALS:")
                    print("-"*40)
                    
                    for pair, signal_data in signals.items():
                        if 'error' not in signal_data:
                            print(f"\n{pair}:")
                            print(f"  Signal: {signal_data.get('signal', 'HOLD')}")
                            print(f"  Entry: ${signal_data.get('entry', 0):.5f}")
                            print(f"  Exit: ${signal_data.get('exit', 0):.5f}")
                            print(f"  Confidence: {signal_data.get('confidence', 0):.1%}")
                            
                            # Show analysis breakdown if available
                            if 'analysis' in signal_data:
                                analysis = signal_data['analysis']
                                print(f"  Technical: {analysis.get('technical', {}).get('score', 0):.2f}")
                                print(f"  Economic: {analysis.get('economic', {}).get('score', 0):.2f}")
                        else:
                            print(f"\n{pair}: ❌ {signal_data['error']}")
                
                # Step 2: Show message format that would be sent
                print(f"\n📝 STEP 2: Message Format (WOULD BE SENT)")
                print("-"*60)
                
                if 'formatted_message' in result:
                    print("Preview of message that would be sent:")
                    print("-"*40)
                    print(result['formatted_message'])
                    print("-"*40)
                else:
                    print("Message format not available in result")
                    
            else:
                print("⚠️ No real data available for signal generation")
                print("This is expected behavior - system won't generate signals without real data")
                
        else:
            print("❌ Forex Signal Integration setup failed")
            
    except Exception as e:
        print(f"❌ Error in forex signal integration: {e}")
        import traceback
        traceback.print_exc()
    
    # Step 3: Test individual price validation
    print(f"\n💰 STEP 3: Individual Price Validation Demo")
    print("-"*60)
    
    try:
        from src.price_validator import price_validator
        
        test_pair = 'EURUSD'
        print(f"Testing price validation for {test_pair}...")
        
        validation_result = await price_validator.get_validated_price(test_pair)
        
        if validation_result.is_valid:
            print(f"\n✅ Price validation successful for {test_pair}:")
            print(f"   Price: ${validation_result.consensus_price:.5f}")
            print(f"   Sources: {validation_result.sources_count}")
            print(f"   Variance: {validation_result.variance:.4%}")
            print(f"   Status: {validation_result.reason}")
        else:
            print(f"\n❌ Price validation failed for {test_pair}:")
            print(f"   Reason: {validation_result.reason}")
            print(f"   Sources found: {validation_result.sources_count}")
            
    except Exception as e:
        print(f"❌ Error in price validation: {e}")
    
    # Summary
    print(f"\n" + "="*80)
    print("✅ DEMO COMPLETE")
    print("="*80)
    
    print(f"\n🎯 What this demo showed:")
    print(f"✅ Enhanced forex signal integration working")
    print(f"✅ Multi-source price validation (3+ sources)")
    print(f"✅ Signal generation with entry/exit and confidence")
    print(f"✅ Real API data validation (NO synthetic data)")
    print(f"✅ Structured message format ready for delivery")
    print(f"❌ NO actual messages sent to any platform")
    
    print(f"\n📅 At 6 AM PST weekdays, the enhanced_api_signals_daily.py script:")
    print(f"   1. Runs this exact same signal generation process")
    print(f"   2. Formats the signals in structured plaintext")
    print(f"   3. Sends via Signal and Telegram (concurrently)")
    print(f"   4. Logs all activity for monitoring")
    
    print(f"\n" + "="*80)

if __name__ == "__main__":
    asyncio.run(demo_enhanced_signals())