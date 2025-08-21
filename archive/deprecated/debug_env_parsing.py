#!/usr/bin/env python3
"""
Debug environment variable parsing for WhatsApp
"""

import os
import sys
from pathlib import Path

# Add paths
sys.path.insert(0, str(Path(__file__).parent))

from utils.env_config import EnvironmentConfig

def debug_env_parsing():
    """Debug environment variable parsing"""
    print("=" * 60)
    print("DEBUGGING ENVIRONMENT VARIABLE PARSING")
    print("=" * 60)
    
    # Check environment variables directly
    print("Direct environment variables:")
    for key in os.environ:
        if 'WHATSAPP' in key:
            print(f"  {key} = {os.environ[key]}")
    
    print("\nEnvironmentConfig parsing:")
    env_config = EnvironmentConfig('daily_report')
    
    # Debug the credentials
    print("Parsed credentials:")
    credentials = env_config.get_all_vars()
    for key, value in credentials.items():
        if 'WHATSAPP' in key:
            print(f"  {key} = {value}")
    
    # Test group ID parsing specifically
    group_id = credentials.get('WHATSAPP_GROUP_ID')
    print(f"\nGroup ID from credentials: {group_id}")
    
    if group_id:
        print("Group ID found - parsing should work")
    else:
        print("Group ID NOT found - this is the issue")

if __name__ == "__main__":
    debug_env_parsing()