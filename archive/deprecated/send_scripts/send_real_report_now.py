#!/usr/bin/env python3
"""Send real MyMama report with heatmaps to both messengers"""

import asyncio
import json
import os
import sys
from datetime import datetime
from pathlib import Path

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.scrapers.unified_mymama_scraper import UnifiedMyMamaScraper
from src.data_processors.template_generator import StructuredTemplateGenerator
from src.messengers.unified_messenger import UnifiedMessenger
from messengers.multi_messenger import MultiMessenger
from messenger_compatibility import TelegramMessenger, SignalMessenger

async def send_real_report_with_heatmaps():
    """Send real financial report with heatmaps"""
    
    print("📊 Collecting real financial data from MyMama...")
    
    # Initialize scraper and collect data
    scraper = UnifiedMyMamaScraper()
    data = await scraper.scrape_data()
    
    # Generate structured report
    generator = StructuredTemplateGenerator()
    report = generator.generate_report(data)
    
    print("\n✅ Real data collected successfully!")
    print(f"📊 Report contains {len(data.get('forex', []))} forex signals")
    print(f"📈 Report contains {len(data.get('options', []))} options trades")
    print(f"📉 Report contains {len(data.get('earnings', []))} earnings reports")
    
    # Find latest heatmap images
    heatmap_dir = Path("heatmaps/reports")
    latest_heatmaps = None
    
    if heatmap_dir.exists():
        # Get latest directory
        dirs = [d for d in heatmap_dir.iterdir() if d.is_dir() and d.name.startswith("2025")]
        if dirs:
            latest_dir = max(dirs, key=lambda d: d.name)
            categorical = latest_dir / "categorical_heatmap.png"
            forex_pairs = latest_dir / "forex_pairs_heatmap.png"
            
            if categorical.exists() and forex_pairs.exists():
                latest_heatmaps = {
                    'categorical': str(categorical),
                    'forex_pairs': str(forex_pairs)
                }
                print(f"\n📊 Found heatmaps from: {latest_dir.name}")
    
    # Initialize messengers
    print("\n📱 Initializing messengers...")
    multi_messenger = MultiMessenger()
    
    # Send text report
    print("\n📤 Sending structured report...")
    await multi_messenger.send_structured_financial_data(report)
    
    # Send heatmap images if available
    if latest_heatmaps:
        print("\n📊 Sending heatmap images...")
        
        # Send categorical heatmap
        await multi_messenger.send_attachment(
            latest_heatmaps['categorical'],
            caption="📊 Interest Rate Heatmap - Categorical Analysis"
        )
        
        # Send forex pairs heatmap
        await multi_messenger.send_attachment(
            latest_heatmaps['forex_pairs'],
            caption="💱 Interest Rate Heatmap - Forex Pairs"
        )
        
        print("✅ Heatmaps sent successfully!")
    
    print("\n🎉 Real report with heatmaps sent successfully!")
    
    # Save report for verification
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = f"output/mymama/sent_report_{timestamp}.txt"
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    
    with open(output_file, 'w') as f:
        f.write(report)
    
    print(f"💾 Report saved to: {output_file}")

if __name__ == "__main__":
    asyncio.run(send_real_report_with_heatmaps())