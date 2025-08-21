#!/usr/bin/env python3
"""
Test Signal messaging with direct API calls
"""

import asyncio
import httpx
import json
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_signal_v1():
    """Test Signal v1 API"""
    async with httpx.AsyncClient() as client:
        payload = {
            "number": "+16572463906",
            "recipients": ["group.cUY1YUE5SHRRMW0wQy9SVGMrSWNvVTQrakluaU00YXlBeVBscUdLUFdMTT0="],
            "message": "🧪 Test message from Signal v1 API"
        }
        
        try:
            response = await client.post(
                "http://localhost:8080/v1/send",
                json=payload,
                timeout=30.0
            )
            logger.info(f"V1 Response status: {response.status_code}")
            logger.info(f"V1 Response: {response.text}")
            return response
        except Exception as e:
            logger.error(f"V1 API error: {e}")
            return None

async def test_signal_v2():
    """Test Signal v2 API"""
    async with httpx.AsyncClient() as client:
        payload = {
            "number": "+16572463906",
            "recipients": ["group.cUY1YUE5SHRRMW0wQy9SVGMrSWNvVTQrakluaU00YXlBeVBscUdLUFdMTT0="],
            "message": "🧪 Test message from Signal v2 API"
        }
        
        try:
            response = await client.post(
                "http://localhost:8080/v2/send",
                json=payload,
                timeout=30.0
            )
            logger.info(f"V2 Response status: {response.status_code}")
            logger.info(f"V2 Response: {response.text}")
            return response
        except Exception as e:
            logger.error(f"V2 API error: {e}")
            return None

async def main():
    logger.info("Testing Signal API endpoints...")
    
    logger.info("=== Testing V1 API ===")
    v1_result = await test_signal_v1()
    
    logger.info("=== Testing V2 API ===") 
    v2_result = await test_signal_v2()
    
    if v1_result and v1_result.status_code == 201:
        logger.info("✅ V1 API working")
    elif v2_result and v2_result.status_code == 201:
        logger.info("✅ V2 API working")
    else:
        logger.error("❌ Both APIs failed")

if __name__ == "__main__":
    asyncio.run(main())