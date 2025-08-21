#!/usr/bin/env python3
"""
Configure Signal group settings including disappearing messages.
"""

import asyncio
import aiohttp
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from src.config.settings import settings
from messenger_compatibility import SignalMessenger


async def configure_disappearing_messages(duration_seconds):
    """Configure disappearing messages for the Signal group."""
    
    signal_config = settings.get_signal_config()
    api_url = signal_config.get('api_url', 'http://localhost:8080')
    phone_number = signal_config.get('phone_number')
    group_id = signal_config.get('group_id')
    
    if not all([phone_number, group_id]):
        print("❌ Missing Signal configuration")
        return False
    
    try:
        # Update group settings
        group_data = {
            "timer": duration_seconds  # Time in seconds for messages to disappear
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.put(
                f"{api_url}/v1/groups/{phone_number}/{group_id}",
                json=group_data
            ) as response:
                
                if response.status == 204:
                    duration_hours = duration_seconds // 3600
                    duration_days = duration_hours // 24
                    
                    if duration_days > 0:
                        time_str = f"{duration_days} day(s)"
                    elif duration_hours > 0:
                        time_str = f"{duration_hours} hour(s)"
                    else:
                        time_str = f"{duration_seconds} second(s)"
                    
                    print(f"✅ Disappearing messages set to: {time_str}")
                    print("📱 New messages will automatically delete after this time")
                    return True
                else:
                    error_text = await response.text()
                    print(f"❌ Failed to update group: {response.status} - {error_text}")
                    return False
                    
    except Exception as e:
        print(f"❌ Error configuring group: {e}")
        return False


async def send_cleanup_notice():
    """Send a notice about the chat cleanup."""
    signal_config = settings.get_signal_config()
    signal_messenger = SignalMessenger(signal_config)
    
    message = """🧹 Chat History Management

This group has been configured for automatic message cleanup.
New messages will disappear after the set duration to keep the chat clean.

Historical messages remain until manually deleted.
Future financial alerts will auto-delete to maintain a clean feed."""

    result = await signal_messenger.send_message(message)
    return result.status.name == 'SUCCESS'


async def main():
    """Main function."""
    print("🔧 Configure Signal Group Message Management")
    print("=" * 50)
    print()
    print("Choose message deletion timing:")
    print("1. 1 hour")
    print("2. 6 hours") 
    print("3. 1 day")
    print("4. 1 week")
    print("5. Custom duration")
    print("6. Disable disappearing messages")
    print()
    
    choice = input("Enter choice (1-6): ").strip()
    
    duration_map = {
        '1': 3600,        # 1 hour
        '2': 21600,       # 6 hours
        '3': 86400,       # 1 day
        '4': 604800,      # 1 week
        '6': 0            # Disable
    }
    
    if choice in duration_map:
        duration = duration_map[choice]
    elif choice == '5':
        try:
            hours = float(input("Enter hours for custom duration: "))
            duration = int(hours * 3600)
        except ValueError:
            print("❌ Invalid duration")
            return
    else:
        print("❌ Invalid choice")
        return
    
    print(f"\n🔧 Configuring disappearing messages...")
    success = await configure_disappearing_messages(duration)
    
    if success:
        print("\n📨 Sending cleanup notice...")
        await send_cleanup_notice()
        
        print("\n✅ Group configuration updated!")
        print("\n💡 Note: This only affects NEW messages.")
        print("💡 To clear existing history, use the Signal app manually.")


if __name__ == "__main__":
    asyncio.run(main())