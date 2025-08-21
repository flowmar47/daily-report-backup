#!/usr/bin/env python3
"""
Manually send today's financial report
Collects real data from MyMama.uk and sends to all platforms
"""

import asyncio
import os
import sys
from pathlib import Path
from datetime import datetime

# Add parent directory to path
sys.path.append(str(Path(__file__).parent))

from main import DailyReportAutomation

async def send_manual_report():
    """Run the daily report manually"""
    print(f"📊 Manual Financial Report - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    print("Collecting real financial data from MyMama.uk...")
    print("This will only send if real data is available.\n")
    
    try:
        # Initialize the automation
        automation = DailyReportAutomation()
        
        # Run the daily report
        await automation.run_daily_report()
        
        print("\n✅ Manual report process completed")
        return True
        
    except Exception as e:
        print(f"\n❌ Error running manual report: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """Main entry point"""
    success = await send_manual_report()
    if not success:
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())