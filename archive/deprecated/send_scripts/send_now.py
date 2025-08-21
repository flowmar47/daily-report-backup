#!/usr/bin/env python3
import asyncio
import sys
from pathlib import Path
from datetime import datetime

sys.path.append(str(Path('.') / 'src'))

async def send_reports_now():
    print(f"Sending live financial reports - {datetime.now()}")
    
    # Import components
    from main import DailyReportAutomation
    
    # Create automation instance
    automation = DailyReportAutomation()
    
    # Collect live data
    print("Collecting live financial data...")
    forex_data = await automation.collect_market_data()
    
    if forex_data and forex_data.get('has_real_data'):
        print("Real data found - sending to all platforms...")
        success = await automation.send_structured_financial_data(forex_data)
        if success:
            print("SUCCESS: Reports sent to Signal + Telegram + WhatsApp!")
        else:
            print("FAILED: Could not send reports")
    else:
        print("No real financial data available today")
    
    # Generate and send heatmaps
    print("Generating heatmaps...")
    heatmap_data = await automation.generate_heatmaps()
    if heatmap_data:
        print("Sending heatmaps to all platforms...")
        heatmap_success = await automation.send_heatmap_images(heatmap_data)
        if heatmap_success:
            print("SUCCESS: Heatmaps sent!")
        else:
            print("FAILED: Could not send heatmaps")
    
    # Cleanup
    await automation.cleanup_browser()
    print("COMPLETED: Live reports delivered!")

if __name__ == "__main__":
    asyncio.run(send_reports_now())