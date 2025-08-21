#!/usr/bin/env python3
"""Quick Signal verification script"""
import requests
import json
import sys

API_URL = "http://localhost:8080"
PHONE_NUMBER = "+16572463906"

def main():
    print("Signal Quick Registration/Verification")
    print("=" * 40)
    
    # First, need to register with CAPTCHA
    print("\n1. Get a fresh CAPTCHA token from:")
    print("   https://signalcaptchas.org/registration/generate.html")
    
    captcha_input = input("\n2. Paste CAPTCHA URL or token: ").strip()
    
    # Extract token if full URL provided
    if captcha_input.startswith("signalcaptcha://"):
        captcha_token = captcha_input.replace("signalcaptcha://", "")
    else:
        captcha_token = captcha_input
    
    print(f"\n3. Registering with Signal...")
    
    # Register with CAPTCHA
    try:
        response = requests.post(
            f"{API_URL}/v1/register/{PHONE_NUMBER}",
            json={"captcha": captcha_token}
        )
        
        if response.status_code == 200:
            print("✅ Registration initiated! Check your phone for SMS code.")
            
            # Now verify with SMS code
            sms_code = input("\n4. Enter SMS verification code: ").strip()
            
            verify_response = requests.post(
                f"{API_URL}/v1/register/{PHONE_NUMBER}/verify/{sms_code}"
            )
            
            if verify_response.status_code == 200:
                print("✅ Phone number verified successfully!")
                
                # Create group
                print("\n5. Creating Ohms Alerts Reports group...")
                group_response = requests.post(
                    f"{API_URL}/v1/groups/{PHONE_NUMBER}",
                    json={"name": "Ohms Alerts Reports", "members": [PHONE_NUMBER]}
                )
                
                if group_response.status_code == 200:
                    group_data = group_response.json()
                    print(f"✅ Group created! ID: {group_data}")
                    
                    # Update .env file
                    from dotenv import set_key
                    from pathlib import Path
                    env_path = Path(__file__).parent / '.env'
                    
                    if 'id' in group_data:
                        set_key(env_path, 'SIGNAL_GROUP_ID', group_data['id'])
                        print(f"✅ Updated .env with group ID: {group_data['id']}")
                    
                    print("\n✅ Signal setup complete!")
                else:
                    print(f"❌ Group creation failed: {group_response.text}")
            else:
                print(f"❌ SMS verification failed: {verify_response.text}")
        else:
            print(f"❌ Registration failed: {response.text}")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    main()