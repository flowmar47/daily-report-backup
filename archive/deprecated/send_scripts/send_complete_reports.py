#!/usr/bin/env python3
"""Send complete reports - MyMama data and heatmaps to Signal and Telegram"""
import asyncio
import os
import sys
from datetime import datetime
from pathlib import Path
import requests
from dotenv import load_dotenv

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

# Load environment
load_dotenv('.env')

# Import the working scraper
from real_only_mymama_scraper import RealOnlyMyMamaScraper

async def send_to_telegram(message):
    """Send message to Telegram"""
    bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
    group_id = os.getenv('TELEGRAM_GROUP_ID')
    
    if not bot_token or not group_id:
        print("❌ Missing Telegram credentials")
        return False
        
    try:
        import aiohttp
        url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        
        payload = {
            'chat_id': group_id,
            'text': message,
            'parse_mode': 'Markdown',
            'disable_web_page_preview': True
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload) as response:
                if response.status == 200:
                    print("✅ Telegram: Message sent")
                    return True
                else:
                    print(f"❌ Telegram: Failed ({response.status})")
                    return False
    except Exception as e:
        print(f"❌ Telegram error: {e}")
        return False

def send_to_signal(message):
    """Send message to Signal"""
    api_url = os.getenv('SIGNAL_API_URL', 'http://localhost:8080')
    phone = os.getenv('SIGNAL_PHONE_NUMBER')
    group = os.getenv('SIGNAL_GROUP_ID')
    
    if not phone or not group:
        print("❌ Missing Signal credentials")
        return False
        
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
            print("✅ Signal: Message sent")
            return True
        else:
            print(f"❌ Signal: Failed ({response.status_code})")
            return False
    except Exception as e:
        print(f"❌ Signal error: {e}")
        return False

def format_message(alerts_data):
    """Format MyMama alerts data"""
    timestamp = datetime.now().strftime("%d %B %Y")
    
    if not alerts_data.get('forex') and not alerts_data.get('options') and not alerts_data.get('earnings'):
        return f"""MYMAMA FOREX ALERTS - {timestamp}

No trading alerts available at this time.

The MyMama platform currently has no active forex, options, or earnings data.
Next check scheduled for tomorrow at 6:00 AM PST."""
    
    message = f"MYMAMA FOREX ALERTS - {timestamp}\n\n"
    
    # Add forex section
    if alerts_data.get('forex'):
        message += "FOREX SIGNALS:\n"
        for item in alerts_data['forex']:
            message += f"• {item}\n"
        message += "\n"
    
    # Add options section
    if alerts_data.get('options'):
        message += "OPTIONS TRADES:\n"
        for item in alerts_data['options']:
            message += f"• {item}\n"
        message += "\n"
    
    # Add earnings section
    if alerts_data.get('earnings'):
        message += "EARNINGS THIS WEEK:\n"
        for item in alerts_data['earnings']:
            message += f"• {item}\n"
        message += "\n"
    
    return message.strip()

async def send_mymama_report():
    """Send MyMama report to both platforms"""
    print("📊 Task 1: MyMama Report")
    print("=" * 50)
    
    try:
        # Get real alerts
        print("🔍 Scraping MyMama data...")
        scraper = RealOnlyMyMamaScraper()
        alerts_data = await scraper.get_real_alerts_only()
        
        # Format message
        message = format_message(alerts_data)
        
        # Send to both platforms
        print("📤 Sending to Signal and Telegram...")
        
        # Send to Telegram
        tg_success = await send_to_telegram(message)
        
        # Send to Signal
        sig_success = send_to_signal(message)
        
        return tg_success or sig_success
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

async def send_heatmaps():
    """Send pre-generated heatmaps if available"""
    print("\n📊 Task 2: Financial Heatmaps")
    print("=" * 50)
    
    try:
        # Look for any PNG files in heatmaps directory
        heatmaps_dir = Path("/home/ohms/OhmsAlertsReports/heatmaps_package/core_files")
        png_files = list(heatmaps_dir.glob("*.png"))
        
        if not png_files:
            print("⚠️ No heatmap files found")
            print("To generate heatmaps, run:")
            print("cd /home/ohms/OhmsAlertsReports/heatmaps_package/core_files")
            print("python3 bloomberg_report_final.py")
            return False
        
        # Sort by modification time and take most recent
        png_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
        recent_files = png_files[:2]  # Take up to 2 most recent
        
        print(f"📎 Found {len(recent_files)} heatmap files")
        
        # Send to Telegram with images
        bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
        group_id = os.getenv('TELEGRAM_GROUP_ID')
        
        if bot_token and group_id:
            caption = f"📊 Financial Heatmaps - {datetime.now().strftime('%d %B %Y')}"
            
            for i, png_file in enumerate(recent_files):
                print(f"📤 Sending {png_file.name} to Telegram...")
                
                with open(png_file, 'rb') as photo:
                    files = {'photo': photo}
                    data = {
                        'chat_id': group_id,
                        'caption': caption if i == 0 else None
                    }
                    
                    response = requests.post(
                        f"https://api.telegram.org/bot{bot_token}/sendPhoto",
                        files=files,
                        data=data
                    )
                    
                    if response.status_code == 200:
                        print(f"✅ Telegram: {png_file.name} sent")
        
        # Send notification to Signal
        files_info = "\n".join([f"- {f.name}" for f in recent_files])
        signal_msg = f"📊 Financial Heatmaps - {datetime.now().strftime('%d %B %Y')}\n\nHeatmap files generated:\n{files_info}"
        send_to_signal(signal_msg)
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

async def main():
    """Main function"""
    print("🚀 Sending Complete Daily Reports")
    print(f"📅 Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 50)
    
    # Send MyMama report
    mymama_success = await send_mymama_report()
    
    # Send heatmaps
    heatmap_success = await send_heatmaps()
    
    print("\n" + "=" * 50)
    print("📊 Summary:")
    print(f"  - MyMama Report: {'✅ Sent' if mymama_success else '❌ Failed'}")
    print(f"  - Heatmaps: {'✅ Sent' if heatmap_success else '❌ Failed/Not Found'}")
    print("=" * 50)

if __name__ == "__main__":
    asyncio.run(main())