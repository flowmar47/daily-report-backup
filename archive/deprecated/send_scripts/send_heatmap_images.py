#!/usr/bin/env python3
"""
Send heatmap images to both Signal and Telegram groups
"""

import asyncio
import sys
import os
from pathlib import Path
from datetime import datetime
sys.path.append('.')

from src.messengers.unified_messenger import UnifiedMultiMessenger, AttachmentData

async def send_heatmap_images():
    """Find and send the latest heatmap images to both groups"""
    print('🎨 Looking for heatmap images...')
    
    # Look for heatmap images in the heatmaps package
    heatmap_dirs = [
        '/home/ohms/OhmsAlertsReports/heatmaps_package/core_files',
        '/home/ohms/OhmsAlertsReports/heatmaps_package',
        '/home/ohms/OhmsAlertsReports/daily-report'
    ]
    
    heatmap_files = []
    
    for heatmap_dir in heatmap_dirs:
        heatmap_path = Path(heatmap_dir)
        if heatmap_path.exists():
            # Look for PNG files with "heatmap", "bloomberg", or today's date
            today = datetime.now().strftime('%Y%m%d')
            
            for pattern in ['*heatmap*.png', '*bloomberg*.png', f'*{today}*.png', '*.png']:
                found_files = list(heatmap_path.glob(pattern))
                for file in found_files:
                    if file.stat().st_mtime > (datetime.now().timestamp() - 86400):  # Last 24 hours
                        heatmap_files.append(file)
    
    # Remove duplicates and sort by modification time
    heatmap_files = list(set(heatmap_files))
    heatmap_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
    
    if not heatmap_files:
        print('❌ No recent heatmap images found')
        return
    
    print(f'✅ Found {len(heatmap_files)} heatmap images')
    
    # Take the 2 most recent files (likely the two main heatmaps)
    recent_heatmaps = heatmap_files[:2]
    
    multi_messenger = UnifiedMultiMessenger()
    
    try:
        for i, heatmap_file in enumerate(recent_heatmaps):
            print(f'📤 Sending heatmap {i+1}: {heatmap_file.name}')
            
            # Create attachment data
            attachment = AttachmentData(
                file_path=str(heatmap_file),
                filename=heatmap_file.name,
                caption=f"📊 Daily Interest Rate Heatmap - {datetime.now().strftime('%B %d, %Y')}"
            )
            
            # Send to all platforms
            results = await multi_messenger.send_attachments([attachment])
            
            for platform, platform_results in results.items():
                for result in platform_results:
                    status = "✅ SUCCESS" if result.status.value == 'success' else "❌ FAILED"
                    print(f"  {platform}: {status}")
                    if result.error:
                        print(f"    Error: {result.error}")
        
        print('✅ Heatmap delivery completed')
        
    finally:
        await multi_messenger.cleanup()

if __name__ == "__main__":
    asyncio.run(send_heatmap_images())