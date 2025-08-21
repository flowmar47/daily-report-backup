#!/usr/bin/env python3
"""
Alternative Signal Messenger using Webhook/API approach
This avoids the ARM64 compatibility issues with signal-cli
"""
import os
import json
import logging
import requests
from typing import Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)

class SignalWebhookMessenger:
    """
    Signal messenger using webhook or API service
    This can work with services like:
    - signal-cli-rest-api (Docker)
    - signal-api webhook services
    - Custom Signal bridge
    """
    
    def __init__(self):
        # For now, let's prepare the structure
        # You'll need to set up one of these services:
        # 1. signal-cli-rest-api Docker container
        # 2. A Signal webhook service
        # 3. A Signal bridge service
        
        self.api_url = os.getenv('SIGNAL_API_URL', 'http://localhost:8080')
        self.phone_number = os.getenv('SIGNAL_PHONE_NUMBER', '+16572463906')
        self.group_id = os.getenv('SIGNAL_GROUP_ID')
        
    def send_message_via_api(self, message: str, group_id: Optional[str] = None) -> bool:
        """Send message via Signal REST API"""
        target_group = group_id or self.group_id
        
        if not target_group:
            logger.error("❌ No Signal group ID available")
            return False
            
        try:
            # For signal-cli-rest-api
            endpoint = f"{self.api_url}/v2/send"
            
            payload = {
                "message": message,
                "number": self.phone_number,
                "recipients": [target_group] if target_group.startswith('+') else [],
                "group_id": target_group if target_group.startswith('group.') else None
            }
            
            response = requests.post(endpoint, json=payload, timeout=30)
            
            if response.status_code == 200:
                logger.info("✅ Signal message sent via API")
                return True
            else:
                logger.error(f"❌ API error: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Error sending via API: {e}")
            return False
    
    def register_number(self):
        """Register phone number via API"""
        try:
            # Registration endpoint
            endpoint = f"{self.api_url}/v1/register/{self.phone_number}"
            
            response = requests.post(endpoint, timeout=30)
            
            if response.status_code == 200:
                logger.info("✅ Registration initiated - check SMS")
                return True
            else:
                logger.error(f"❌ Registration failed: {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Error during registration: {e}")
            return False
    
    def verify_code(self, code: str):
        """Verify SMS code"""
        try:
            endpoint = f"{self.api_url}/v1/register/{self.phone_number}/verify/{code}"
            
            response = requests.post(endpoint, timeout=30)
            
            if response.status_code == 200:
                logger.info("✅ Verification successful")
                return True
            else:
                logger.error(f"❌ Verification failed: {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Error during verification: {e}")
            return False

# Alternative: Use a webhook service
class SignalWebhookService:
    """
    Alternative using webhook services like:
    - Integromat/Make
    - Zapier
    - IFTTT with Signal integration
    """
    
    def __init__(self):
        self.webhook_url = os.getenv('SIGNAL_WEBHOOK_URL')
        
    def send_via_webhook(self, message: str) -> bool:
        """Send message via webhook"""
        if not self.webhook_url:
            logger.error("❌ No webhook URL configured")
            return False
            
        try:
            payload = {
                "message": message,
                "phone": os.getenv('SIGNAL_PHONE_NUMBER'),
                "group": os.getenv('SIGNAL_GROUP_ID')
            }
            
            response = requests.post(self.webhook_url, json=payload, timeout=30)
            
            if response.status_code in [200, 201, 204]:
                logger.info("✅ Message sent via webhook")
                return True
            else:
                logger.error(f"❌ Webhook error: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Error sending via webhook: {e}")
            return False

# For now, let's document the alternatives
SETUP_INSTRUCTIONS = """
# Signal Integration Alternatives for Raspberry Pi ARM64

Due to architecture compatibility issues with signal-cli on ARM64, 
here are alternative approaches:

## Option 1: Docker-based Signal API
```bash
# Install Docker
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER

# Run signal-cli-rest-api
docker run -d \\
    --name signal-api \\
    --restart unless-stopped \\
    -p 8080:8080 \\
    -v ~/signal-data:/home/.local/share/signal-cli \\
    bbernhard/signal-cli-rest-api:latest

# Register via API
curl -X POST http://localhost:8080/v1/register/+16572463906
```

## Option 2: Signal Webhook Service
1. Use a service like Make.com (formerly Integromat)
2. Create a webhook that receives messages
3. Connect it to Signal using their app
4. Set SIGNAL_WEBHOOK_URL in .env

## Option 3: Signal Bridge
Use Matrix bridges or other Signal bridge services that provide REST APIs

## Option 4: Run signal-cli on x86_64 server
1. Set up signal-cli on an x86_64 server
2. Expose it via REST API
3. Configure SIGNAL_API_URL to point to that server

## Temporary Solution
For now, the system will continue sending to Telegram only.
When Signal is properly configured, messages will automatically
be sent to both platforms.
"""

if __name__ == "__main__":
    print(SETUP_INSTRUCTIONS)