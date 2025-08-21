#!/usr/bin/env python3
"""
Test script to verify that the Telegram Unicode fix works properly
"""

import asyncio
import json
import logging
import sys
from pathlib import Path

# Add paths for imports
sys.path.append(str(Path(__file__).parent / 'src'))
sys.path.append(str(Path(__file__).parent))

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def test_unicode_cleaning():
    """Test the Unicode cleaning functionality"""
    
    try:
        from src.messengers.unified_messenger import UnifiedTelegramMessenger
        from utils.env_config import EnvironmentConfig
        
        # Initialize environment
        env_config = EnvironmentConfig('daily_report')
        
        # Create Telegram messenger
        telegram_messenger = UnifiedTelegramMessenger(env_config)
        
        # Test data with problematic Unicode characters (from actual error)
        problematic_text = """PREMIUM SWING TRADES

Monday – Wednesday

RDUS – Radius Recycling, Inc.

    EARNINGS DATE: June\u202f30, 2025 (Before Market Open)
    ANALYSIS: Why Swing: LU typically sees a ~4\u20135% move the next day\u200b
"""
        
        logger.info("Original text with Unicode issues:")
        logger.info(f"Length: {len(problematic_text)}")
        logger.info(f"Sample: {repr(problematic_text[:100])}")
        
        # Check for problematic characters
        unicode_issues = []
        for i, char in enumerate(problematic_text):
            if ord(char) > 127 and char not in ['\n', '\r', '\t']:
                unicode_issues.append((i, char, ord(char), hex(ord(char))))
        
        logger.info(f"Found {len(unicode_issues)} Unicode issues in original:")
        for pos, char, code, hex_code in unicode_issues:
            logger.info(f"  Position {pos}: {repr(char)} (U+{hex_code[2:].upper().zfill(4)})")
        
        # Apply the Unicode cleaning
        cleaned_text = telegram_messenger._format_financial_message(problematic_text)
        
        logger.info("\nAfter cleaning:")
        logger.info(f"Length: {len(cleaned_text)}")
        logger.info(f"Sample: {repr(cleaned_text[:100])}")
        
        # Check for remaining Unicode issues
        remaining_issues = []
        for i, char in enumerate(cleaned_text):
            if ord(char) > 127 and char not in ['\n', '\r', '\t']:
                remaining_issues.append((i, char, ord(char), hex(ord(char))))
        
        if remaining_issues:
            logger.warning(f"Still found {len(remaining_issues)} Unicode issues after cleaning:")
            for pos, char, code, hex_code in remaining_issues:
                logger.warning(f"  Position {pos}: {repr(char)} (U+{hex_code[2:].upper().zfill(4)})")
        else:
            logger.info("✅ All problematic Unicode characters successfully cleaned!")
        
        # Show the difference
        logger.info("\nBefore and after comparison:")
        logger.info(f"Before: {repr(problematic_text)}")
        logger.info(f"After:  {repr(cleaned_text)}")
        
        return cleaned_text
        
    except ImportError as e:
        logger.error(f"Import error: {e}")
        return None
    except Exception as e:
        logger.error(f"Test failed: {e}", exc_info=True)
        return None

async def test_with_real_data():
    """Test with the actual financial data that caused the 400 error"""
    
    try:
        from src.messengers.unified_messenger import UnifiedTelegramMessenger
        from src.data_processors.template_generator import StructuredTemplateGenerator
        from utils.env_config import EnvironmentConfig
        
        # Load real data
        data_file = Path("real_alerts_only/real_alerts_20250702_060141.json")
        if not data_file.exists():
            logger.warning("No real data file found for testing")
            return
        
        with open(data_file, 'r') as f:
            financial_data = json.load(f)
        
        # Generate the structured message
        generator = StructuredTemplateGenerator()
        original_message = generator.generate_structured_message(financial_data)
        
        logger.info(f"Generated original message length: {len(original_message)}")
        
        # Initialize Telegram messenger and clean the message
        env_config = EnvironmentConfig('daily_report')
        telegram_messenger = UnifiedTelegramMessenger(env_config)
        cleaned_message = telegram_messenger._format_financial_message(original_message)
        
        logger.info(f"Cleaned message length: {len(cleaned_message)}")
        
        # Compare Unicode characters
        def count_unicode_issues(text):
            count = 0
            for char in text:
                if ord(char) > 127 and char not in ['\n', '\r', '\t']:
                    count += 1
            return count
        
        original_unicode_count = count_unicode_issues(original_message)
        cleaned_unicode_count = count_unicode_issues(cleaned_message)
        
        logger.info(f"Original Unicode issues: {original_unicode_count}")
        logger.info(f"Cleaned Unicode issues: {cleaned_unicode_count}")
        
        if cleaned_unicode_count == 0:
            logger.info("✅ Real data successfully cleaned of all problematic Unicode!")
        else:
            logger.warning(f"⚠️ Still has {cleaned_unicode_count} Unicode characters after cleaning")
        
        # Save cleaned message for inspection
        output_file = Path("cleaned_message_sample.txt")
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(cleaned_message)
        logger.info(f"Cleaned message saved to: {output_file}")
        
        return cleaned_message
        
    except Exception as e:
        logger.error(f"Real data test failed: {e}", exc_info=True)
        return None

if __name__ == "__main__":
    print("Testing Telegram Unicode Fix")
    print("=" * 40)
    
    # Test 1: Basic Unicode cleaning
    print("\n1. Testing basic Unicode cleaning...")
    asyncio.run(test_unicode_cleaning())
    
    # Test 2: Real financial data
    print("\n2. Testing with real financial data...")
    asyncio.run(test_with_real_data())
    
    print("\n✅ Testing completed!")
    print("\nNext steps:")
    print("1. Restart the daily report service to apply the fix")
    print("2. Monitor tomorrow's run for successful Telegram delivery")
    print("3. Check both Signal and Telegram receive the cleaned messages")