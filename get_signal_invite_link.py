#!/usr/bin/env python3
"""
Get Signal group invite link
"""
import requests
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
script_dir = Path(__file__).parent
env_path = script_dir / '.env'
load_dotenv(env_path)

API_URL = os.getenv('SIGNAL_API_URL', 'http://localhost:8080')
PHONE_NUMBER = os.getenv('SIGNAL_PHONE_NUMBER', '+16572463906')
GROUP_ID = os.getenv('SIGNAL_GROUP_ID')

def get_group_invite_link():
    """Get or create group invite link"""
    print("🔗 Getting Signal group invite link...")
    
    if not GROUP_ID:
        print("❌ No group ID found in configuration")
        return
    
    try:
        # Create group invite link
        response = requests.post(
            f"{API_URL}/v1/groups/{PHONE_NUMBER}/{GROUP_ID}/link",
            json={"name": "Ohms Alerts Reports Invite"}
        )
        
        if response.status_code in [200, 201]:
            data = response.json()
            link = data.get('link', data.get('url', data.get('invite_link')))
            
            if link:
                print(f"\n✅ Signal Group Invite Link:")
                print(f"📱 {link}")
                print(f"\n💡 Share this link to invite others to the group")
                print(f"   They'll be able to join 'Ohms Alerts Reports' directly")
                return link
            else:
                print(f"⚠️ Link created but format unclear: {data}")
        else:
            print(f"❌ Failed to create invite link: {response.status_code}")
            print(f"Response: {response.text}")
            
            # Try alternative endpoint
            print("\n🔄 Trying alternative method...")
            response2 = requests.get(
                f"{API_URL}/v1/groups/{PHONE_NUMBER}/{GROUP_ID}"
            )
            
            if response2.status_code == 200:
                data = response2.json()
                print(f"Group info: {data}")
                
                # Check if invite link exists in group data
                link = data.get('invite_link', data.get('link', data.get('group_link')))
                if link:
                    print(f"\n✅ Found existing invite link:")
                    print(f"📱 {link}")
                    return link
            
    except Exception as e:
        print(f"❌ Error getting invite link: {e}")
        
        # Try to get group info
        print("\n📋 Group details:")
        print(f"   Group ID: {GROUP_ID}")
        print(f"   Phone: {PHONE_NUMBER}")
        print(f"\n💡 Manual invite process:")
        print(f"   1. Open Signal on your phone")
        print(f"   2. Go to 'Ohms Alerts Reports' group")
        print(f"   3. Tap group name at top")
        print(f"   4. Select 'Group link'")
        print(f"   5. Turn on 'Group link' if off")
        print(f"   6. Share the link")

def list_group_details():
    """Get detailed group information"""
    print("\n📊 Fetching group details...")
    
    try:
        response = requests.get(f"{API_URL}/v1/groups/{PHONE_NUMBER}")
        
        if response.status_code == 200:
            groups = response.json()
            for group in groups:
                if group.get('id') == GROUP_ID or group.get('internal_id') == GROUP_ID:
                    print(f"\n✅ Group found:")
                    print(f"   Name: {group.get('name', 'Unknown')}")
                    print(f"   ID: {GROUP_ID}")
                    print(f"   Members: {group.get('members', [])}")
                    
                    # Check for invite link in group data
                    if 'invite_link' in group:
                        print(f"   Invite Link: {group['invite_link']}")
                    elif 'link' in group:
                        print(f"   Link: {group['link']}")
                    else:
                        print(f"   Invite Link: Not found in API response")
                    
                    return group
    except Exception as e:
        print(f"❌ Error getting group details: {e}")
    
    return None

def main():
    """Main function"""
    print("🔗 Signal Group Invite Link Tool")
    print("=" * 50)
    
    # Check API
    try:
        response = requests.get(f"{API_URL}/v1/about")
        if response.status_code == 200:
            print(f"✅ Signal API connected")
        else:
            print("❌ Signal API not responding")
            return
    except:
        print("❌ Cannot connect to Signal API")
        return
    
    # Get group details first
    group = list_group_details()
    
    # Try to get invite link
    link = get_group_invite_link()
    
    if not link:
        print("\n📝 Alternative: Group Joining Instructions")
        print("=" * 50)
        print(f"Since the API doesn't support invite links directly,")
        print(f"you can add members manually:")
        print(f"\n1. Share this info with the person to add:")
        print(f"   - Your Signal number: {PHONE_NUMBER}")
        print(f"   - Group name: Ohms Alerts Reports")
        print(f"\n2. They should:")
        print(f"   - Add your number to their Signal contacts")
        print(f"   - Message you on Signal")
        print(f"\n3. You can then add them to the group:")
        print(f"   - Open Signal")
        print(f"   - Go to 'Ohms Alerts Reports' group")
        print(f"   - Tap 'Add members'")
        print(f"   - Select their contact")

if __name__ == "__main__":
    main()