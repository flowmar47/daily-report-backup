#!/usr/bin/env python3
"""
Complete Signal verification after CAPTCHA registration
Run this after receiving the SMS code
"""
import requests
import json
import time
import os
from pathlib import Path
from dotenv import load_dotenv, set_key

# Load environment variables
script_dir = Path(__file__).parent
env_path = script_dir / '.env'
load_dotenv(env_path)

API_URL = "http://localhost:8080"
PHONE_NUMBER = "+16572463906"

def verify_sms_code(code):
    """Verify the SMS code"""
    print(f"🔐 Verifying SMS code: {code}")
    
    try:
        response = requests.post(
            f"{API_URL}/v1/register/{PHONE_NUMBER}/verify/{code}"
        )
        
        if response.status_code in [200, 204]:
            print("✅ SMS verification successful!")
            print("📱 Your Signal account is now registered!")
            return True
        else:
            print(f"❌ Verification failed: {response.status_code}")
            print(f"Response: {response.text}")
            
            if "Invalid verification code" in response.text:
                print("\n💡 Tips:")
                print("- Make sure you entered the code correctly")
                print("- The code should be 6 digits")
                print("- Try requesting a new code if this one expired")
            return False
            
    except Exception as e:
        print(f"❌ Error during verification: {e}")
        return False

def create_group():
    """Create the Ohms Alerts Reports group"""
    print(f"\n👥 Creating Signal group 'Ohms Alerts Reports'...")
    
    try:
        response = requests.post(
            f"{API_URL}/v1/groups/{PHONE_NUMBER}",
            json={
                "name": "Ohms Alerts Reports",
                "members": [PHONE_NUMBER]
            }
        )
        
        if response.status_code in [200, 201]:
            data = response.json()
            # Try different possible keys for group ID
            group_id = data.get('id') or data.get('group_id') or data.get('internal_id')
            
            if group_id:
                print(f"✅ Group created successfully!")
                print(f"📝 Group ID: {group_id}")
                return group_id
            else:
                print(f"⚠️  Group created but ID unclear: {data}")
                return data
        else:
            print(f"❌ Group creation failed: {response.status_code}")
            print(f"Response: {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ Error creating group: {e}")
        return None

def list_groups():
    """List all groups to find our group ID"""
    print(f"\n📋 Listing Signal groups...")
    
    try:
        response = requests.get(f"{API_URL}/v1/groups/{PHONE_NUMBER}")
        
        if response.status_code == 200:
            groups = response.json()
            if groups:
                print("✅ Found groups:")
                for i, group in enumerate(groups):
                    name = group.get('name', 'Unknown')
                    group_id = group.get('id') or group.get('group_id') or group.get('internal_id', 'Unknown')
                    print(f"   {i+1}. {name}")
                    print(f"      ID: {group_id}")
                return groups
            else:
                print("ℹ️  No groups found yet")
                return []
        else:
            print(f"❌ Failed to list groups: {response.status_code}")
            return []
            
    except Exception as e:
        print(f"❌ Error listing groups: {e}")
        return []

def send_test_message(group_id):
    """Send a test message to verify everything works"""
    print(f"\n📤 Sending test message to group...")
    
    test_message = """🎉 Signal Integration Complete!

✅ Phone registered: +16572463906
✅ Group created: Ohms Alerts Reports  
✅ API working: Docker container
✅ Ready for daily reports!

This is a test from the Ohms Alerts Reports automation system."""
    
    try:
        response = requests.post(
            f"{API_URL}/v2/send",
            json={
                "message": test_message,
                "number": PHONE_NUMBER,
                "recipients": [group_id]
            }
        )
        
        if response.status_code in [200, 201]:
            print("✅ Test message sent successfully!")
            print("📱 Check your Signal app to see the message")
            return True
        else:
            print(f"❌ Message send failed: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error sending message: {e}")
        return False

def save_configuration(group_id):
    """Save Signal configuration to .env file"""
    print(f"\n💾 Saving configuration...")
    
    try:
        # Update .env file
        set_key(env_path, 'SIGNAL_PHONE_NUMBER', PHONE_NUMBER)
        set_key(env_path, 'SIGNAL_GROUP_ID', str(group_id))
        set_key(env_path, 'SIGNAL_API_URL', API_URL)
        
        print("✅ Configuration saved to .env:")
        print(f"   SIGNAL_PHONE_NUMBER={PHONE_NUMBER}")
        print(f"   SIGNAL_GROUP_ID={group_id}")
        print(f"   SIGNAL_API_URL={API_URL}")
        return True
        
    except Exception as e:
        print(f"❌ Error saving configuration: {e}")
        return False

def main():
    """Main verification flow"""
    print("📱 Signal SMS Verification & Setup")
    print("=" * 50)
    
    # Check API status
    try:
        response = requests.get(f"{API_URL}/v1/about")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Signal API running (v{data.get('version')})")
        else:
            print("❌ Signal API not responding!")
            return
    except Exception as e:
        print(f"❌ Cannot connect to Signal API: {e}")
        return
    
    print(f"\n📲 Registration pending for {PHONE_NUMBER}")
    print("You should have received an SMS with a 6-digit verification code.")
    
    # Get SMS code
    sms_code = input("\nEnter the 6-digit SMS verification code: ").strip()
    
    if len(sms_code) != 6 or not sms_code.isdigit():
        print("❌ Invalid code format. Should be 6 digits.")
        return
    
    # Verify SMS code
    if verify_sms_code(sms_code):
        print("\n⏳ Waiting for registration to complete...")
        time.sleep(3)
        
        # Create group
        group_id = create_group()
        
        if not group_id:
            # Try listing groups in case it was created
            groups = list_groups()
            if groups:
                print("\nSelect the group to use for alerts:")
                for i, group in enumerate(groups):
                    print(f"{i+1}. {group.get('name', 'Unknown')}")
                
                try:
                    choice = int(input("Enter group number: ")) - 1
                    if 0 <= choice < len(groups):
                        group_id = groups[choice].get('id') or groups[choice].get('group_id') or groups[choice].get('internal_id')
                except:
                    print("❌ Invalid selection")
                    return
        
        if group_id:
            # Save configuration
            if save_configuration(group_id):
                # Send test message
                if send_test_message(group_id):
                    print("\n🎉 Signal Integration Complete!")
                    print("\n✅ Your system will now send daily reports to:")
                    print("   📱 Telegram group")  
                    print("   📱 Signal group")
                    print("\n📅 Next report scheduled for 8:00 AM PST on weekdays")
                    print("\n🧪 Test the integration anytime with:")
                    print("   python check_signal_status.py")
        else:
            print("❌ Could not determine group ID")
    else:
        print("\n❌ SMS verification failed")
        print("💡 You can try running this script again with a new code")

if __name__ == "__main__":
    main()