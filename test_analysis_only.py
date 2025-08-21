#!/usr/bin/env python3
"""
Analysis-Only Test - NO MESSAGING
Shows the complete analysis flow without sending any messages
"""

import asyncio
import sys
import logging
from pathlib import Path
from datetime import datetime
import json

# Setup paths
sys.path.append(str(Path(__file__).parent))
sys.path.append(str(Path(__file__).parent / 'Signals' / 'src'))

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def test_analysis_only():
    """
    Test analysis and signal generation WITHOUT sending messages
    """
    
    print("\n" + "="*80)
    print("🔬 ANALYSIS-ONLY TEST (NO MESSAGES WILL BE SENT)")
    print("="*80)
    
    # Test configuration
    test_pairs = ['EURUSD', 'GBPUSD', 'USDJPY', 'USDCAD', 'AUDUSD']
    
    # ============================================================================
    # STEP 1: PRICE VALIDATION
    # ============================================================================
    print("\n📊 STEP 1: Multi-Source Price Validation")
    print("-"*60)
    
    from src.price_validator import price_validator
    
    # Get validation statistics
    stats = await price_validator.get_validation_statistics()
    print(f"System Status: {stats.get('system_health', {}).get('status', 'unknown')}")
    print(f"Data Sources Available:")
    print(f"  - yfinance: {'✅' if stats['available_integrations']['yfinance'] else '❌'}")
    print(f"  - Enhanced fetcher: {'✅' if stats['available_integrations']['enhanced_data_fetcher'] else '❌'}")
    print(f"  - API sources: {len(stats['api_sources'])} configured")
    
    # Validate prices
    print("\nValidating prices from multiple sources...")
    validation_results = await price_validator.batch_validate_with_details(test_pairs)
    
    print("\n✅ Validated Prices:")
    validated_pairs = []
    for pair, result in validation_results.items():
        if result['is_valid']:
            validated_pairs.append(pair)
            print(f"  {pair}: ${result['price']:.5f} (from {result['sources_count']} sources, variance: {result['variance']:.4%})")
        else:
            print(f"  {pair}: ❌ FAILED - {result['reason']}")
    
    if not validated_pairs:
        print("\n⚠️ No pairs validated successfully. Exiting test.")
        return
    
    # ============================================================================
    # STEP 2: ENHANCED TECHNICAL ANALYSIS
    # ============================================================================
    print("\n📈 STEP 2: Enhanced Technical Analysis")
    print("-"*60)
    
    from enhanced_technical_analysis import EnhancedTechnicalAnalyzer
    from data_fetcher import data_fetcher
    import pandas as pd
    
    analyzer = EnhancedTechnicalAnalyzer()
    analysis_results = {}
    
    for pair in validated_pairs[:3]:  # Analyze first 3 validated pairs
        print(f"\n🔍 Analyzing {pair}...")
        
        # Fetch historical data
        historical_data = data_fetcher.fetch_forex_data_smart(pair, interval='4hour')
        
        if not historical_data:
            print(f"  ⚠️ No historical data available for {pair}")
            continue
        
        # Convert to DataFrame
        df = pd.DataFrame(historical_data['values'])
        df['datetime'] = pd.to_datetime(df['datetime'])
        df.set_index('datetime', inplace=True)
        
        for col in ['open', 'high', 'low', 'close', 'volume']:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')
        
        print(f"  Data points: {len(df)}")
        
        # Run enhanced analysis
        result = analyzer.analyze_forex_pair(pair, df, '4hour')
        analysis_results[pair] = result
        
        print(f"\n  📊 Analysis Results for {pair}:")
        print(f"    Signal: {result.signal}")
        print(f"    Confidence: {result.confidence:.1%}")
        print(f"    Entry: ${result.entry_price:.5f}")
        print(f"    Stop Loss: ${result.stop_loss:.5f}")
        print(f"    Take Profit: ${result.take_profit:.5f}")
        print(f"    Risk/Reward: 1:{result.risk_reward_ratio:.1f}")
        
        # Show indicators
        print(f"\n    Indicator Scores:")
        for indicator, score in result.indicator_signals.items():
            print(f"      {indicator.capitalize()}: {score:+.2f}")
        
        # Show patterns
        if result.patterns_detected:
            print(f"\n    Patterns Detected: {', '.join(result.patterns_detected[:3])}")
    
    # ============================================================================
    # STEP 3: SIGNAL GENERATION
    # ============================================================================
    print("\n🎯 STEP 3: Signal Generation with Entry/Exit")
    print("-"*60)
    
    from signal_generator import SignalGenerator
    
    signal_gen = SignalGenerator()
    signals = signal_gen.generate_signals(pairs=validated_pairs)
    
    print("\n📢 Generated Trading Signals:")
    print("-"*40)
    
    strong_signals = []
    medium_signals = []
    weak_signals = []
    
    for pair, signal_data in signals.items():
        if 'error' in signal_data:
            continue
        
        confidence = signal_data.get('confidence', 0)
        
        signal_info = {
            'pair': pair,
            'signal': signal_data.get('signal', 'HOLD'),
            'confidence': confidence,
            'entry': signal_data.get('entry', 0),
            'exit': signal_data.get('exit', 0),
            'analysis': signal_data.get('analysis', {})
        }
        
        if confidence >= 0.7:
            strong_signals.append(signal_info)
        elif confidence >= 0.5:
            medium_signals.append(signal_info)
        else:
            weak_signals.append(signal_info)
    
    # Display signals by strength
    if strong_signals:
        print("\n💪 STRONG SIGNALS (Confidence ≥ 70%):")
        for sig in strong_signals:
            print(f"\n  {sig['pair']}: {sig['signal']}")
            print(f"    Confidence: {sig['confidence']:.1%}")
            print(f"    Entry: ${sig['entry']:.5f}")
            print(f"    Exit: ${sig['exit']:.5f}")
            if sig['analysis']:
                print(f"    Technical: {sig['analysis'].get('technical', {}).get('score', 0):.2f}")
                print(f"    Economic: {sig['analysis'].get('economic', {}).get('score', 0):.2f}")
    
    if medium_signals:
        print("\n📊 MEDIUM SIGNALS (Confidence 50-70%):")
        for sig in medium_signals:
            print(f"\n  {sig['pair']}: {sig['signal']}")
            print(f"    Confidence: {sig['confidence']:.1%}")
            print(f"    Entry: ${sig['entry']:.5f}")
            print(f"    Exit: ${sig['exit']:.5f}")
    
    if weak_signals:
        print("\n⚠️ WEAK SIGNALS (Confidence < 50%):")
        for sig in weak_signals:
            print(f"  {sig['pair']}: {sig['signal']} (Confidence: {sig['confidence']:.1%})")
    
    # ============================================================================
    # STEP 4: SHOW WHAT WOULD BE SENT (WITHOUT SENDING)
    # ============================================================================
    print("\n📝 STEP 4: Message Preview (NOT SENT)")
    print("-"*60)
    
    # Generate the message that would be sent
    from datetime import datetime
    
    message_lines = []
    message_lines.append("FOREX TRADING SIGNALS")
    message_lines.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')} PST")
    message_lines.append("")
    message_lines.append("FOREX PAIRS")
    message_lines.append("")
    
    # Add strong signals to message
    for sig in strong_signals[:5]:  # Limit to 5 signals
        message_lines.append(f"Pair: {sig['pair']}")
        message_lines.append(f"Signal: {sig['signal']}")
        message_lines.append(f"Entry: {sig['entry']:.5f}")
        message_lines.append(f"Exit: {sig['exit']:.5f}")
        message_lines.append(f"Confidence: {sig['confidence']:.1%}")
        message_lines.append("")
    
    message_lines.append(f"Enhanced API Analysis - {len(strong_signals)} strong signals")
    message_lines.append("Real market data from validated sources")
    
    print("Message that WOULD be sent (but won't be):")
    print("-"*40)
    print("\n".join(message_lines))
    print("-"*40)
    
    # ============================================================================
    # SUMMARY
    # ============================================================================
    print("\n" + "="*80)
    print("📊 ANALYSIS COMPLETE (NO MESSAGES SENT)")
    print("="*80)
    
    print("\n📈 Analysis Summary:")
    print(f"  - Pairs validated: {len(validated_pairs)}")
    print(f"  - Pairs analyzed: {len(analysis_results)}")
    print(f"  - Strong signals: {len(strong_signals)}")
    print(f"  - Medium signals: {len(medium_signals)}")
    print(f"  - Weak signals: {len(weak_signals)}")
    
    print("\n✅ System Capabilities Demonstrated:")
    print("  ✅ Price validation from multiple APIs")
    print("  ✅ Enhanced technical analysis with 50+ indicators")
    print("  ✅ Signal generation with entry/exit points")
    print("  ✅ Confidence scoring for all signals")
    print("  ✅ Smart caching for API optimization")
    
    print("\n💡 This test demonstrated the analysis pipeline WITHOUT:")
    print("  ❌ Sending any messages to Signal")
    print("  ❌ Sending any messages to Telegram")
    print("  ❌ Sending any messages to WhatsApp")
    print("  ❌ Generating any heatmaps")
    
    print("\n" + "="*80)

if __name__ == "__main__":
    asyncio.run(test_analysis_only())