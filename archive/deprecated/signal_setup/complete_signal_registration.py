#!/usr/bin/env python3
"""Complete Signal registration process for Docker container."""

import os
import sys
import time
import requests
import subprocess
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

SIGNAL_API_URL = os.getenv('SIGNAL_API_URL', 'http://localhost:8080')
SIGNAL_PHONE_NUMBER = os.getenv('SIGNAL_PHONE_NUMBER', '+16572463906')
SIGNAL_GROUP_ID = os.getenv('SIGNAL_GROUP_ID')

def check_container_status():
    """Check if Signal container is running."""
    result = subprocess.run(['docker', 'ps', '--filter', 'name=signal-api', '--format', '{{.Status}}'], 
                          capture_output=True, text=True)
    if 'Up' in result.stdout:
        print("✓ Signal container is running")
        return True
    else:
        print("✗ Signal container is not running")
        print("Starting container...")
        subprocess.run(['docker', 'start', 'signal-api'])
        time.sleep(5)
        return True

def check_registration_status():
    """Check if number is already registered."""
    try:
        response = requests.get(f"{SIGNAL_API_URL}/v1/accounts")
        accounts = response.json()
        
        if isinstance(accounts, list):
            for account in accounts:
                if account.get('number') == SIGNAL_PHONE_NUMBER:
                    print(f"✓ Number {SIGNAL_PHONE_NUMBER} is already registered")
                    return True
        
        print(f"✗ Number {SIGNAL_PHONE_NUMBER} is not registered")
        return False
    except Exception as e:
        print(f"Error checking registration: {e}")
        return False

def register_with_manual_captcha():
    """Register Signal number with manual captcha process."""
    print("\n" + "="*60)
    print("SIGNAL REGISTRATION PROCESS")
    print("="*60)
    
    print(f"\nPhone Number: {SIGNAL_PHONE_NUMBER}")
    print(f"API URL: {SIGNAL_API_URL}")
    
    print("\n" + "-"*60)
    print("STEP 1: Generate Captcha Token")
    print("-"*60)
    print("\n1. Open this URL in your browser:")
    print("   https://signalcaptchas.org/registration/generate.html")
    print("\n2. Complete the captcha challenge")
    print("\n3. After solving, right-click on the 'Open Signal' button")
    print("   and select 'Copy Link Address'")
    print("\n4. The link will look like:")
    print("   signalcaptcha://signal-recaptcha-v2.LONG_TOKEN_HERE")
    
    captcha_link = input("\nPaste the complete captcha link here: ").strip()
    
    if not captcha_link.startswith("signalcaptcha://"):
        print("\n✗ Invalid captcha link format!")
        return False
    
    # Extract token
    captcha_token = captcha_link.replace("signalcaptcha://", "")
    print(f"\n✓ Captcha token extracted: {captcha_token[:20]}...")
    
    # Register with captcha
    print("\n" + "-"*60)
    print("STEP 2: Initiate Registration")
    print("-"*60)
    
    try:
        print(f"\nSending registration request...")
        response = requests.post(
            f"{SIGNAL_API_URL}/v1/register/{SIGNAL_PHONE_NUMBER}",
            json={
                "captcha": captcha_token,
                "use_voice": False
            },
            timeout=30
        )
        
        print(f"Response Status: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code in [200, 201]:
            print("\n✓ Registration initiated successfully!")
            print("✓ SMS verification code should arrive within 1-2 minutes")
        else:
            print(f"\n✗ Registration failed: {response.text}")
            
            # Try voice if SMS fails
            if "rate limit" in response.text.lower():
                print("\nTrying voice verification instead...")
                response = requests.post(
                    f"{SIGNAL_API_URL}/v1/register/{SIGNAL_PHONE_NUMBER}",
                    json={
                        "captcha": captcha_token,
                        "use_voice": True
                    },
                    timeout=30
                )
                if response.status_code in [200, 201]:
                    print("✓ Voice call initiated - you will receive a call with the code")
                else:
                    return False
            else:
                return False
    
    except Exception as e:
        print(f"\n✗ Error during registration: {e}")
        return False
    
    # Get verification code
    print("\n" + "-"*60)
    print("STEP 3: Verify Code")
    print("-"*60)
    
    verification_code = input("\nEnter the 6-digit verification code: ").strip()
    
    try:
        print(f"\nVerifying code...")
        verify_response = requests.post(
            f"{SIGNAL_API_URL}/v1/register/{SIGNAL_PHONE_NUMBER}/verify/{verification_code}",
            timeout=30
        )
        
        print(f"Verification Status: {verify_response.status_code}")
        print(f"Response: {verify_response.text}")
        
        if verify_response.status_code in [200, 201]:
            print("\n✓ SIGNAL NUMBER REGISTERED SUCCESSFULLY!")
            
            # Test the registration
            print("\nTesting registration...")
            test_response = requests.get(f"{SIGNAL_API_URL}/v1/about")
            if test_response.status_code == 200:
                print("✓ Signal API is responding correctly")
            
            return True
        else:
            print(f"\n✗ Verification failed: {verify_response.text}")
            return False
            
    except Exception as e:
        print(f"\n✗ Error during verification: {e}")
        return False

def test_messaging():
    """Test sending a message after registration."""
    print("\n" + "-"*60)
    print("TESTING MESSAGE SENDING")
    print("-"*60)
    
    try:
        # Test sending to self
        test_message = {
            "message": "Signal registration successful! This is a test message.",
            "number": SIGNAL_PHONE_NUMBER,
            "recipients": [SIGNAL_PHONE_NUMBER]
        }
        
        response = requests.post(f"{SIGNAL_API_URL}/v2/send", json=test_message)
        
        if response.status_code == 200:
            print("✓ Test message sent successfully!")
        else:
            print(f"✗ Test message failed: {response.text}")
            
    except Exception as e:
        print(f"✗ Error sending test message: {e}")

def main():
    """Main registration process."""
    print("\nSignal Docker Registration Helper")
    print("================================\n")
    
    # Check container
    if not check_container_status():
        print("Failed to start container")
        return False
    
    # Check if already registered
    if check_registration_status():
        print("\nNumber is already registered. Testing messaging...")
        test_messaging()
        return True
    
    # Perform registration
    if register_with_manual_captcha():
        print("\nRegistration completed successfully!")
        test_messaging()
        
        if SIGNAL_GROUP_ID:
            print(f"\nGroup ID configured: {SIGNAL_GROUP_ID}")
            print("You can now send messages to your Signal group.")
        
        return True
    else:
        print("\nRegistration failed. Please try again.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)