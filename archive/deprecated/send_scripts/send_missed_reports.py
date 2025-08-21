#!/usr/bin/env python3
"""Send missed reports (MyMama data and heatmaps) to Signal and Telegram"""
import asyncio
import os
import sys
from datetime import datetime
from pathlib import Path
import subprocess
import requests
from dotenv import load_dotenv

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

# Load environment
load_dotenv('.env')

async def send_mymama_report():
    """Scrape and send MyMama report using the working method"""
    try:
        print("📊 Task 1: MyMama Report")
        print("=" * 50)
        
        # Use the working send_to_both_messengers.py script
        print("🔍 Running MyMama scraper and sending to both platforms...")
        result = subprocess.run(
            [sys.executable, "send_to_both_messengers.py"],
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            print("✅ MyMama report sent successfully")
            if result.stdout:
                print(result.stdout)
            return True
        else:
            print("❌ MyMama report failed")
            if result.stderr:
                print(result.stderr)
            return False
            
    except Exception as e:
        print(f"❌ Error in MyMama report: {e}")
        return False

async def send_heatmaps():
    """Generate and send financial heatmaps"""
    try:
        print("\n📊 Task 2: Financial Heatmaps")
        print("=" * 50)
        
        # Change to heatmaps directory
        heatmaps_dir = Path("/home/ohms/OhmsAlertsReports/heatmaps_package/core_files")
        original_dir = os.getcwd()
        os.chdir(heatmaps_dir)
        
        # Generate heatmaps
        print("🎨 Generating financial heatmaps...")
        result = subprocess.run(
            [sys.executable, "silent_bloomberg_system.py"],
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            print("✅ Heatmaps generated successfully")
            
            # Find generated PNG files (modified in last 5 minutes)
            import time
            current_time = time.time()
            png_files = []
            
            for file in heatmaps_dir.glob("*.png"):
                if current_time - file.stat().st_mtime < 300:  # 5 minutes
                    png_files.append(file)
            
            if png_files:
                print(f"📎 Found {len(png_files)} heatmap files: {[f.name for f in png_files]}")
                
                # Send to Telegram
                bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
                group_id = os.getenv('TELEGRAM_GROUP_ID')
                
                if bot_token and group_id:
                    caption = f"📊 Financial Heatmaps - {datetime.now().strftime('%d %B %Y')}\n\nInterest rate differentials and currency analysis"
                    
                    for i, png_file in enumerate(png_files):
                        print(f"\n📤 Sending {png_file.name} to Telegram...")
                        
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
                            else:
                                print(f"❌ Telegram: Failed to send {png_file.name}")
                
                # Send notification to Signal
                signal_api = os.getenv('SIGNAL_API_URL', 'http://localhost:8080')
                signal_phone = os.getenv('SIGNAL_PHONE_NUMBER')
                signal_group = os.getenv('SIGNAL_GROUP_ID')
                
                if signal_phone and signal_group:
                    print("\n📤 Sending heatmap notification to Signal...")
                    
                    files_info = "\n".join([f"- {png.name}" for png in png_files])
                    message = f"{caption}\n\nGenerated heatmap files:\n{files_info}"
                    
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
                    else:
                        print("❌ Signal: Failed to send notification")
                
                return True
            else:
                print("❌ No heatmap files found")
                return False
        else:
            print(f"❌ Heatmap generation failed")
            if result.stderr:
                print(result.stderr)
            return False
            
    except Exception as e:
        print(f"❌ Error in heatmaps: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        # Return to original directory
        os.chdir(original_dir)

async def main():
    """Main function to send all missed reports"""
    print("🚀 Sending Missed Daily Reports")
    print(f"📅 Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 50)
    
    # Send MyMama report
    mymama_success = await send_mymama_report()
    
    # Send heatmaps
    heatmap_success = await send_heatmaps()
    
    print("\n" + "=" * 50)
    print("📊 Summary:")
    print(f"  - MyMama Report: {'✅ Sent' if mymama_success else '❌ Failed'}")
    print(f"  - Heatmaps: {'✅ Sent' if heatmap_success else '❌ Failed'}")
    print("=" * 50)

if __name__ == "__main__":
    asyncio.run(main())