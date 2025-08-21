#!/usr/bin/env python3
"""
Wait for group to become available and complete setup
"""
import requests
import time
from pathlib import Path
from dotenv import load_dotenv, set_key

env_path = Path(__file__).parent / '.env'
load_dotenv(env_path)

API_URL = "http://localhost:8080"
PHONE_NUMBER = "+16572463906"

def check_for_group():
    """Check if Ohms Alerts Reports group is available"""
    try:
        response = requests.get(f"{API_URL}/v1/groups/{PHONE_NUMBER}")
        
        if response.status_code == 200:
            groups = response.json()
            
            for group in groups:
                if "Ohms Alerts Reports" in group.get('name', ''):
                    return group.get('id') or group.get('internal_id')
        
        return None
        
    except Exception:
        return None

def complete_setup(group_id):
    """Complete the setup with found group"""
    print(f"\n✅ Found 'Ohms Alerts Reports' group!")
    print(f"   Group ID: {group_id}")
    
    # Save configuration
    print("\n💾 Saving configuration...")
    set_key(env_path, 'SIGNAL_PHONE_NUMBER', PHONE_NUMBER)
    set_key(env_path, 'SIGNAL_GROUP_ID', group_id)
    set_key(env_path, 'SIGNAL_API_URL', API_URL)
    
    # Send test message
    print("\n📤 Sending test message...")
    
    message = """🎉 Signal Bot Connected!

✅ Registration complete
✅ Group joined successfully
✅ Ready for automated alerts

Daily financial reports will be sent here at 8 AM PST alongside Telegram notifications."""
    
    try:
        response = requests.post(
            f"{API_URL}/v2/send",
            json={
                "message": message,
                "number": PHONE_NUMBER,
                "recipients": [group_id]
            }
        )
        
        if response.status_code in [200, 201]:
            print("✅ Test message sent!")
            print("\n🎉 Signal integration complete!")
            print("📊 Your daily reports will now be sent to both:")
            print("   • Telegram group")
            print("   • Signal group")
            return True
    except:
        pass
    
    return False

def main():
    print("🔍 Waiting for 'Ohms Alerts Reports' group...")
    print("=" * 50)
    print("\n📱 Please do one of the following:")
    print("1. Add +16572463906 to your 'Ohms Alerts Reports' group")
    print("   OR")
    print("2. Have the bot join using the group link")
    print("\n⏳ Checking every 5 seconds...")
    
    attempts = 0
    while attempts < 60:  # Try for 5 minutes
        group_id = check_for_group()
        
        if group_id:
            complete_setup(group_id)
            break
        
        attempts += 1
        if attempts % 12 == 0:  # Every minute
            print(f"   Still waiting... ({attempts * 5} seconds)")
        
        time.sleep(5)
    
    if attempts >= 60:
        print("\n⏰ Timeout after 5 minutes")
        print("Please add the bot to the group manually and run:")
        print("   python check_signal_status.py")

if __name__ == "__main__":
    main()