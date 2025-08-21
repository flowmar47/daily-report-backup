#!/usr/bin/env python3
"""Send real MyMama data and fresh heatmaps only"""
import os
import sys
import subprocess
from datetime import datetime
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

def main():
    print("🚀 Sending Real Data Only")
    print(f"📅 Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 50)
    
    # First, try to run the main daily report system
    print("\n📊 Task 1: Real MyMama Data")
    print("=" * 50)
    print("Running main daily report system...")
    
    result = subprocess.run(
        [sys.executable, "test_complete_fixed_system.py"],
        capture_output=True,
        text=True,
        cwd="/home/ohms/OhmsAlertsReports/daily-report"
    )
    
    if result.returncode == 0:
        print("✅ Real MyMama data scraped and sent")
        print(result.stdout[-500:] if result.stdout else "")  # Last 500 chars
    else:
        print("❌ Failed to scrape MyMama data")
        if "Playwright" in str(result.stderr):
            print("⚠️ Browser not installed. The system already sent a 'no data available' message.")
        else:
            print(result.stderr[-500:] if result.stderr else "")
    
    # Second, generate fresh heatmaps
    print("\n📊 Task 2: Fresh Heatmaps")
    print("=" * 50)
    print("Generating new heatmaps...")
    
    # Try to generate using the main system's heatmap generator
    heatmap_result = subprocess.run(
        [sys.executable, "main.py", "--heatmaps-only"],
        capture_output=True,
        text=True,
        cwd="/home/ohms/OhmsAlertsReports/daily-report"
    )
    
    if heatmap_result.returncode != 0:
        # Try the standalone heatmap generator
        print("Trying standalone heatmap generator...")
        
        # Check if we can access the heatmaps package
        heatmaps_path = Path("/home/ohms/OhmsAlertsReports/heatmaps_package/core_files")
        if heatmaps_path.exists():
            print(f"Note: To generate heatmaps, you need to:")
            print(f"1. cd {heatmaps_path}")
            print(f"2. Install dependencies: pip3 install pandas matplotlib numpy requests python-dotenv")
            print(f"3. Run: python3 bloomberg_report_final.py")
            print(f"4. Or use silent mode: python3 silent_bloomberg_system.py")
        else:
            print("❌ Heatmaps package not found")
    else:
        print("✅ Heatmaps generated (if data was available)")
    
    print("\n" + "=" * 50)
    print("Summary:")
    print("- MyMama: Check Signal/Telegram for any messages sent")
    print("- Heatmaps: Manual generation may be required")
    print("=" * 50)

if __name__ == "__main__":
    main()