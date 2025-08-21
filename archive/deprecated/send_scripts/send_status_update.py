#!/usr/bin/env python3
"""Send status update about MyMama data and heatmaps"""
import os
import requests
from datetime import datetime
from dotenv import load_dotenv

# Load environment
load_dotenv('.env')

def send_status_update():
    """Send status update to both platforms"""
    
    message = f"""📊 Daily Report Status - {datetime.now().strftime('%d %B %Y %H:%M')}

MyMama Alerts:
• Browser installation issue preventing live scraping
• Last successful scrape: Check previous messages
• To fix: Install Playwright browsers with sufficient disk space

Heatmaps:
• Heatmap generation requires manual setup
• Location: /home/ohms/OhmsAlertsReports/heatmaps_package/core_files
• Run: python3 bloomberg_report_final.py

System Status:
• Signal: ✅ Connected and verified
• Telegram: ✅ Connected and verified
• Automated reports: Scheduled for 6:00 AM PST weekdays

Next Steps:
1. Clear disk space or use alternative tmp directory
2. Run: playwright install chromium
3. Generate fresh heatmaps manually
4. System will resume normal operation tomorrow"""

    # Send to Telegram
    bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
    group_id = os.getenv('TELEGRAM_GROUP_ID')
    
    if bot_token and group_id:
        try:
            response = requests.post(
                f"https://api.telegram.org/bot{bot_token}/sendMessage",
                json={
                    'chat_id': group_id,
                    'text': message,
                    'parse_mode': 'Markdown'
                }
            )
            if response.status_code == 200:
                print("✅ Telegram: Status update sent")
        except Exception as e:
            print(f"❌ Telegram error: {e}")
    
    # Send to Signal
    api_url = os.getenv('SIGNAL_API_URL', 'http://localhost:8080')
    phone = os.getenv('SIGNAL_PHONE_NUMBER')
    group = os.getenv('SIGNAL_GROUP_ID')
    
    if phone and group:
        try:
            response = requests.post(
                f"{api_url}/v2/send",
                json={
                    "message": message,
                    "number": phone,
                    "recipients": [group]
                }
            )
            if response.status_code in [200, 201]:
                print("✅ Signal: Status update sent")
        except Exception as e:
            print(f"❌ Signal error: {e}")

if __name__ == "__main__":
    print("📤 Sending status update to both platforms...")
    send_status_update()
    print("✅ Done")