#!/usr/bin/env python3
"""
Direct test of Signal Docker API to diagnose messaging issues
"""

import httpx
import asyncio
import json
import logging
from datetime import datetime

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def test_signal_api():
    """Test Signal API directly without any wrappers"""
    
    # Configuration from .env
    phone_number = '+16572463906'
    group_id = 'group.ZmFLQ25IUTBKbWpuNFdpaDdXTjVoVXpYOFZtNGVZZ1lYRGdwMWpMcW0zMD0='
    api_url = 'http://localhost:8080'
    
    logger.info(f"Testing Signal API at {api_url}")
    logger.info(f"Phone: {phone_number}")
    logger.info(f"Group: {group_id}")
    
    async with httpx.AsyncClient(base_url=api_url, timeout=30.0) as client:
        try:
            # Test 1: Check API status
            logger.info("Test 1: Checking API status...")
            response = await client.get('/v1/about')
            logger.info(f"API Status: {response.json()}")
            
            # Test 2: Check registered accounts
            logger.info("\nTest 2: Checking registered accounts...")
            response = await client.get('/v1/accounts')
            accounts = response.json()
            logger.info(f"Registered accounts: {json.dumps(accounts, indent=2)}")
            
            # Test 3: Send test message to group
            logger.info("\nTest 3: Sending test message to group...")
            test_message = f"Signal API Test - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            
            # Try v2 API endpoint
            payload = {
                "number": phone_number.strip('"\''),
                "recipients": [group_id.strip('"\'')],
                "message": test_message
            }
            
            logger.debug(f"Payload: {json.dumps(payload, indent=2)}")
            
            response = await client.post('/v2/send', json=payload)
            logger.info(f"Response status: {response.status_code}")
            logger.info(f"Response body: {response.text}")
            
            if response.status_code == 201:
                logger.info("✅ Message sent successfully!")
            else:
                logger.error(f"❌ Failed to send message: {response.text}")
                
                # Try v1 API as fallback
                logger.info("\nTrying v1 API endpoint...")
                v1_payload = {
                    "message": test_message,
                    "number": phone_number.strip('"\''),
                    "recipients": [group_id.strip('"\'')]
                }
                
                response = await client.post('/v1/send', json=v1_payload)
                logger.info(f"V1 Response status: {response.status_code}")
                logger.info(f"V1 Response body: {response.text}")
            
        except Exception as e:
            logger.error(f"Error during test: {e}", exc_info=True)

if __name__ == "__main__":
    asyncio.run(test_signal_api())