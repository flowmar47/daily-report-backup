#!/usr/bin/env python3
"""
Register Signal with persistent storage
"""
import requests
import json
import time
import os
import sys
from pathlib import Path
from dotenv import load_dotenv, set_key

# Load environment variables
script_dir = Path(__file__).parent
env_path = script_dir / '.env'
load_dotenv(env_path)

API_URL = "http://localhost:8080"
PHONE_NUMBER = "+16572463906"

def check_service_status():
    """Check if Signal API service is running"""
    print("🔍 Checking Signal API service...")
    
    # Check systemd service
    import subprocess
    result = subprocess.run(['systemctl', 'is-active', 'signal-api'], capture_output=True, text=True)
    if result.stdout.strip() == 'active':
        print("✅ Signal API service is active")
    else:
        print("❌ Signal API service is not active")
        print("   Run: sudo systemctl start signal-api")
        return False
    
    # Check API
    try:
        response = requests.get(f"{API_URL}/v1/about", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ API responding (v{data.get('version')})")
            return True
    except:
        print("❌ API not responding")
        return False
    
    return False

def register_with_captcha():
    """Register with CAPTCHA"""
    print("\n📱 Signal Registration")
    print("=" * 50)
    print("\n⚠️  CAPTCHA Required for Registration")
    print("\n📝 Steps:")
    print("1. Open: https://signalcaptchas.org/registration/generate.html")
    print("2. Solve the CAPTCHA puzzle")
    print("3. Right-click 'Open Signal' button → 'Copy Link Address'")
    print("4. Paste the ENTIRE link below")
    print("\nExample format: signalcaptcha://signal-recaptcha-v2.6LfBXs0b...")
    
    captcha_url = input("\n🔗 Paste CAPTCHA link: ").strip()
    
    if not captcha_url:
        print("❌ No CAPTCHA provided")
        return False
    
    # Extract token
    if captcha_url.startswith("signalcaptcha://"):
        captcha_token = captcha_url.replace("signalcaptcha://", "")
    else:
        captcha_token = captcha_url
    
    print(f"\n🔐 Registering with CAPTCHA...")
    
    try:
        response = requests.post(
            f"{API_URL}/v1/register/{PHONE_NUMBER}",
            json={"captcha": captcha_token},
            timeout=30
        )
        
        if response.status_code in [200, 201]:
            print("✅ Registration initiated!")
            print("📲 Check +16572463906 for SMS verification code")
            return True
        else:
            print(f"❌ Registration failed: {response.status_code}")
            print(f"Response: {response.text}")
            if "Invalid captcha" in response.text:
                print("\n💡 Try getting a fresh CAPTCHA")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def verify_sms(code):
    """Verify SMS code"""
    print(f"\n🔐 Verifying code: {code}")
    
    try:
        response = requests.post(
            f"{API_URL}/v1/register/{PHONE_NUMBER}/verify/{code}",
            timeout=30
        )
        
        if response.status_code in [200, 201, 204]:
            print("✅ Verification successful!")
            return True
        else:
            print(f"❌ Verification failed: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def find_existing_group():
    """Find existing Ohms Alerts Reports group"""
    print("\n🔍 Looking for existing groups...")
    
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
                    print(f"   ID: {group_id}")
                    return group_id
            
            # List all groups
            if groups:
                print("\n📋 Available groups:")
                for i, group in enumerate(groups, 1):
                    print(f"{i}. {group.get('name', 'Unknown')}")
                    print(f"   ID: {group.get('id', 'Unknown')}")
                
                choice = input("\nSelect group number (or press Enter to skip): ")
                if choice.isdigit():
                    idx = int(choice) - 1
                    if 0 <= idx < len(groups):
                        return groups[idx].get('id') or groups[idx].get('internal_id')
        
        return None
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return None

def join_group_by_link():
    """Join group using the provided link"""
    print("\n🔗 Joining group from link...")
    print("Your group link: https://signal.group/#CjQKINt32QjJxlAbqjC22WE26xbRE9UMcUgCPttd15JxcxjPEhB2LIW5CW8UQpcceUiQ38cF")
    
    # Note: Signal CLI REST API doesn't directly support joining by link
    # User needs to join manually or we need to parse the group ID
    print("\n📱 To join your existing group:")
    print("1. Open Signal on your phone")
    print("2. Use the group link to join")
    print("3. The bot will see the group after you join")
    
    input("\nPress Enter after joining the group...")
    
    # Check for groups again
    return find_existing_group()

def save_config(group_id):
    """Save configuration"""
    print(f"\n💾 Saving configuration...")
    
    try:
        set_key(env_path, 'SIGNAL_PHONE_NUMBER', PHONE_NUMBER)
        set_key(env_path, 'SIGNAL_GROUP_ID', group_id)
        set_key(env_path, 'SIGNAL_API_URL', API_URL)
        
        print("✅ Configuration saved!")
        print(f"   Phone: {PHONE_NUMBER}")
        print(f"   Group: {group_id}")
        print(f"   API: {API_URL}")
        return True
        
    except Exception as e:
        print(f"❌ Error saving config: {e}")
        return False

def test_message(group_id):
    """Send test message"""
    print(f"\n📤 Sending test message...")
    
    test_msg = f"""🎉 Signal Integration Restored!

✅ Persistent storage configured
✅ Auto-restart enabled
✅ Daily backups scheduled
✅ Ready for automated alerts

Time: {time.strftime('%Y-%m-%d %H:%M:%S')}"""
    
    try:
        response = requests.post(
            f"{API_URL}/v2/send",
            json={
                "message": test_msg,
                "number": PHONE_NUMBER,
                "recipients": [group_id]
            },
            timeout=30
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
    """Main registration flow"""
    print("🚀 Signal Persistent Registration")
    print("=" * 50)
    
    # Check service
    if not check_service_status():
        print("\n❌ Please ensure Signal API service is running")
        return
    
    # Check if already registered
    existing_group = find_existing_group()
    
    if existing_group:
        print("\n✅ Already registered!")
        save_config(existing_group)
        test_message(existing_group)
        return
    
    # New registration
    print("\n📱 Starting new registration...")
    
    if not register_with_captcha():
        return
    
    # Get SMS code
    sms_code = input("\n📲 Enter 6-digit SMS code: ").strip()
    
    if not sms_code.isdigit() or len(sms_code) != 6:
        print("❌ Invalid code format")
        return
    
    if not verify_sms(sms_code):
        return
    
    print("\n⏳ Waiting for registration to complete...")
    time.sleep(5)
    
    # Try to find or join group
    group_id = find_existing_group()
    
    if not group_id:
        group_id = join_group_by_link()
    
    if group_id:
        save_config(group_id)
        test_message(group_id)
        
        print("\n✅ Signal integration complete!")
        print("\n📊 Persistence features:")
        print("   • Docker volume for data persistence")
        print("   • Systemd service with auto-restart")
        print("   • Starts automatically on boot")
        print("   • Daily backups at 3 AM")
        print("\n🎯 Your daily reports will now be sent to both:")
        print("   • Telegram group")
        print("   • Signal group")
    else:
        print("\n⚠️ Could not find group")
        print("Please join the group manually and run this script again")

if __name__ == "__main__":
    main()