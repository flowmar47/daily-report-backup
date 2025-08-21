#!/usr/bin/env python3
"""
Final test of Bloomberg heatmap system integration
"""

import os
import sys
import subprocess
from pathlib import Path
from datetime import datetime

def generate_heatmaps():
    """Generate Bloomberg-style heatmaps"""
    
    # Path to the heatmaps core files directory
    heatmaps_dir = Path(__file__).parent.parent / "heatmaps_package" / "core_files"
    
    print(f"Generating Bloomberg heatmaps...")
    print(f"Heatmaps directory: {heatmaps_dir}")
    
    # Change to the heatmaps directory and run the script
    original_dir = os.getcwd()
    
    try:
        os.chdir(heatmaps_dir)
        
        # Set environment to handle Unicode properly
        env = os.environ.copy()
        env['PYTHONIOENCODING'] = 'utf-8'
        
        # Run the Bloomberg script
        result = subprocess.run([
            sys.executable, "bloomberg_report_final.py"
        ], capture_output=True, text=True, env=env)
        
        if result.returncode == 0:
            print("SUCCESS: Bloomberg heatmaps generated successfully")
            
            # Find the latest report directory
            reports_dir = Path("reports")
            if reports_dir.exists():
                report_subdirs = [d for d in reports_dir.iterdir() if d.is_dir()]
                if report_subdirs:
                    latest_report = max(report_subdirs, key=lambda x: x.name)
                    
                    # Get paths to the generated files
                    categorical_heatmap = latest_report / "categorical_heatmap.png"
                    forex_pairs_heatmap = latest_report / "forex_pairs_heatmap.png"
                    daily_brief = latest_report / "daily_brief.md"
                    
                    return {
                        'success': True,
                        'categorical_heatmap': str(categorical_heatmap),
                        'forex_pairs_heatmap': str(forex_pairs_heatmap),
                        'daily_brief': str(daily_brief),
                        'report_dir': str(latest_report)
                    }
        
        print(f"ERROR: Bloomberg heatmap generation failed: {result.stderr}")
        return {'success': False, 'error': result.stderr}
        
    finally:
        os.chdir(original_dir)

def main():
    """Main test function"""
    
    print("=== BLOOMBERG HEATMAP INTEGRATION TEST ===")
    print(f"Test started at: {datetime.now()}")
    
    # Generate heatmaps
    result = generate_heatmaps()
    
    if result['success']:
        print(f"\nHEATMAPS GENERATED SUCCESSFULLY:")
        print(f"   Report directory: {result['report_dir']}")
        print(f"   Categorical heatmap: {Path(result['categorical_heatmap']).name}")
        print(f"   Forex pairs heatmap: {Path(result['forex_pairs_heatmap']).name}")
        print(f"   Daily brief: {Path(result['daily_brief']).name}")
        
        # Check file sizes
        for file_key in ['categorical_heatmap', 'forex_pairs_heatmap', 'daily_brief']:
            file_path = Path(result[file_key])
            if file_path.exists():
                size_kb = file_path.stat().st_size / 1024
                print(f"   {file_path.name}: {size_kb:.1f} KB")
        
        print(f"\nINTEGRATION POINTS:")
        print(f"   1. Heatmaps can be sent via Signal/Telegram messengers")
        print(f"   2. Daily brief can be included in structured reports")
        print(f"   3. Files are mobile-optimized for instant messaging")
        print(f"   4. Professional Bloomberg-style visualizations")
        
        print(f"\nUSAGE FOR DAILY REPORT INTEGRATION:")
        print(f"   # Generate heatmaps in daily report script:")
        print(f"   import subprocess, os")
        print(f"   heatmap_dir = '../heatmaps_package/core_files'")
        print(f"   os.chdir(heatmap_dir)")
        print(f"   subprocess.run(['python3', 'bloomberg_report_final.py'])")
        print(f"   # Then send generated PNG files via unified messenger")
        
        print(f"\nBLOOMBERG HEATMAP INTEGRATION TEST: PASSED")
        return True
    else:
        print(f"ERROR: Heatmap generation failed: {result.get('error', 'Unknown error')}")
        print(f"BLOOMBERG HEATMAP INTEGRATION TEST: FAILED")
        return False

if __name__ == "__main__":
    main()