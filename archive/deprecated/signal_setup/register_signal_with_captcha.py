#!/usr/bin/env python3
"""Register Signal number with Docker API using captcha."""

import os
import sys
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

SIGNAL_API_URL = os.getenv('SIGNAL_API_URL', 'http://localhost:8080')
SIGNAL_PHONE_NUMBER = os.getenv('SIGNAL_PHONE_NUMBER', '+16572463906')

def register_with_captcha():
    """Register Signal number with captcha."""
    print(f"Registering Signal number: {SIGNAL_PHONE_NUMBER}")
    print("\nPlease follow these steps:")
    print("1. Open https://signalcaptchas.org/registration/generate.html in your browser")
    print("2. Solve the captcha")
    print("3. Right-click on the 'Open Signal' link and copy the link")
    print("4. Paste the link here and press Enter")
    print("\nThe link should look like: signalcaptcha://signal-recaptcha-v2.LONG_TOKEN_HERE\n")
    
    captcha_link = input("Paste the captcha link: ").strip()
    
    # Extract captcha token from the link
    if not captcha_link.startswith("signalcaptcha://"):
        print("Error: Invalid captcha link format")
        return False
    
    captcha_token = captcha_link.replace("signalcaptcha://", "")
    
    # Register with captcha
    print(f"\nRegistering with captcha token...")
    
    try:
        response = requests.post(
            f"{SIGNAL_API_URL}/v1/register/{SIGNAL_PHONE_NUMBER}",
            json={
                "captcha": captcha_token,
                "use_voice": False
            }
        )
        
        if response.status_code == 200 or response.status_code == 201:
            print("Registration initiated successfully!")
            print("You should receive a verification code via SMS.")
            
            # Get verification code
            verification_code = input("\nEnter the 6-digit verification code: ").strip()
            
            # Verify the code
            verify_response = requests.post(
                f"{SIGNAL_API_URL}/v1/register/{SIGNAL_PHONE_NUMBER}/verify/{verification_code}"
            )
            
            if verify_response.status_code == 200 or verify_response.status_code == 201:
                print("\nSignal number registered successfully!")
                return True
            else:
                print(f"\nVerification failed: {verify_response.text}")
                return False
                
        else:
            print(f"\nRegistration failed: {response.text}")
            return False
            
    except Exception as e:
        print(f"\nError during registration: {e}")
        return False

if __name__ == "__main__":
    success = register_with_captcha()
    sys.exit(0 if success else 1)