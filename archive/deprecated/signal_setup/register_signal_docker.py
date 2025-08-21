#!/usr/bin/env python3
"""
Register Signal number using Docker REST API
"""
import requests
import json
import time
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
script_dir = Path(__file__).parent
env_path = script_dir / '.env'
load_dotenv(env_path)

API_URL = "http://localhost:8080"
PHONE_NUMBER = "+16572463906"

def check_api_status():
    """Check if API is running"""
    try:
        response = requests.get(f"{API_URL}/v1/about")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Signal API is running")
            print(f"   Version: {data.get('version')}")
            print(f"   Mode: {data.get('mode')}")
            return True
    except Exception as e:
        print(f"❌ API not reachable: {e}")
    return False

def register_number():
    """Register phone number"""
    print(f"\n📱 Registering {PHONE_NUMBER}...")
    
    try:
        # Register with voice call option as backup
        response = requests.post(
            f"{API_URL}/v1/register/{PHONE_NUMBER}",
            json={"use_voice": False}
        )
        
        if response.status_code == 200:
            print("✅ Registration initiated!")
            print("📲 Check your phone for SMS verification code")
            print("   If you don't receive SMS, we can try voice call")
            return True
        else:
            print(f"❌ Registration failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error during registration: {e}")
        return False

def verify_code(code):
    """Verify SMS/Voice code"""
    print(f"\n🔐 Verifying code: {code}")
    
    try:
        response = requests.post(
            f"{API_URL}/v1/register/{PHONE_NUMBER}/verify/{code}"
        )
        
        if response.status_code == 200 or response.status_code == 204:
            print("✅ Verification successful!")
            return True
        else:
            print(f"❌ Verification failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error during verification: {e}")
        return False

def create_group():
    """Create Signal group"""
    print(f"\n👥 Creating group 'Ohms Alerts Reports'...")
    
    try:
        # Create group
        response = requests.post(
            f"{API_URL}/v1/groups/{PHONE_NUMBER}",
            json={
                "name": "Ohms Alerts Reports",
                "members": [PHONE_NUMBER]  # Just ourselves initially
            }
        )
        
        if response.status_code == 200 or response.status_code == 201:
            data = response.json()
            group_id = data.get('id', data.get('group_id'))
            print(f"✅ Group created!")
            print(f"📝 Group ID: {group_id}")
            return group_id
        else:
            print(f"❌ Group creation failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ Error creating group: {e}")
        return None

def list_groups():
    """List all groups"""
    print(f"\n📋 Listing groups for {PHONE_NUMBER}...")
    
    try:
        response = requests.get(f"{API_URL}/v1/groups/{PHONE_NUMBER}")
        
        if response.status_code == 200:
            groups = response.json()
            if groups:
                print("✅ Groups found:")
                for group in groups:
                    print(f"   - {group.get('name', 'Unknown')}: {group.get('id', group.get('group_id'))}")
            else:
                print("ℹ️  No groups found")
            return groups
        else:
            print(f"❌ Failed to list groups: {response.status_code}")
            return []
            
    except Exception as e:
        print(f"❌ Error listing groups: {e}")
        return []

def test_send_message(group_id):
    """Test sending a message"""
    print(f"\n📤 Testing message send to group {group_id[:8]}...")
    
    test_message = "🚀 Test message from Ohms Alerts Reports automation"
    
    try:
        response = requests.post(
            f"{API_URL}/v2/send",
            json={
                "message": test_message,
                "number": PHONE_NUMBER,
                "recipients": [group_id]
            }
        )
        
        if response.status_code == 200 or response.status_code == 201:
            print("✅ Test message sent successfully!")
            return True
        else:
            print(f"❌ Message send failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error sending message: {e}")
        return False

def save_config(group_id):
    """Save configuration to .env"""
    env_vars = {}
    
    # Read existing .env
    if os.path.exists(env_path):
        with open(env_path, 'r') as f:
            for line in f:
                if '=' in line and not line.strip().startswith('#'):
                    key, value = line.strip().split('=', 1)
                    env_vars[key] = value
    
    # Update Signal configuration
    env_vars['SIGNAL_PHONE_NUMBER'] = PHONE_NUMBER
    env_vars['SIGNAL_GROUP_ID'] = group_id
    env_vars['SIGNAL_API_URL'] = API_URL
    
    # Write back
    with open(env_path, 'w') as f:
        for key, value in env_vars.items():
            f.write(f"{key}={value}\n")
    
    print(f"\n✅ Configuration saved to {env_path}")

def main():
    """Main registration flow"""
    print("🚀 Signal Registration via Docker API")
    print("=" * 50)
    
    # Check API status
    if not check_api_status():
        print("\n❌ Signal API is not running!")
        print("   Make sure Docker container is running:")
        print("   sudo docker ps | grep signal-api")
        return
    
    # Check if already registered
    groups = list_groups()
    
    if groups:
        print("\n✅ Phone number appears to be registered!")
        
        # Look for our group
        ohms_group = None
        for group in groups:
            if "Ohms Alerts Reports" in group.get('name', ''):
                ohms_group = group
                break
        
        if ohms_group:
            group_id = ohms_group.get('id', ohms_group.get('group_id'))
            print(f"\n✅ Found existing group: {group_id}")
            save_config(group_id)
            test_send_message(group_id)
        else:
            # Create new group
            response = input("\nCreate new group? (y/n): ")
            if response.lower() == 'y':
                group_id = create_group()
                if group_id:
                    save_config(group_id)
                    test_send_message(group_id)
    else:
        # New registration
        print("\n📱 Starting new registration...")
        
        if register_number():
            code = input("\nEnter verification code from SMS: ")
            
            if verify_code(code):
                time.sleep(2)
                
                # Create group
                group_id = create_group()
                if group_id:
                    save_config(group_id)
                    test_send_message(group_id)
                else:
                    # List groups and let user choose
                    groups = list_groups()
                    if groups:
                        print("\nEnter the group ID for 'Ohms Alerts Reports':")
                        group_id = input("Group ID: ")
                        if group_id:
                            save_config(group_id)
                            test_send_message(group_id)

if __name__ == "__main__":
    main()