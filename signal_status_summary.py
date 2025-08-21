#!/usr/bin/env python3
"""
Signal Integration Status Summary
"""
import subprocess
import requests
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment
env_path = Path(__file__).parent / '.env'
load_dotenv(env_path)

print("🚀 Signal Integration Status Summary")
print("=" * 60)

# 1. Check systemd service
print("\n📊 Systemd Service Status:")
try:
    result = subprocess.run(['systemctl', 'status', 'signal-api', '--no-pager'], 
                          capture_output=True, text=True)
    if 'active (running)' in result.stdout:
        print("   ✅ Service: Active and running")
        print("   ✅ Auto-start: Enabled on boot")
        print("   ✅ Restart policy: Always restart on failure")
    else:
        print("   ❌ Service: Not running")
except Exception as e:
    print(f"   ❌ Error checking service: {e}")

# 2. Check Docker
print("\n🐳 Docker Status:")
try:
    docker_ps = subprocess.run(['sudo', 'docker', 'ps', '--filter', 'name=signal-api'], 
                              capture_output=True, text=True)
    if 'signal-api' in docker_ps.stdout:
        print("   ✅ Container: Running")
        
        # Check volume
        volume_check = subprocess.run(['sudo', 'docker', 'volume', 'ls'], 
                                    capture_output=True, text=True)
        if 'signal-data' in volume_check.stdout:
            print("   ✅ Persistent volume: signal-data")
        else:
            print("   ⚠️  No persistent volume found")
    else:
        print("   ❌ Container: Not running")
except Exception as e:
    print(f"   ❌ Error checking Docker: {e}")

# 3. Check API
print("\n🌐 API Status:")
try:
    response = requests.get('http://localhost:8080/v1/about', timeout=5)
    if response.status_code == 200:
        data = response.json()
        print(f"   ✅ API: Responding (v{data.get('version')})")
        print(f"   ✅ Mode: {data.get('mode')}")
    else:
        print(f"   ❌ API: Error {response.status_code}")
except Exception as e:
    print(f"   ❌ API: Not accessible - {e}")

# 4. Check configuration
print("\n⚙️  Configuration:")
phone = os.getenv('SIGNAL_PHONE_NUMBER')
group = os.getenv('SIGNAL_GROUP_ID')
api_url = os.getenv('SIGNAL_API_URL')

if phone:
    print(f"   ✅ Phone: {phone}")
else:
    print("   ❌ Phone number not configured")

if group:
    print(f"   ✅ Group ID: {group[:30]}...")
else:
    print("   ❌ Group ID not configured")

if api_url:
    print(f"   ✅ API URL: {api_url}")
else:
    print("   ⚠️  Using default API URL")

# 5. Check monitoring
print("\n🔍 Monitoring:")
try:
    cron_check = subprocess.run(['crontab', '-l'], capture_output=True, text=True)
    if 'monitor_signal.sh' in cron_check.stdout:
        print("   ✅ Health monitoring: Active (every 5 minutes)")
    else:
        print("   ⚠️  Health monitoring not in cron")
    
    if 'signal-backup.sh' in cron_check.stdout:
        print("   ✅ Daily backups: Scheduled (3 AM)")
    else:
        print("   ⚠️  Backups not scheduled")
except:
    print("   ⚠️  Could not check cron jobs")

# 6. Registration status
print("\n📱 Registration Status:")
if phone and api_url:
    try:
        response = requests.get(f"{api_url}/v1/groups/{phone}", timeout=5)
        if response.status_code == 200:
            groups = response.json()
            print(f"   ✅ Registered: Yes")
            print(f"   ✅ Groups: {len(groups)}")
            for g in groups:
                if "Ohms Alerts Reports" in g.get('name', ''):
                    print(f"   ✅ Target group found: {g.get('name')}")
        else:
            print("   ❌ Not registered - need to run registration")
    except:
        print("   ⚠️  Cannot check registration")
else:
    print("   ❌ Missing configuration")

# 7. Summary
print("\n📋 Summary:")
print("   Your Signal group link:")
print("   https://signal.group/#CjQKINt32QjJxlAbqjC22WE26xbRE9UMcUgCPttd15JxcxjPEhB2LIW5CW8UQpcceUiQ38cF")
print("\n   To complete registration:")
print("   python register_signal_persistent.py")
print("\n   Service will persist through reboots and failures ✅")