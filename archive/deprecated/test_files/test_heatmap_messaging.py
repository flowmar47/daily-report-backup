#!/usr/bin/env python3
"""
Test script to verify heatmap generation and messaging integration
"""

import asyncio
import sys
import os
sys.path.append('src')

from main import DailyReportAutomation

async def test_complete_heatmap_pipeline():
    """Test the complete heatmap pipeline including messaging"""
    
    print("🚀 Testing complete heatmap pipeline...")
    
    # Initialize automation
    automation = DailyReportAutomation()
    
    # Step 1: Generate heatmaps
    print("\n📊 Step 1: Generating heatmaps...")
    heatmap_data = await automation.generate_heatmaps()
    
    if not heatmap_data:
        print("❌ Heatmap generation failed")
        return False
    
    print("✅ Heatmaps generated successfully!")
    print(f"  📊 Categorical: {heatmap_data['categorical_heatmap']}")
    print(f"  💱 Forex: {heatmap_data['forex_heatmap']}")
    
    # Verify files exist
    if not os.path.exists(heatmap_data['categorical_heatmap']):
        print("❌ Categorical heatmap file not found")
        return False
    
    if not os.path.exists(heatmap_data['forex_heatmap']):
        print("❌ Forex heatmap file not found")
        return False
    
    print("✅ Both heatmap files verified")
    
    # Step 2: Test messaging
    print("\n📱 Step 2: Testing heatmap messaging...")
    try:
        success = await automation.send_heatmap_images(heatmap_data)
        
        if success:
            print("✅ Heatmap images sent successfully to both platforms!")
        else:
            print("⚠️ Heatmap sending had some issues")
        
        return success
        
    except Exception as e:
        print(f"❌ Error in heatmap messaging: {e}")
        return False

async def test_heatmap_generation_only():
    """Test just the heatmap generation"""
    
    print("🔬 Testing heatmap generation only...")
    
    automation = DailyReportAutomation()
    heatmap_data = await automation.generate_heatmaps()
    
    if heatmap_data:
        print("✅ Heatmap generation successful")
        print(f"  📊 Categorical: {heatmap_data['categorical_heatmap']}")
        print(f"  💱 Forex: {heatmap_data['forex_heatmap']}")
        return True
    else:
        print("❌ Heatmap generation failed")
        return False

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "generation-only":
        success = asyncio.run(test_heatmap_generation_only())
    else:
        success = asyncio.run(test_complete_heatmap_pipeline())
    
    sys.exit(0 if success else 1)