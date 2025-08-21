#!/usr/bin/env python3
import os
import subprocess
import sys
import json
from datetime import datetime

def generate_heatmaps():
    """Generate heatmaps manually"""
    print("🌡️ Generating interest rate heatmaps...")
    
    heatmap_dir = "/home/ohms/OhmsAlertsReports/heatmaps_package/core_files"
    
    if not os.path.exists(heatmap_dir):
        print("❌ Heatmap directory not found")
        return None
    
    try:
        # Run the silent heatmap system for clean execution
        result = subprocess.run([
            sys.executable, "silent_bloomberg_system.py"
        ], cwd=heatmap_dir, capture_output=True, text=True, timeout=180)
        
        if result.returncode == 0:
            print("✅ Heatmap generation completed")
            
            # Check for generated files
            reports_dir = os.path.join(heatmap_dir, "reports")
            if os.path.exists(reports_dir):
                subdirs = [d for d in os.listdir(reports_dir) 
                          if os.path.isdir(os.path.join(reports_dir, d)) and len(d) > 8]
                
                if subdirs:
                    latest_dir = max(subdirs)
                    package_dir = os.path.join(reports_dir, latest_dir)
                    
                    categorical_path = os.path.join(package_dir, "categorical_heatmap.png")
                    forex_path = os.path.join(package_dir, "forex_pairs_heatmap.png")
                    
                    if os.path.exists(categorical_path) and os.path.exists(forex_path):
                        # Get file sizes to verify they're real
                        cat_size = os.path.getsize(categorical_path)
                        forex_size = os.path.getsize(forex_path)
                        
                        print(f"✅ Categorical heatmap: {cat_size/1024:.1f} KB")
                        print(f"✅ Forex heatmap: {forex_size/1024:.1f} KB")
                        
                        return {
                            'categorical_heatmap': categorical_path,
                            'forex_heatmap': forex_path,
                            'timestamp': datetime.now().isoformat()
                        }
        
        print("❌ Heatmap files not found or generation failed")
        return None
        
    except Exception as e:
        print(f"❌ Heatmap generation error: {e}")
        return None

def run_concurrent_collection():
    """Run the concurrent data collection that was working before"""
    print("📊 Running concurrent data collection...")
    
    try:
        # Use the working concurrent collector
        from concurrent_data_collector import ConcurrentDataCollector
        from enhanced_error_handler import EnhancedErrorHandler
        
        # Initialize components
        error_config = {'max_retries': 2, 'base_retry_delay': 2}
        error_handler = EnhancedErrorHandler(error_config)
        
        collector_config = {
            'max_concurrent_operations': 2,
            'timeout_seconds': 120,
            'error_handling': error_config
        }
        
        collector = ConcurrentDataCollector(collector_config)
        
        # This should work now with our fixes
        import asyncio
        result = asyncio.run(collector.collect_all_data_concurrent())
        
        if result and result.get('forex_data'):
            forex_data = result['forex_data']
            if forex_data and forex_data.get('has_real_data'):
                print("✅ Real financial data collected")
                return forex_data
        
        print("❌ No real financial data available")
        return None
        
    except Exception as e:
        print(f"❌ Data collection failed: {e}")
        return None

def main():
    print("🎯 MANUAL VERIFICATION OF FRESH DATA")
    print("=" * 50)
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S PST')}")
    
    # Step 1: Generate heatmaps
    heatmap_data = generate_heatmaps()
    
    # Step 2: Collect financial data
    financial_data = run_concurrent_collection()
    
    # Step 3: Verification summary
    print("\n📋 VERIFICATION SUMMARY")
    print("=" * 50)
    
    verified_items = []
    
    if heatmap_data:
        print("✅ Interest rate heatmaps: READY")
        verified_items.append("heatmaps")
    else:
        print("❌ Interest rate heatmaps: NOT READY")
    
    if financial_data:
        print("✅ Financial data: READY") 
        verified_items.append("financial_data")
    else:
        print("❌ Financial data: NOT READY")
    
    result = {
        'verified': len(verified_items) >= 1,  # At least one must be ready
        'financial_data': financial_data,
        'heatmap_data': heatmap_data,
        'verified_items': verified_items,
        'timestamp': datetime.now().isoformat()
    }
    
    # Save results
    with open('manual_verification.json', 'w') as f:
        json.dump(result, f, indent=2, default=str)
    
    print(f"\n🎯 VERIFICATION COMPLETE: {len(verified_items)} items ready")
    
    if result['verified']:
        print("✅ READY TO PROCEED WITH SENDING")
    else:
        print("❌ NOT READY - insufficient verified data")
    
    return result

if __name__ == "__main__":
    main()