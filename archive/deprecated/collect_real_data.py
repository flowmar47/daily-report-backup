#!/usr/bin/env python3
"""Collect real financial data from MyMama"""

import os
import sys
import json
from datetime import datetime

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.scrapers.unified_mymama_scraper import UnifiedMyMamaScraper
from src.data_processors.template_generator import StructuredTemplateGenerator

def collect_real_data():
    """Collect real trading data from MyMama"""
    print("Collecting real financial data from MyMama...")
    
    # Initialize scraper
    scraper = UnifiedMyMamaScraper()
    
    # Scrape all sections using async method
    import asyncio
    data = asyncio.run(scraper.scrape())
    
    # Save raw data
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = "output/mymama"
    os.makedirs(output_dir, exist_ok=True)
    
    output_file = os.path.join(output_dir, f"real_data_{timestamp}.json")
    with open(output_file, 'w') as f:
        json.dump(data, f, indent=2)
    
    # Also save as latest
    latest_file = os.path.join(output_dir, "latest_real_data.json")
    with open(latest_file, 'w') as f:
        json.dump(data, f, indent=2)
    
    # Generate structured report
    generator = StructuredTemplateGenerator()
    report = generator.generate_report(data)
    
    print(f"\nData collected and saved to: {output_file}")
    print("\nGenerated Report:")
    print("=" * 60)
    print(report)
    print("=" * 60)
    
    return data, report

if __name__ == "__main__":
    data, report = collect_real_data()