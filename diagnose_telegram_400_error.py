#!/usr/bin/env python3
"""
Diagnostic script to identify and fix Telegram 400 errors
Based on analysis of logs showing successful Signal but failed Telegram
"""

import asyncio
import json
import logging
import os
import re
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load environment
load_dotenv()

# Add paths for imports
sys.path.append(str(Path(__file__).parent / 'src'))
sys.path.append(str(Path(__file__).parent))

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def clean_unicode_for_telegram(text: str) -> str:
    """
    Clean problematic Unicode characters that cause Telegram 400 errors
    
    Known problematic characters found in the data:
    - \u202f (narrow no-break space)
    - \u200b (zero-width space)
    - Other control characters
    """
    if not text:
        return text
    
    # Replace problematic Unicode characters
    text = text.replace('\u202f', ' ')  # narrow no-break space -> regular space
    text = text.replace('\u200b', '')   # zero-width space -> nothing
    text = text.replace('\u2009', ' ')  # thin space -> regular space
    text = text.replace('\u00a0', ' ')  # non-breaking space -> regular space
    text = text.replace('\u2060', '')   # word joiner -> nothing
    
    # Remove other control characters except newlines and tabs
    text = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F-\x9F]', '', text)
    
    # Normalize multiple spaces to single spaces
    text = re.sub(r' +', ' ', text)
    
    # Clean up any trailing/leading whitespace on lines
    lines = text.split('\n')
    lines = [line.strip() for line in lines]
    text = '\n'.join(lines)
    
    return text

async def test_telegram_messaging():
    """Test Telegram messaging with problematic and cleaned data"""
    
    try:
        import httpx
        
        bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
        group_id = os.getenv('TELEGRAM_GROUP_ID')
        
        if not bot_token or not group_id:
            logger.error("Missing Telegram credentials in .env file")
            return
        
        logger.info(f"Testing with bot token: {bot_token[:20]}...")
        logger.info(f"Testing with group ID: {group_id}")
        
        # Read the actual problematic data that caused the 400 error
        data_file = Path("real_alerts_only/real_alerts_20250702_060141.json")
        if data_file.exists():
            with open(data_file, 'r') as f:
                raw_data = json.load(f)
            
            # Extract problematic content from swing trades (contains Unicode characters)
            problematic_text = ""
            if raw_data.get('swing_trades'):
                for trade in raw_data['swing_trades']:
                    analysis = trade.get('analysis', '')
                    if analysis:
                        problematic_text += f"Analysis: {analysis}\n"
            
            if not problematic_text:
                problematic_text = "Test with Unicode: June\u202f30, 2025\u200bsample text"
            
            logger.info(f"Found problematic text with Unicode characters (length: {len(problematic_text)})")
            logger.info(f"Sample: {repr(problematic_text[:100])}")
            
            # Test 1: Send problematic text (should get 400 error)
            logger.info("\n=== Test 1: Sending problematic text (expecting 400 error) ===")
            async with httpx.AsyncClient() as client:
                url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
                payload = {
                    'chat_id': group_id,
                    'text': f"TEST 1 - Problematic Unicode:\n{problematic_text[:500]}",
                    'parse_mode': 'Markdown'
                }
                
                try:
                    response = await client.post(url, json=payload, timeout=10.0)
                    logger.info(f"Response status: {response.status_code}")
                    if response.status_code != 200:
                        logger.error(f"Error response: {response.text}")
                    else:
                        logger.info("✅ Problematic text sent successfully (unexpected!)")
                except Exception as e:
                    logger.error(f"❌ Error sending problematic text: {e}")
            
            # Test 2: Send cleaned text (should succeed)
            logger.info("\n=== Test 2: Sending cleaned text (expecting success) ===")
            cleaned_text = clean_unicode_for_telegram(problematic_text)
            logger.info(f"Cleaned text sample: {repr(cleaned_text[:100])}")
            
            async with httpx.AsyncClient() as client:
                url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
                payload = {
                    'chat_id': group_id,
                    'text': f"TEST 2 - Cleaned Unicode:\n{cleaned_text[:500]}",
                    'parse_mode': 'Markdown'
                }
                
                try:
                    response = await client.post(url, json=payload, timeout=10.0)
                    logger.info(f"Response status: {response.status_code}")
                    if response.status_code == 200:
                        logger.info("✅ Cleaned text sent successfully!")
                        result = response.json()
                        message_id = result.get('result', {}).get('message_id')
                        logger.info(f"Message ID: {message_id}")
                    else:
                        logger.error(f"Error response: {response.text}")
                except Exception as e:
                    logger.error(f"❌ Error sending cleaned text: {e}")
        
        else:
            logger.warning("No real data file found, testing with sample Unicode")
            
            # Test with sample problematic Unicode
            problematic_sample = "Test with problematic Unicode: June\u202f30, 2025\u200b(earnings date)"
            
            logger.info("\n=== Testing with sample problematic Unicode ===")
            async with httpx.AsyncClient() as client:
                url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
                payload = {
                    'chat_id': group_id,
                    'text': f"Sample problematic: {problematic_sample}",
                    'parse_mode': 'Markdown'
                }
                
                try:
                    response = await client.post(url, json=payload, timeout=10.0)
                    logger.info(f"Sample response status: {response.status_code}")
                    if response.status_code != 200:
                        logger.error(f"Sample error response: {response.text}")
                except Exception as e:
                    logger.error(f"❌ Sample error: {e}")
    
    except ImportError:
        logger.error("httpx not available, cannot test Telegram API directly")
        logger.info("Install httpx with: pip install httpx")
    
    except Exception as e:
        logger.error(f"Test failed: {e}", exc_info=True)

def analyze_unicode_in_data():
    """Analyze the actual data for problematic Unicode characters"""
    
    logger.info("\n=== Analyzing Unicode characters in real data ===")
    
    data_file = Path("real_alerts_only/real_alerts_20250702_060141.json")
    if not data_file.exists():
        logger.warning("No real data file found for analysis")
        return
    
    with open(data_file, 'r') as f:
        raw_data = json.load(f)
    
    # Convert to string for analysis
    data_str = json.dumps(raw_data, indent=2)
    
    # Find problematic Unicode characters
    problematic_chars = {
        '\u202f': 'narrow no-break space',
        '\u200b': 'zero-width space',
        '\u2009': 'thin space',
        '\u00a0': 'non-breaking space',
        '\u2060': 'word joiner'
    }
    
    found_issues = []
    for char, description in problematic_chars.items():
        count = data_str.count(char)
        if count > 0:
            found_issues.append(f"Found {count} instances of {description} (\\u{ord(char):04x})")
    
    if found_issues:
        logger.warning("🚨 Found problematic Unicode characters:")
        for issue in found_issues:
            logger.warning(f"  - {issue}")
    else:
        logger.info("✅ No problematic Unicode characters found")
    
    # Show sample of where they occur
    if found_issues:
        logger.info("\nSample locations:")
        for section_name, section_data in raw_data.items():
            if isinstance(section_data, list):
                for i, item in enumerate(section_data):
                    if isinstance(item, dict):
                        for key, value in item.items():
                            if isinstance(value, str):
                                for char in problematic_chars:
                                    if char in value:
                                        logger.info(f"  {section_name}[{i}].{key}: {repr(value[:50])}")

if __name__ == "__main__":
    print("Diagnosing Telegram 400 Error")
    print("=" * 50)
    
    # Analyze the data first
    analyze_unicode_in_data()
    
    # Test messaging with the user's permission
    user_input = input("\nRun live Telegram messaging tests? (y/N): ").strip().lower()
    if user_input in ['y', 'yes']:
        print("WARNING: This will send test messages to your live Telegram group!")
        confirm = input("Are you sure? (y/N): ").strip().lower()
        if confirm in ['y', 'yes']:
            asyncio.run(test_telegram_messaging())
        else:
            print("Messaging tests skipped by user")
    else:
        print("Analysis complete. Messaging tests skipped.")
        print("\nRECOMMENDATION:")
        print("The 400 error is likely caused by Unicode characters in the message text.")
        print("Add Unicode cleaning to the template generator before sending to Telegram.")