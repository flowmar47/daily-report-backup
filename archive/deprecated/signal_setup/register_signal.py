#!/usr/bin/env python3
"""
Signal CLI Registration and Group Setup Script
"""
import subprocess
import time
import os
import json
import sys

PHONE_NUMBER = "+16572463906"
SIGNAL_CLI = "signal-cli"

def run_command(cmd):
    """Run command and return output"""
    print(f"Running: {cmd}")
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if result.returncode == 0:
        print(f"Success: {result.stdout}")
    else:
        print(f"Error: {result.stderr}")
    return result

def register_number():
    """Register phone number with Signal"""
    print(f"\n📱 Registering phone number: {PHONE_NUMBER}")
    print("You will receive an SMS with a verification code...")
    
    cmd = f"{SIGNAL_CLI} -u {PHONE_NUMBER} register"
    result = run_command(cmd)
    
    if result.returncode == 0:
        print("\n✅ Registration initiated!")
        print("📲 Please check your phone for the SMS verification code")
        return True
    else:
        print("\n❌ Registration failed!")
        return False

def verify_number(code):
    """Verify phone number with SMS code"""
    print(f"\n🔐 Verifying with code: {code}")
    
    cmd = f"{SIGNAL_CLI} -u {PHONE_NUMBER} verify {code}"
    result = run_command(cmd)
    
    if result.returncode == 0:
        print("\n✅ Verification successful!")
        return True
    else:
        print("\n❌ Verification failed!")
        return False

def create_group():
    """Create Signal group and get group ID"""
    print(f"\n👥 Creating group 'Ohms Alerts Reports'...")
    
    # Create group with just ourselves first
    cmd = f"{SIGNAL_CLI} -u {PHONE_NUMBER} updateGroup -n 'Ohms Alerts Reports' -m {PHONE_NUMBER}"
    result = run_command(cmd)
    
    if result.returncode == 0:
        # Get group ID from the output
        output = result.stdout
        # Signal CLI typically returns the group ID in the output
        print("\n✅ Group created!")
        
        # List groups to find our group ID
        list_cmd = f"{SIGNAL_CLI} -u {PHONE_NUMBER} listGroups"
        list_result = run_command(list_cmd)
        
        if list_result.returncode == 0:
            print("\n📋 Groups list:")
            print(list_result.stdout)
            print("\n💡 Look for 'Ohms Alerts Reports' in the list above to find the group ID")
            return True
    
    print("\n❌ Group creation failed!")
    return False

def test_send_message(group_id):
    """Test sending message to group"""
    print(f"\n📤 Testing message send to group: {group_id}")
    
    test_message = "🚀 Test message from Ohms Alerts Reports automation system"
    cmd = f'{SIGNAL_CLI} -u {PHONE_NUMBER} send -g "{group_id}" -m "{test_message}"'
    result = run_command(cmd)
    
    if result.returncode == 0:
        print("\n✅ Test message sent successfully!")
        return True
    else:
        print("\n❌ Test message failed!")
        return False

def save_config(group_id):
    """Save Signal configuration to .env file"""
    env_path = "/home/ohms/OhmsAlertsReports/daily-report/.env"
    
    # Read existing .env
    env_vars = {}
    if os.path.exists(env_path):
        with open(env_path, 'r') as f:
            for line in f:
                if '=' in line and not line.strip().startswith('#'):
                    key, value = line.strip().split('=', 1)
                    env_vars[key] = value
    
    # Add Signal configuration
    env_vars['SIGNAL_PHONE_NUMBER'] = PHONE_NUMBER
    env_vars['SIGNAL_GROUP_ID'] = group_id
    
    # Write back
    with open(env_path, 'w') as f:
        for key, value in env_vars.items():
            f.write(f"{key}={value}\n")
    
    print(f"\n✅ Configuration saved to {env_path}")

def main():
    """Main setup flow"""
    print("🚀 Signal CLI Setup for Ohms Alerts Reports")
    print("=" * 50)
    
    # Check if already registered
    check_cmd = f"{SIGNAL_CLI} -u {PHONE_NUMBER} listGroups"
    check_result = run_command(check_cmd)
    
    if check_result.returncode == 0:
        print("\n✅ Phone number already registered!")
        print("📋 Existing groups:")
        print(check_result.stdout)
        
        response = input("\nDo you want to create a new group? (y/n): ")
        if response.lower() == 'y':
            create_group()
        
        group_id = input("\nEnter the Signal group ID for 'Ohms Alerts Reports': ")
        if group_id:
            save_config(group_id)
            test_send_message(group_id)
    else:
        print("\n📱 Phone number not registered. Starting registration...")
        
        if register_number():
            code = input("\nEnter the verification code from SMS: ")
            if verify_number(code):
                time.sleep(2)
                create_group()
                group_id = input("\nEnter the Signal group ID from the list above: ")
                if group_id:
                    save_config(group_id)
                    test_send_message(group_id)

if __name__ == "__main__":
    main()