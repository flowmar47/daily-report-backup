#!/usr/bin/env python3
"""
Simple test script to generate Bloomberg heatmaps with mock data
"""

import os
import sys
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
import subprocess

def create_mock_data():
    """Create mock data for testing"""
    
    # Path to the heatmaps core files directory
    heatmaps_dir = Path(__file__).parent.parent / "heatmaps_package" / "core_files"
    db_path = heatmaps_dir / "interest_rates.db"
    
    print(f"Creating mock data in {db_path}")
    
    # Mock data for major currencies
    mock_data = [
        ('USD', 'United States', 'Federal Reserve', 'Federal Funds Rate', 5.25, '2025-07-07', datetime.now().isoformat(), 'FRED:DFF'),
        ('EUR', 'Eurozone', 'European Central Bank', 'Main Refinancing Rate', 4.5, '2025-07-07', datetime.now().isoformat(), 'ECB:MRR'),
        ('GBP', 'United Kingdom', 'Bank of England', 'Bank Rate', 5.25, '2025-07-07', datetime.now().isoformat(), 'BOE:BR'),
        ('JPY', 'Japan', 'Bank of Japan', 'Policy Rate', -0.1, '2025-07-07', datetime.now().isoformat(), 'BOJ:PR'),
        ('CAD', 'Canada', 'Bank of Canada', 'Overnight Rate', 4.75, '2025-07-07', datetime.now().isoformat(), 'BOC:OR'),
        ('AUD', 'Australia', 'Reserve Bank of Australia', 'Cash Rate', 4.35, '2025-07-07', datetime.now().isoformat(), 'RBA:CR'),
        ('CHF', 'Switzerland', 'Swiss National Bank', 'Policy Rate', 1.5, '2025-07-07', datetime.now().isoformat(), 'SNB:PR'),
        ('NZD', 'New Zealand', 'Reserve Bank of New Zealand', 'Official Cash Rate', 5.5, '2025-07-07', datetime.now().isoformat(), 'RBNZ:OCR'),
    ]
    
    # Connect to database and insert mock data
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Create table if it doesn't exist
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS interest_rates (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            currency TEXT NOT NULL,
            country TEXT NOT NULL,
            central_bank TEXT NOT NULL,
            rate_type TEXT NOT NULL,
            rate_value REAL NOT NULL,
            effective_date TEXT NOT NULL,
            collection_timestamp TEXT NOT NULL,
            source TEXT NOT NULL
        )
    ''')
    
    # Insert mock data
    cursor.executemany('''
        INSERT INTO interest_rates (currency, country, central_bank, rate_type, rate_value, effective_date, collection_timestamp, source)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', mock_data)
    
    conn.commit()
    conn.close()
    
    print(f"Inserted {len(mock_data)} mock records")
    return True

def test_bloomberg_generation():
    """Test Bloomberg heatmap generation with mock data"""
    
    # Path to the heatmaps core files directory
    heatmaps_dir = Path(__file__).parent.parent / "heatmaps_package" / "core_files"
    
    print(f"Testing Bloomberg heatmap generation...")
    
    # Change to the heatmaps directory and run the script
    original_dir = os.getcwd()
    
    try:
        os.chdir(heatmaps_dir)
        print(f"Changed to directory: {os.getcwd()}")
        
        # Set environment to handle Unicode properly
        env = os.environ.copy()
        env['PYTHONIOENCODING'] = 'utf-8'
        
        # Run the Bloomberg script
        result = subprocess.run([
            sys.executable, "bloomberg_report_final.py"
        ], capture_output=True, text=True, env=env)
        
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
                    print(f"  Generated file: {file.name} ({file.stat().st_size} bytes)")
                    
                return True
        
        return False
        
    finally:
        os.chdir(original_dir)

if __name__ == "__main__":
    print("=== BLOOMBERG HEATMAP SYSTEM TEST ===")
    
    # Create mock data
    if create_mock_data():
        print("Mock data created successfully")
    else:
        print("Failed to create mock data")
        sys.exit(1)
    
    # Test Bloomberg generation
    if test_bloomberg_generation():
        print("\nBLOOMBERG HEATMAP GENERATION TEST PASSED")
    else:
        print("\nBLOOMBERG HEATMAP GENERATION TEST FAILED")