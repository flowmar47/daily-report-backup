#!/usr/bin/env python3
"""
Test script to run Bloomberg heatmap generation from daily-report directory
"""

import os
import sys
import subprocess
from pathlib import Path

def test_bloomberg_heatmap():
    """Test Bloomberg heatmap generation"""
    
    # Path to the heatmaps core files directory
    heatmaps_dir = Path(__file__).parent.parent / "heatmaps_package" / "core_files"
    
    print(f"Testing Bloomberg heatmap generation...")
    print(f"Heatmaps directory: {heatmaps_dir}")
    print(f"Directory exists: {heatmaps_dir.exists()}")
    
    # Check if database exists
    db_path = heatmaps_dir / "interest_rates.db"
    print(f"Database path: {db_path}")
    print(f"Database exists: {db_path.exists()}")
    
    # Change to the heatmaps directory and run the script
    original_dir = os.getcwd()
    
    try:
        os.chdir(heatmaps_dir)
        print(f"Changed to directory: {os.getcwd()}")
        
        # Run the Bloomberg script
        result = subprocess.run([
            sys.executable, "bloomberg_report_final.py"
        ], capture_output=True, text=True)
        
        print(f"Return code: {result.returncode}")
        print(f"STDOUT:\n{result.stdout}")
        if result.stderr:
            print(f"STDERR:\n{result.stderr}")
        
        # Check if heatmaps were generated
        reports_dir = Path("reports")
        if reports_dir.exists():
            report_subdirs = [d for d in reports_dir.iterdir() if d.is_dir()]
            if report_subdirs:
                latest_report = max(report_subdirs, key=lambda x: x.name)
                print(f"Latest report directory: {latest_report}")
                
                # List files in the latest report
                for file in latest_report.iterdir():
                    print(f"  Generated file: {file.name}")
                    
                return True
        
        return False
        
    finally:
        os.chdir(original_dir)

if __name__ == "__main__":
    success = test_bloomberg_heatmap()
    if success:
        print("\n✅ Bloomberg heatmap generation test PASSED")
    else:
        print("\n❌ Bloomberg heatmap generation test FAILED")