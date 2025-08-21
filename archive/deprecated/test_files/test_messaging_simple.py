#!/usr/bin/env python3
"""Quick test of Signal and Telegram messaging"""

import asyncio
import sys
from pathlib import Path

sys.path.append(str(Path('.') / 'src'))

async def test_messaging():
    """Test messaging on Signal and Telegram only"""
    from main import DailyReportAutomation
    
    automation = DailyReportAutomation()
    
    # Use existing data from today's collection
    data_file = Path('output/enhanced_browserbase/enhanced_browserbase_data_20250703_092053.json')
    if data_file.exists():
        import json
        with open(data_file) as f:
            forex_data = json.load(f)['data']
        
        print("Using existing scraped data for test...")
        
        # Generate formatted message
        formatted_message = await automation.generate_report(forex_data)
        print(f"Message preview: {formatted_message[:200]}...")
        
        # Test only Signal and Telegram
        from src.messengers.unified_messenger import UnifiedMultiMessenger
        
        platforms = ['telegram', 'signal']
        multi_messenger = UnifiedMultiMessenger(platforms)
        
        # Send to both platforms
        results = await multi_messenger.send_structured_financial_data(formatted_message)
        
        # Check results
        for platform, result in results.items():
            if result.success:
                print(f"✅ {platform.upper()}: SUCCESS")
            else:
                print(f"❌ {platform.upper()}: FAILED - {result.error}")
        
        await multi_messenger.cleanup()
    else:
        print("No data file found for testing")

if __name__ == "__main__":
    asyncio.run(test_messaging())