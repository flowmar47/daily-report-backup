#!/usr/bin/env python3
"""
Register Signal with CAPTCHA support
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

def register_with_captcha():
    """Register with CAPTCHA"""
    print("📱 Signal Registration with CAPTCHA")
    print("=" * 50)
    print("\n⚠️  CAPTCHA Required!")
    print("\n1. Open this URL in your browser:")
    print("   https://signalcaptchas.org/registration/generate.html")
    print("\n2. Solve the CAPTCHA puzzle")
    print("\n3. After solving, right-click on 'Open Signal' button")
    print("4. Select 'Copy Link Address'")
    print("5. Paste the ENTIRE link below")
    print("\nExample: signalcaptcha://signal-recaptcha-v2.6LfBXs0bAAAAAAjkDyyI1Lk5gBAUWfhI_bIyox5W...")
    
    captcha_url = input("\nPaste CAPTCHA link here: ").strip()
    
    # Extract token from URL
    if captcha_url.startswith("signalcaptcha://"):
        captcha_token = captcha_url.replace("signalcaptcha://", "")
    else:
        captcha_token = captcha_url
    
    print(f"\n🔐 Using CAPTCHA token: {captcha_token[:50]}...")
    
    # Register with CAPTCHA
    try:
        response = requests.post(
            f"{API_URL}/v1/register/{PHONE_NUMBER}",
            json={"captcha": captcha_token}
        )
        
        if response.status_code == 200:
            print("\n✅ Registration initiated!")
            print("📲 Check your phone for SMS verification code")
            return True
        else:
            print(f"\n❌ Registration failed: {response.status_code}")
            print(f"Response: {response.text}")
            
            if "Invalid captcha" in response.text:
                print("\n💡 Tips:")
                print("- Make sure you solved the CAPTCHA correctly")
                print("- Copy the ENTIRE link, not just part of it")
                print("- Try getting a fresh CAPTCHA")
            return False
            
    except Exception as e:
        print(f"\n❌ Error: {e}")
        return False

def verify_code(code):
    """Verify SMS code"""
    print(f"\n🔐 Verifying code: {code}")
    
    try:
        response = requests.post(
            f"{API_URL}/v1/register/{PHONE_NUMBER}/verify/{code}"
        )
        
        if response.status_code in [200, 204]:
            print("✅ Verification successful!")
            return True
        else:
            print(f"❌ Verification failed: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def create_group():
    """Create Signal group"""
    print("\n👥 Creating group 'Ohms Alerts Reports'...")
    
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
            group_id = data.get('id', data.get('group_id'))
            print(f"✅ Group created!")
            print(f"📝 Group ID: {group_id}")
            return group_id
        else:
            print(f"❌ Group creation failed: {response.status_code}")
            print(f"Response: {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return None

def list_groups():
    """List groups"""
    try:
        response = requests.get(f"{API_URL}/v1/groups/{PHONE_NUMBER}")
        
        if response.status_code == 200:
            groups = response.json()
            if groups:
                print("\n📋 Your Signal groups:")
                for i, group in enumerate(groups):
                    print(f"{i+1}. {group.get('name', 'Unknown')}")
                    print(f"   ID: {group.get('id', group.get('internal_id', 'Unknown'))}")
                return groups
            else:
                print("\nℹ️  No groups found")
                return []
        else:
            return []
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return []

def test_message(group_id):
    """Send test message"""
    print(f"\n📤 Sending test message...")
    
    try:
        response = requests.post(
            f"{API_URL}/v2/send",
            json={
                "message": "🚀 Ohms Alerts Reports - Signal integration successful!",
                "number": PHONE_NUMBER,
                "recipients": [group_id]
            }
        )
        
        if response.status_code in [200, 201]:
            print("✅ Test message sent!")
            return True
        else:
            print(f"❌ Failed: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def save_config(group_id):
    """Save configuration"""
    try:
        set_key(env_path, 'SIGNAL_PHONE_NUMBER', PHONE_NUMBER)
        set_key(env_path, 'SIGNAL_GROUP_ID', group_id)
        set_key(env_path, 'SIGNAL_API_URL', API_URL)
        print(f"\n✅ Configuration saved to {env_path}")
        return True
    except Exception as e:
        print(f"\n❌ Error saving config: {e}")
        return False

def main():
    """Main flow"""
    print("🚀 Signal Docker Registration Helper")
    print("=" * 50)
    
    # Check API
    try:
        response = requests.get(f"{API_URL}/v1/about")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Signal API running (v{data.get('version')})")
        else:
            print("❌ Signal API not responding!")
            print("Make sure Docker container is running:")
            print("  sudo docker ps | grep signal-api")
            return
    except Exception as e:
        print(f"❌ Cannot connect to API: {e}")
        return
    
    # Check if already registered
    groups = list_groups()
    
    if groups:
        print("\n✅ Phone number is already registered!")
        
        # Look for our group
        ohms_group = None
        for group in groups:
            if "Ohms Alerts Reports" in group.get('name', ''):
                ohms_group = group
                break
        
        if ohms_group:
            group_id = ohms_group.get('id', ohms_group.get('internal_id'))
            print(f"\n✅ Found Ohms Alerts Reports group: {group_id}")
            
            # Save and test
            if save_config(group_id):
                test_message(group_id)
        else:
            # Create new group
            choice = input("\nCreate 'Ohms Alerts Reports' group? (y/n): ")
            if choice.lower() == 'y':
                group_id = create_group()
                if group_id:
                    save_config(group_id)
                    test_message(group_id)
    else:
        # New registration
        if register_with_captcha():
            code = input("\nEnter SMS verification code: ")
            
            if verify_code(code):
                print("\n⏳ Waiting for registration to complete...")
                time.sleep(3)
                
                # Create group
                group_id = create_group()
                if group_id:
                    save_config(group_id)
                    test_message(group_id)
                else:
                    # List groups
                    groups = list_groups()
                    if groups:
                        choice = input("\nEnter group number to use: ")
                        try:
                            idx = int(choice) - 1
                            if 0 <= idx < len(groups):
                                group_id = groups[idx].get('id', groups[idx].get('internal_id'))
                                save_config(group_id)
                                test_message(group_id)
                        except:
                            print("❌ Invalid selection")

if __name__ == "__main__":
    main()