#!/usr/bin/env python3
"""
Fix encoding issues and generate real heatmaps from international interest rate data
"""

import subprocess
import sys
import os
from pathlib import Path

# Set UTF-8 encoding
os.environ['PYTHONIOENCODING'] = 'utf-8'
os.environ['LANG'] = 'en_US.UTF-8'
os.environ['LC_ALL'] = 'en_US.UTF-8'

# Add paths
heatmap_dir = Path("/home/ohms/OhmsAlertsReports/heatmaps_package/core_files")
sys.path.insert(0, str(heatmap_dir))

# Change to heatmap directory
os.chdir(str(heatmap_dir))

print("Generating real interest rate heatmaps...")

try:
    # First collect the data
    print("Step 1: Collecting international interest rates...")
    result = subprocess.run([
        sys.executable, 
        str(heatmap_dir / "collect_international_rates.py")
    ], capture_output=True, text=True, encoding='utf-8')
    
    if result.returncode != 0:
        print(f"Warning: Data collection had issues: {result.stderr[:200]}")
    
    # Then generate the heatmaps
    print("Step 2: Generating Bloomberg-style heatmaps...")
    result = subprocess.run([
        sys.executable,
        str(heatmap_dir / "bloomberg_report_final.py")
    ], capture_output=True, text=True, encoding='utf-8')
    
    if result.returncode != 0:
        print(f"Warning: Heatmap generation had issues: {result.stderr[:200]}")
    
    # Check for output
    output_dir = heatmap_dir / "output"
    if output_dir.exists():
        pngs = list(output_dir.glob("*.png"))
        if pngs:
            print(f"Success! Generated {len(pngs)} heatmaps:")
            for png in pngs:
                print(f"  - {png.name}")
        else:
            print("No heatmaps found in output directory")
    
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()