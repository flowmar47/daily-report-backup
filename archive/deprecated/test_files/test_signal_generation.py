#!/usr/bin/env python3
"""
Test the Forex Signal Generation System
"""

import asyncio
import logging
import json
from datetime import datetime

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def test_signal_generation():
    """Test the signal generation system"""
    logger.info("🧪 Testing Forex Signal Generation System...")
    
    try:
        # Import the integration module
        from forex_signal_integration import forex_signal_integration
        
        if not forex_signal_integration or not forex_signal_integration.setup_successful:
            logger.error("❌ Integration not properly initialized")
            return False
        
        # Test signal generation
        logger.info("📊 Generating forex signals...")
        signals_data = await forex_signal_integration.generate_forex_signals()
        
        # Check results
        if signals_data.get('error'):
            logger.error(f"❌ Error generating signals: {signals_data['error']}")
            return False
        
        # Display results
        logger.info(f"✅ Signal generation successful!")
        logger.info(f"   Total pairs analyzed: {signals_data.get('total_signals', 0)}")
        logger.info(f"   Active signals: {signals_data.get('active_signals', 0)}")
        logger.info(f"   Hold recommendations: {signals_data.get('hold_signals', 0)}")
        
        # Show active signals
        for alert in signals_data.get('forex_alerts', []):
            logger.info(f"   📈 {alert['pair']}: {alert['mt4_action']} @ {alert.get('entry_price', 'N/A')}")
            if alert.get('confidence'):
                logger.info(f"      Confidence: {alert['confidence']:.1%}")
            if alert.get('target_pips'):
                logger.info(f"      Target: {alert['target_pips']:.0f} pips")
        
        # Test plaintext formatting
        logger.info("\n📄 Testing plaintext formatting...")
        formatted_text = forex_signal_integration.format_signals_for_plaintext(signals_data)
        
        # Display first part of formatted text
        logger.info("Formatted output (first 500 chars):")
        print(formatted_text[:500])
        
        # Save to file for review
        output_file = f"test_signals_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        with open(output_file, 'w') as f:
            f.write(formatted_text)
        logger.info(f"💾 Full output saved to: {output_file}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """Main test function"""
    success = await test_signal_generation()
    if success:
        logger.info("✅ All tests passed!")
    else:
        logger.error("❌ Tests failed")
    
    return success

if __name__ == "__main__":
    result = asyncio.run(main())
    exit(0 if result else 1)