#!/usr/bin/env python3
import os
import sys
import shutil
import subprocess

def main():
    print("🧹 Starting automatic cleanup and fixes...")
    
    # 1. Remove duplicate chromium installation
    print("\n1. Removing duplicate chromium installation...")
    playwright_dup = "/home/ohms/.cache/ms-playwright/chromium_headless_shell-1169"
    if os.path.exists(playwright_dup):
        try:
            shutil.rmtree(playwright_dup)
            print(f"✓ Removed: {playwright_dup}")
        except Exception as e:
            print(f"✗ Could not remove {playwright_dup}: {e}")
    else:
        print("✓ Duplicate already removed")
    
    # 2. Complete Playwright installation
    print("\n2. Installing Playwright browsers...")
    try:
        os.chdir('/home/ohms/OhmsAlertsReports/daily-report')
        # Activate virtual environment and install
        result = subprocess.run([
            '/home/ohms/OhmsAlertsReports/daily-report/venv/bin/python', 
            '-m', 'playwright', 'install', 'chromium'
        ], capture_output=True, text=True, timeout=300)
        
        if result.returncode == 0:
            print("✓ Playwright chromium installed successfully")
        else:
            print(f"✗ Playwright install failed: {result.stderr}")
    except subprocess.TimeoutExpired:
        print("⚠️ Playwright install timed out, but may have completed")
    except Exception as e:
        print(f"✗ Playwright install error: {e}")
    
    # 3. Test basic functionality
    print("\n3. Testing system components...")
    
    # Test imports
    try:
        sys.path.insert(0, '/home/ohms/OhmsAlertsReports/daily-report')
        from main import DailyReportAutomation
        automation = DailyReportAutomation()
        print("✓ Main automation class loads successfully")
    except Exception as e:
        print(f"✗ Main automation import failed: {e}")
    
    # Check if scraper can be imported
    try:
        from real_only_mymama_scraper import RealOnlyMyMamaScraper
        scraper = RealOnlyMyMamaScraper()
        print("✓ Scraper class loads successfully")
    except Exception as e:
        print(f"✗ Scraper import failed: {e}")
    
    # 4. Check disk space after cleanup
    print("\n4. Checking disk space...")
    try:
        statvfs = os.statvfs('/tmp')
        total = statvfs.f_frsize * statvfs.f_blocks
        free = statvfs.f_frsize * statvfs.f_avail
        print(f"/tmp: {free / 1024**2:.1f} MB free of {total / 1024**2:.1f} MB")
        
        statvfs_root = os.statvfs('/')
        total_root = statvfs_root.f_frsize * statvfs_root.f_blocks
        free_root = statvfs_root.f_frsize * statvfs_root.f_avail
        print(f"Root: {free_root / 1024**3:.1f} GB free of {total_root / 1024**3:.1f} GB")
    except Exception as e:
        print(f"Could not check disk space: {e}")
    
    print("\n✨ Cleanup and fixes completed!")

if __name__ == "__main__":
    main()