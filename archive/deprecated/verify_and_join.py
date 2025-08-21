#!/usr/bin/env python3
"""
Verify SMS and join existing group
"""
import requests
import time
import sys
from pathlib import Path
from dotenv import load_dotenv, set_key

# Load environment
env_path = Path(__file__).parent / '.env'
load_dotenv(env_path)

API_URL = "http://localhost:8080"
PHONE_NUMBER = "+16572463906"
YOUR_GROUP_LINK = "https://signal.group/#CjQKINt32QjJxlAbqjC22WE26xbRE9UMcUgCPttd15JxcxjPEhB2LIW5CW8UQpcceUiQ38cF"

def verify_sms(code):
    """Verify SMS code"""
    print(f"🔐 Verifying SMS code: {code}")
    
    try:
        response = requests.post(
            f"{API_URL}/v1/register/{PHONE_NUMBER}/verify/{code}",
            timeout=30
        )
        
        if response.status_code in [200, 201, 204]:
            print("✅ SMS verification successful!")
            print("📱 Your Signal account is now active!")
            return True
        else:
            print(f"❌ Verification failed: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def find_group():
    """Find the Ohms Alerts Reports group"""
    print("\n🔍 Looking for your groups...")
    
    try:
        response = requests.get(f"{API_URL}/v1/groups/{PHONE_NUMBER}")
        
        if response.status_code == 200:
            groups = response.json()
            print(f"✅ Found {len(groups)} groups")
            
            # Look for Ohms Alerts Reports
            for group in groups:
                if "Ohms Alerts Reports" in group.get('name', ''):
                    group_id = group.get('id') or group.get('internal_id')
                    print(f"\n✅ Found 'Ohms Alerts Reports' group!")
                    print(f"   Group ID: {group_id}")
                    return group_id
            
            # List all groups if not found
            if groups:
                print("\n📋 Your groups:")
                for i, group in enumerate(groups, 1):
                    name = group.get('name', 'Unknown')
                    gid = group.get('id', group.get('internal_id', 'Unknown'))
                    print(f"{i}. {name}")
                    print(f"   ID: {gid}")
            else:
                print("ℹ️  No groups found yet")
                print("\n💡 You may need to:")
                print("1. Open Signal on your phone")
                print(f"2. Join the group using: {YOUR_GROUP_LINK}")
                print("3. Run this script again")
        
        return None
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return None

def save_config(group_id):
    """Save configuration"""
    print(f"\n💾 Saving configuration...")
    
    try:
        set_key(env_path, 'SIGNAL_PHONE_NUMBER', PHONE_NUMBER)
        set_key(env_path, 'SIGNAL_GROUP_ID', group_id)
        set_key(env_path, 'SIGNAL_API_URL', API_URL)
        
        print("✅ Configuration saved!")
        return True
        
    except Exception as e:
        print(f"❌ Error saving config: {e}")
        return False

def test_message(group_id):
    """Send test message"""
    print(f"\n📤 Sending test message...")
    
    message = f"""🎉 Signal Integration Complete!

✅ Registration verified
✅ Group connected
✅ Persistent storage active
✅ Auto-restart enabled

Your daily financial reports will now be sent here automatically at 8 AM PST!

Group Link: {YOUR_GROUP_LINK}"""
    
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
            return True
        else:
            print(f"❌ Send failed: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def main():
    if len(sys.argv) < 2:
        print("Usage: python verify_and_join.py <SMS_CODE>")
        print("Example: python verify_and_join.py 123456")
        return
    
    sms_code = sys.argv[1].strip()
    
    print("📱 Signal Verification & Group Setup")
    print("=" * 50)
    
    # Verify SMS
    if not verify_sms(sms_code):
        print("\n❌ Verification failed. Please check the code and try again.")
        return
    
    print("\n⏳ Waiting for registration to complete...")
    time.sleep(3)
    
    # Find group
    group_id = find_group()
    
    if group_id:
        # Save and test
        if save_config(group_id):
            test_message(group_id)
            print("\n🎉 Complete! Signal is now fully integrated!")
            print(f"\n📱 Group link: {YOUR_GROUP_LINK}")
            print("📊 Daily reports will be sent to both Telegram and Signal")
    else:
        print("\n⚠️  Group not found in your Signal account")
        print("\n📝 Next steps:")
        print("1. Open Signal on your phone")
        print(f"2. Click this link: {YOUR_GROUP_LINK}")
        print("3. Join the group")
        print("4. Run: python check_signal_status.py")
        print("\nThe bot will find the group once you've joined it.")

if __name__ == "__main__":
    main()