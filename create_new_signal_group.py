#!/usr/bin/env python3
"""
Create a new Signal group for financial alerts with a clean history.
"""

import asyncio
import aiohttp
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from src.config.settings import settings


async def create_new_signal_group():
    """Create a new Signal group for alerts."""
    
    signal_config = settings.get_signal_config()
    api_url = signal_config.get('api_url', 'http://localhost:8080')
    phone_number = signal_config.get('phone_number')
    
    if not phone_number:
        print("❌ No phone number configured")
        return None
    
    try:
        # Create new group
        group_data = {
            "name": "Daily Financial Alerts",
            "description": "Automated daily financial alerts and trading signals",
            "members": [],  # Start with just the creator
            "avatar": None
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{api_url}/v1/groups/{phone_number}",
                json=group_data
            ) as response:
                
                if response.status == 201:
                    result = await response.json()
                    group_id = result.get('id')
                    invite_link = result.get('invite_link')
                    
                    print("✅ New Signal group created successfully!")
                    print(f"📱 Group ID: {group_id}")
                    print(f"🔗 Invite Link: {invite_link}")
                    print()
                    print("📝 Next steps:")
                    print("1. Update your .env file with the new SIGNAL_GROUP_ID")
                    print("2. Share the invite link with group members")
                    print("3. Restart the daily alerts service")
                    
                    return {
                        'group_id': group_id,
                        'invite_link': invite_link
                    }
                else:
                    error_text = await response.text()
                    print(f"❌ Failed to create group: {response.status} - {error_text}")
                    return None
                    
    except Exception as e:
        print(f"❌ Error creating group: {e}")
        return None


async def main():
    """Main function."""
    print("🔧 Creating New Signal Group for Financial Alerts")
    print("=" * 60)
    print("⚠️  This will create a NEW group with clean history")
    print("⚠️  You'll need to update your configuration and invite members")
    print()
    
    confirm = input("Do you want to proceed? (y/N): ").lower().strip()
    if confirm != 'y':
        print("❌ Operation cancelled")
        return
    
    result = await create_new_signal_group()
    
    if result:
        print()
        print("🔧 To use the new group, update your .env file:")
        print(f"SIGNAL_GROUP_ID={result['group_id']}")
        print()
        print("Then restart the service:")
        print("sudo systemctl restart daily-alerts")


if __name__ == "__main__":
    asyncio.run(main())