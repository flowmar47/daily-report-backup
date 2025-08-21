#!/usr/bin/env python3
"""Fix environment and run fresh data collection"""
import os
import sys
import subprocess
import tempfile
import shutil
from pathlib import Path

def main():
    print("🔧 Step 1: Fixing environment issues")
    print("=" * 50)
    
    # Ensure tmp directories exist
    tmp_dirs = ['/tmp', '/var/tmp', '/home/ohms/tmp']
    for tmp_dir in tmp_dirs:
        try:
            os.makedirs(tmp_dir, exist_ok=True)
            os.chmod(tmp_dir, 0o1777)
            print(f"✅ Ensured {tmp_dir} exists")
        except Exception as e:
            print(f"⚠️ Could not create {tmp_dir}: {e}")
    
    # Set TMPDIR to a working location
    os.environ['TMPDIR'] = '/home/ohms/tmp'
    os.environ['TEMP'] = '/home/ohms/tmp'
    os.environ['TMP'] = '/home/ohms/tmp'
    
    print("\n🔧 Step 2: Installing Playwright browsers")
    print("=" * 50)
    
    # Change to project directory
    os.chdir('/home/ohms/OhmsAlertsReports/daily-report')
    
    # Activate virtual environment
    venv_path = Path('venv')
    if venv_path.exists():
        # Add venv to Python path
        site_packages = venv_path / 'lib' / 'python3.11' / 'site-packages'
        if site_packages.exists():
            sys.path.insert(0, str(site_packages))
        
        # Install Playwright browsers
        playwright_cmd = str(venv_path / 'bin' / 'playwright')
        
        print("Installing Chromium browser...")
        try:
            result = subprocess.run(
                [playwright_cmd, 'install', 'chromium'],
                capture_output=True,
                text=True,
                env={**os.environ, 'PLAYWRIGHT_BROWSERS_PATH': '/home/ohms/.cache/ms-playwright'}
            )
            
            if result.returncode == 0:
                print("✅ Playwright Chromium installed successfully")
            else:
                print(f"❌ Failed to install Playwright: {result.stderr}")
                # Try alternative installation
                print("Trying alternative installation method...")
                subprocess.run([sys.executable, '-m', 'playwright', 'install', 'chromium'])
        except Exception as e:
            print(f"❌ Error installing Playwright: {e}")
    
    print("\n🔧 Step 3: Running fresh data collection")
    print("=" * 50)
    
    # Import and run the scraper
    try:
        # Add project to path
        sys.path.insert(0, '/home/ohms/OhmsAlertsReports/daily-report')
        
        # Run the real-only scraper
        print("Starting MyMama data collection...")
        from real_only_mymama_scraper import RealOnlyMyMamaScraper
        import asyncio
        
        async def scrape_and_send():
            scraper = RealOnlyMyMamaScraper()
            alerts_data = await scraper.get_real_alerts_only()
            
            if alerts_data.get('has_real_data'):
                print("✅ Fresh data collected successfully!")
                
                # Send to both platforms
                from send_complete_reports import send_to_telegram, send_to_signal, format_message
                
                message = format_message(alerts_data)
                
                # Send to Telegram
                await send_to_telegram(message)
                
                # Send to Signal  
                send_to_signal(message)
                
                print("✅ Fresh data sent to both Signal and Telegram")
            else:
                print("⚠️ No fresh data available on MyMama")
                print(f"Reason: {alerts_data.get('message', 'Unknown')}")
        
        # Run the async function
        asyncio.run(scrape_and_send())
        
    except Exception as e:
        print(f"❌ Error during data collection: {e}")
        import traceback
        traceback.print_exc()
    
    # Generate fresh heatmaps
    print("\n🔧 Bonus: Attempting to generate fresh heatmaps")
    print("=" * 50)
    
    heatmap_dir = Path('/home/ohms/OhmsAlertsReports/heatmaps_package/core_files')
    if heatmap_dir.exists():
        print(f"To generate heatmaps manually:")
        print(f"1. cd {heatmap_dir}")
        print(f"2. python3 -m pip install pandas matplotlib numpy requests python-dotenv")
        print(f"3. python3 bloomberg_report_final.py")
    
    print("\n✅ Process complete!")

if __name__ == "__main__":
    main()