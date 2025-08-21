#!/usr/bin/env python3
"""
Test fresh data collection and heatmap generation
"""

import asyncio
import subprocess
import sys
import os
import json
from datetime import datetime

async def test_mymama_data():
    """Test fresh data collection from MyMama.uk"""
    print("🔍 Testing fresh data collection from MyMama.uk...")
    
    try:
        from real_only_mymama_scraper import RealOnlyMyMamaScraper
        
        scraper = RealOnlyMyMamaScraper()
        result = await scraper.scrape_real_alerts_only()
        
        if result and result.get('success'):
            print("✅ Data collection successful")
            data = result.get('data', {})
            
            # Check for real content indicators
            has_real_data = data.get('has_real_data', False)
            print(f"Has real data: {has_real_data}")
            
            # Count actual alerts
            forex_count = len(data.get('forex_alerts', []))
            options_count = len(data.get('options_alerts', []))
            earnings_count = len(data.get('earnings_alerts', []))
            premium_count = len(data.get('premium_trades', []))
            
            print(f"Forex alerts: {forex_count}")
            print(f"Options alerts: {options_count}") 
            print(f"Earnings alerts: {earnings_count}")
            print(f"Premium trades: {premium_count}")
            
            # Check for test/example indicators
            data_str = str(data).lower()
            test_indicators = ['test', 'example', 'sample', 'demo', 'placeholder']
            has_test_content = any(indicator in data_str for indicator in test_indicators)
            
            if has_test_content:
                print("⚠️ Warning: Data may contain test/example content")
                return None
            
            if has_real_data and (forex_count + options_count + earnings_count + premium_count) > 0:
                print("✅ Real financial data verified")
                return result
            else:
                print("❌ No real alerts found")
                return None
                
        else:
            print("❌ Data collection failed")
            return None
            
    except Exception as e:
        print(f"❌ Error collecting data: {e}")
        return None

def test_heatmap_generation():
    """Test heatmap generation"""
    print("\n🌡️ Testing heatmap generation...")
    
    try:
        # Change to heatmap directory
        heatmap_dir = "/home/ohms/OhmsAlertsReports/heatmaps_package/core_files"
        
        if not os.path.exists(heatmap_dir):
            print("❌ Heatmap directory not found")
            return None
        
        # Run the bloomberg report generator
        result = subprocess.run([
            sys.executable, "bloomberg_report_final.py"
        ], cwd=heatmap_dir, capture_output=True, text=True, timeout=120)
        
        if result.returncode == 0:
            print("✅ Heatmap generation successful")
            
            # Look for generated files
            reports_dir = os.path.join(heatmap_dir, "reports")
            if os.path.exists(reports_dir):
                # Find latest directory
                subdirs = [d for d in os.listdir(reports_dir) 
                          if os.path.isdir(os.path.join(reports_dir, d))]
                
                if subdirs:
                    latest_dir = max(subdirs)
                    package_dir = os.path.join(reports_dir, latest_dir)
                    
                    categorical_path = os.path.join(package_dir, "categorical_heatmap.png")
                    forex_path = os.path.join(package_dir, "forex_pairs_heatmap.png")
                    
                    if os.path.exists(categorical_path) and os.path.exists(forex_path):
                        print(f"✅ Both heatmaps generated in {latest_dir}")
                        return {
                            'categorical_heatmap': categorical_path,
                            'forex_heatmap': forex_path
                        }
                    else:
                        print("❌ Heatmap files not found")
                        return None
                else:
                    print("❌ No heatmap output directories")
                    return None
            else:
                print("❌ Reports directory not found")
                return None
        else:
            print(f"❌ Heatmap generation failed: {result.stderr}")
            return None
            
    except subprocess.TimeoutExpired:
        print("❌ Heatmap generation timed out")
        return None
    except Exception as e:
        print(f"❌ Error generating heatmaps: {e}")
        return None

async def main():
    print("🎯 FRESH DATA COLLECTION AND VERIFICATION")
    print("=" * 60)
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Test MyMama data collection
    mymama_data = await test_mymama_data()
    
    # Test heatmap generation
    heatmap_data = test_heatmap_generation()
    
    print("\n📊 VERIFICATION SUMMARY")
    print("=" * 60)
    
    verified_items = []
    
    if mymama_data:
        print("✅ MyMama financial data: VERIFIED (real alerts)")
        verified_items.append("financial_data")
    else:
        print("❌ MyMama financial data: NOT AVAILABLE")
    
    if heatmap_data:
        print("✅ Interest rate heatmaps: VERIFIED (live data)")
        verified_items.append("heatmaps")
    else:
        print("❌ Interest rate heatmaps: NOT AVAILABLE")
    
    print(f"\n🎯 READY TO SEND: {len(verified_items)} verified items")
    
    if len(verified_items) >= 2:  # Both financial data and heatmaps
        print("✅ All required items verified - ready for sending")
        return {
            'financial_data': mymama_data,
            'heatmap_data': heatmap_data,
            'verified': True
        }
    else:
        print("❌ Insufficient verified data - sending aborted")
        return {
            'verified': False,
            'reason': f"Only {len(verified_items)} of 2 required items available"
        }

if __name__ == "__main__":
    result = asyncio.run(main())
    
    # Save result for next step
    with open('verification_result.json', 'w') as f:
        json.dump(result, f, indent=2, default=str)