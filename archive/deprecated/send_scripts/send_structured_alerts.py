#!/usr/bin/env python3
"""
Send Structured MyMama Alerts to Telegram Group
This script uses the structured JSON format for real alerts data
"""

import asyncio
import sys
from pathlib import Path

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

async def send_alerts_now():
    """Send current structured alerts to Telegram group immediately"""
    
    from structured_alerts_system import StructuredAlertsSystem
    
    print("🚀 Sending structured MyMama alerts to Telegram group...")
    
    # Initialize the system
    alerts_system = StructuredAlertsSystem()
    
    # Get current alerts data
    alerts_data = await alerts_system.get_current_alerts()
    
    # Send to Telegram
    success = await alerts_system.send_to_telegram(alerts_data)
    
    if success:
        print("✅ Structured alerts sent successfully!")
        
        # Show summary
        forex_count = len(alerts_data.get('forex_signals', {}))
        options_count = len(alerts_data.get('options_data', []))
        source = alerts_data.get('metadata', {}).get('source', 'Unknown')
        
        print(f"📊 Sent {forex_count} forex signals and {options_count} options plays")
        print(f"📋 Data source: {source}")
    else:
        print("❌ Failed to send alerts")
    
    return success

if __name__ == "__main__":
    asyncio.run(send_alerts_now())