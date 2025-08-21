#!/usr/bin/env python3
"""Send existing heatmaps to Signal and Telegram"""
import os
import requests
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

# Load environment
load_dotenv('.env')

def send_heatmaps():
    """Send the most recent heatmaps"""
    print("📊 Sending Financial Heatmaps")
    print("=" * 50)
    
    # Find most recent heatmap files
    heatmap_dirs = [
        Path("/home/ohms/OhmsAlertsReports/src/heatmaps/reports"),
        Path("/home/ohms/OhmsAlertsReports/src/heatmaps/test_reports"),
        Path("/home/ohms/OhmsAlertsReports/heatmaps_package/core_files")
    ]
    
    all_pngs = []
    for dir_path in heatmap_dirs:
        if dir_path.exists():
            all_pngs.extend(list(dir_path.glob("**/*.png")))
    
    if not all_pngs:
        print("❌ No heatmap files found")
        return False
    
    # Sort by modification time and get most recent
    all_pngs.sort(key=lambda x: x.stat().st_mtime, reverse=True)
    
    # Get the two most recent different types (categorical and forex)
    categorical = None
    forex = None
    
    for png in all_pngs:
        name_lower = png.name.lower()
        if 'categorical' in name_lower and not categorical:
            categorical = png
        elif ('forex' in name_lower or 'pairs' in name_lower) and not forex:
            forex = png
        
        if categorical and forex:
            break
    
    files_to_send = []
    if categorical:
        files_to_send.append(categorical)
    if forex:
        files_to_send.append(forex)
    
    if not files_to_send:
        # Just take the two most recent
        files_to_send = all_pngs[:2]
    
    print(f"📎 Found {len(files_to_send)} heatmap files:")
    for f in files_to_send:
        print(f"  - {f.name}")
    
    # Send to Telegram
    bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
    group_id = os.getenv('TELEGRAM_GROUP_ID')
    
    success = False
    
    if bot_token and group_id:
        caption = f"📊 Financial Heatmaps - {datetime.now().strftime('%d %B %Y')}\n\nInterest rate differentials and currency analysis"
        
        for i, png_file in enumerate(files_to_send):
            print(f"\n📤 Sending {png_file.name} to Telegram...")
            
            try:
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
                        success = True
                    else:
                        print(f"❌ Telegram: Failed to send {png_file.name} - {response.text}")
            except Exception as e:
                print(f"❌ Error sending to Telegram: {e}")
    
    # Send notification to Signal
    signal_api = os.getenv('SIGNAL_API_URL', 'http://localhost:8080')
    signal_phone = os.getenv('SIGNAL_PHONE_NUMBER')
    signal_group = os.getenv('SIGNAL_GROUP_ID')
    
    if signal_phone and signal_group:
        print("\n📤 Sending heatmap notification to Signal...")
        
        files_info = "\n".join([f"- {f.name}" for f in files_to_send])
        message = f"📊 Financial Heatmaps - {datetime.now().strftime('%d %B %Y')}\n\nInterest rate differentials and currency analysis\n\nFiles:\n{files_info}"
        
        try:
            response = requests.post(
                f"{signal_api}/v2/send",
                json={
                    "message": message,
                    "number": signal_phone,
                    "recipients": [signal_group]
                }
            )
            
            if response.status_code in [200, 201]:
                print("✅ Signal: Heatmap notification sent")
                success = True
            else:
                print(f"❌ Signal: Failed - {response.text}")
        except Exception as e:
            print(f"❌ Error sending to Signal: {e}")
    
    return success

if __name__ == "__main__":
    success = send_heatmaps()
    print("\n" + "=" * 50)
    print(f"Result: {'✅ Heatmaps sent' if success else '❌ Failed to send'}")