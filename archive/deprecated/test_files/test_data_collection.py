#!/usr/bin/env python3
"""
Test script to run data collection for Bloomberg heatmap system
"""

import os
import sys
import subprocess
from pathlib import Path

def test_data_collection():
    """Test data collection for Bloomberg system"""
    
    # Path to the heatmaps core files directory
    heatmaps_dir = Path(__file__).parent.parent / "heatmaps_package" / "core_files"
    
    print(f"Testing data collection...")
    print(f"Heatmaps directory: {heatmaps_dir}")
    
    # Change to the heatmaps directory and run the collection script
    original_dir = os.getcwd()
    
    try:
        os.chdir(heatmaps_dir)
        print(f"Changed to directory: {os.getcwd()}")
        
        # Run the data collection script
        result = subprocess.run([
            sys.executable, "collect_international_rates.py"
        ], capture_output=True, text=True, timeout=300)
        
        print(f"Return code: {result.returncode}")
        print(f"STDOUT:\n{result.stdout}")
        if result.stderr:
            print(f"STDERR:\n{result.stderr}")
        
        # Check if data was collected
        if result.returncode == 0:
            print("\n✅ Data collection completed successfully")
            return True
        else:
            print("\n❌ Data collection failed")
            return False
        
    except subprocess.TimeoutExpired:
        print("\n⏰ Data collection timed out")
        return False
    finally:
        os.chdir(original_dir)

if __name__ == "__main__":
    success = test_data_collection()
    if success:
        print("Data collection test PASSED")
    else:
        print("Data collection test FAILED")