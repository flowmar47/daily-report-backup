#!/usr/bin/env python3
"""
Check Signal Docker setup status
"""
import requests
import subprocess
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
script_dir = Path(__file__).parent
env_path = script_dir / '.env'
load_dotenv(env_path)

API_URL = "http://localhost:8080"

def check_docker():
    """Check Docker container status"""
    print("🐳 Docker Status:")
    
    try:
        result = subprocess.run(['sudo', 'docker', 'ps'], capture_output=True, text=True)
        if 'signal-api' in result.stdout:
            print("   ✅ Signal API container is running")
            return True
        else:
            print("   ❌ Signal API container not found")
            print("   💡 Start with: sudo docker start signal-api")
            return False
    except Exception as e:
        print(f"   ❌ Error checking Docker: {e}")
        return False

def check_api():
    """Check API connectivity"""
    print("\n🌐 API Status:")
    
    try:
        response = requests.get(f"{API_URL}/v1/about", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ API responding (v{data.get('version')}, {data.get('mode')} mode)")
            return True
        else:
            print(f"   ❌ API error: {response.status_code}")
            return False
    except Exception as e:
        print(f"   ❌ Cannot connect to API: {e}")
        return False

def check_registration():
    """Check if phone number is registered"""
    print("\n📱 Registration Status:")
    
    phone = os.getenv('SIGNAL_PHONE_NUMBER', '+16572463906')
    
    try:
        response = requests.get(f"{API_URL}/v1/groups/{phone}")
        
        if response.status_code == 200:
            groups = response.json()
            print(f"   ✅ Phone {phone} is registered")
            if groups:
                print(f"   📊 Found {len(groups)} groups:")
                for group in groups:
                    print(f"      - {group.get('name', 'Unknown')}")
            else:
                print("   ℹ️  No groups found")
            return True
        else:
            print(f"   ❌ Phone {phone} not registered")
            print("   💡 Register with: python register_signal_captcha.py")
            return False
    except Exception as e:
        print(f"   ❌ Error checking registration: {e}")
        return False

def check_config():
    """Check configuration"""
    print("\n⚙️  Configuration:")
    
    phone = os.getenv('SIGNAL_PHONE_NUMBER')
    group_id = os.getenv('SIGNAL_GROUP_ID')
    api_url = os.getenv('SIGNAL_API_URL')
    
    if phone:
        print(f"   ✅ SIGNAL_PHONE_NUMBER: {phone}")
    else:
        print("   ❌ SIGNAL_PHONE_NUMBER not set")
    
    if group_id:
        print(f"   ✅ SIGNAL_GROUP_ID: {group_id[:20]}...")
    else:
        print("   ❌ SIGNAL_GROUP_ID not set")
    
    if api_url:
        print(f"   ✅ SIGNAL_API_URL: {api_url}")
    else:
        print(f"   ⚠️  SIGNAL_API_URL defaulting to {API_URL}")
    
    return bool(phone and group_id)

def test_messaging():
    """Test message sending"""
    print("\n📤 Message Test:")
    
    phone = os.getenv('SIGNAL_PHONE_NUMBER')
    group_id = os.getenv('SIGNAL_GROUP_ID')
    
    if not phone or not group_id:
        print("   ⏭️  Skipped - configuration incomplete")
        return False
    
    try:
        response = requests.post(
            f"{API_URL}/v2/send",
            json={
                "message": "🧪 Signal test from Ohms Alerts Reports system",
                "number": phone,
                "recipients": [group_id]
            },
            timeout=10
        )
        
        if response.status_code in [200, 201]:
            print("   ✅ Test message sent successfully!")
            return True
        else:
            print(f"   ❌ Message failed: {response.status_code}")
            print(f"      {response.text}")
            return False
    except Exception as e:
        print(f"   ❌ Error sending message: {e}")
        return False

def main():
    """Main status check"""
    print("🔍 Signal Integration Status Check")
    print("=" * 50)
    
    docker_ok = check_docker()
    api_ok = check_api() if docker_ok else False
    registration_ok = check_registration() if api_ok else False
    config_ok = check_config()
    messaging_ok = test_messaging() if config_ok else False
    
    print("\n📋 Summary:")
    print(f"   Docker Container: {'✅' if docker_ok else '❌'}")
    print(f"   API Connectivity: {'✅' if api_ok else '❌'}")
    print(f"   Phone Registration: {'✅' if registration_ok else '❌'}")
    print(f"   Configuration: {'✅' if config_ok else '❌'}")
    print(f"   Message Sending: {'✅' if messaging_ok else '❌'}")
    
    if all([docker_ok, api_ok, registration_ok, config_ok, messaging_ok]):
        print("\n🎉 Signal integration is fully working!")
        print("   Messages will be sent to both Telegram and Signal")
    else:
        print("\n⚠️  Signal integration needs setup")
        print("\n💡 Next steps:")
        if not docker_ok:
            print("   1. Start Docker container: sudo docker start signal-api")
        elif not registration_ok:
            print("   1. Register phone: python register_signal_captcha.py")
        elif not config_ok:
            print("   1. Complete configuration in .env file")

if __name__ == "__main__":
    main()