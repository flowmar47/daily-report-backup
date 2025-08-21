#!/usr/bin/env python3
"""
Monitor Signal group membership status and alert on issues
"""

import asyncio
import json
import os
import sys
from datetime import datetime
from pathlib import Path
import httpx

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from utils.env_config import EnvironmentConfig

async def check_signal_group_status():
    """Check Signal group membership status"""
    
    # Load environment config
    env_config = EnvironmentConfig('daily_report')
    config = env_config.get_all_vars()
    
    phone_number = config.get('SIGNAL_PHONE_NUMBER', '+16572463906')
    group_id = config.get('SIGNAL_GROUP_ID')
    api_url = config.get('SIGNAL_API_URL', 'http://localhost:8080')
    
    print("=" * 70)
    print(f"SIGNAL GROUP MEMBERSHIP STATUS - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)
    
    async with httpx.AsyncClient(base_url=api_url, timeout=30.0) as client:
        try:
            # Get group information
            response = await client.get(f"/v1/groups/{phone_number}")
            
            if response.status_code != 200:
                print(f"[ERROR] Failed to get groups: HTTP {response.status_code}")
                print(f"Response: {response.text}")
                return False
            
            groups = response.json()
            
            # Find our target group
            target_group = None
            for group in groups:
                if group.get('id') == group_id:
                    target_group = group
                    break
            
            if not target_group:
                print(f"[WARNING] Group {group_id} not found!")
                print("\nAvailable groups:")
                for group in groups:
                    print(f"  - {group.get('name', 'Unnamed')}: {group.get('id')}")
                return False
            
            # Analyze membership status
            print(f"\nGroup: {target_group.get('name', 'Unnamed')}")
            print(f"Group ID: {target_group.get('id')}")
            print(f"Description: {target_group.get('description', 'No description')}")
            print("-" * 70)
            
            members = target_group.get('members', [])
            admins = target_group.get('admins', [])
            pending_requests = target_group.get('pending_requests', [])
            pending_invites = target_group.get('pending_invites', [])
            
            # Check our status
            is_member = phone_number in members or any(phone_number in str(m) for m in members)
            is_admin = phone_number in admins
            has_pending_request = phone_number in pending_requests
            
            print(f"\nSender Status ({phone_number}):")
            print(f"  - Is Member: {'YES' if is_member else 'NO'}")
            print(f"  - Is Admin: {'YES' if is_admin else 'NO'}")
            print(f"  - Has Pending Request: {'YES' if has_pending_request else 'NO'}")
            
            # Display group statistics
            print(f"\nGroup Statistics:")
            print(f"  - Total Members: {len(members)}")
            print(f"  - Total Admins: {len(admins)}")
            print(f"  - Pending Requests: {len(pending_requests)}")
            print(f"  - Pending Invites: {len(pending_invites)}")
            
            # List pending requests if any
            if pending_requests:
                print(f"\n[WARNING] Pending join requests that need approval:")
                for req in pending_requests:
                    print(f"  - {req}")
                print("\n  ACTION REQUIRED: An admin needs to accept these requests in the Signal app")
            
            # Determine overall status
            if has_pending_request:
                print("\n[ISSUE] The sender has a pending join request!")
                print("SOLUTION: An admin needs to accept the request in the Signal app")
                print("Note: Messages may still be sent but might not reach all members")
                return False
            elif is_member and is_admin:
                print("\n[OK] Sender is properly configured as an admin member")
                return True
            elif is_member:
                print("\n[OK] Sender is a member of the group")
                return True
            else:
                print("\n[CRITICAL] Sender is not a member of the group!")
                print("SOLUTION: Add the sender to the group or check configuration")
                return False
                
        except Exception as e:
            print(f"\n[ERROR] Failed to check status: {e}")
            import traceback
            traceback.print_exc()
            return False

async def test_message_delivery():
    """Test actual message delivery"""
    print("\n" + "=" * 70)
    print("TESTING MESSAGE DELIVERY")
    print("=" * 70)
    
    env_config = EnvironmentConfig('daily_report')
    config = env_config.get_all_vars()
    
    phone_number = config.get('SIGNAL_PHONE_NUMBER', '+16572463906')
    group_id = config.get('SIGNAL_GROUP_ID')
    api_url = config.get('SIGNAL_API_URL', 'http://localhost:8080')
    
    async with httpx.AsyncClient(base_url=api_url, timeout=30.0) as client:
        try:
            payload = {
                "number": phone_number,
                "recipients": [group_id],
                "message": f"Monitor test at {datetime.now().strftime('%H:%M:%S')}"
            }
            
            response = await client.post('/v2/send', json=payload)
            
            if response.status_code == 201:
                print("[SUCCESS] Test message sent successfully")
                result = response.json()
                print(f"Timestamp: {result.get('timestamp')}")
                return True
            else:
                print(f"[FAILED] Message send failed: HTTP {response.status_code}")
                print(f"Response: {response.text}")
                return False
                
        except Exception as e:
            print(f"[ERROR] Failed to send test message: {e}")
            return False

async def main():
    """Main monitoring function"""
    # Check group status
    status_ok = await check_signal_group_status()
    
    # Test delivery
    if status_ok or True:  # Always test even if status shows issues
        delivery_ok = await test_message_delivery()
    else:
        delivery_ok = False
    
    print("\n" + "=" * 70)
    print("MONITORING COMPLETE")
    print("=" * 70)
    
    if status_ok and delivery_ok:
        print("[RESULT] All systems operational")
        return 0
    elif delivery_ok:
        print("[RESULT] Messages delivering despite membership issues")
        return 0
    else:
        print("[RESULT] Issues detected - manual intervention may be required")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)