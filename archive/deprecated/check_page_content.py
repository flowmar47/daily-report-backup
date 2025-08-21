#!/usr/bin/env python3
"""
Check actual page content after authentication
"""
import asyncio
import logging
from enhanced_browserbase_scraper import EnhancedBrowserBaseScraper
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def check_page_content():
    """Check what page content we actually get"""
    try:
        # Use the enhanced scraper to get authenticated content
        scraper = EnhancedBrowserBaseScraper()
        
        # Override the scraper to save page content before extraction
        logger.info("🔍 Getting authenticated page content...")
        
        result = await scraper.scrape_data()
        
        # Check the saved content
        from pathlib import Path
        output_dir = Path("output/enhanced_browserbase")
        latest_file = output_dir / "latest_enhanced_data.json"
        
        if latest_file.exists():
            import json
            with open(latest_file, 'r') as f:
                data = json.load(f)
            
            # Extract page content from the raw data
            page_content = data.get('data', {}).get('page_content', '')
            page_text = data.get('data', {}).get('page_text', '')
            
            logger.info(f"📄 Page content length: {len(page_content)}")
            logger.info(f"📄 Page text length: {len(page_text)}")
            
            # Save readable content
            with open('authenticated_page_content.html', 'w') as f:
                f.write(page_content)
            
            with open('authenticated_page_text.txt', 'w') as f:
                f.write(page_text)
            
            logger.info("💾 Saved content to authenticated_page_*.* files")
            
            # Analyze content
            logger.info("\n🔍 Content Analysis:")
            
            # Check for authentication issues
            if 'sign up' in page_text.lower() or 'log in' in page_text.lower():
                logger.warning("⚠️ Still seeing login/signup page")
            
            # Check for premium content indicators
            if 'premium' in page_text.lower() or 'subscription' in page_text.lower():
                logger.warning("⚠️ May need premium subscription")
            
            # Check for trading content
            forex_terms = ['forex', 'eur', 'usd', 'gbp', 'currency', 'fx']
            options_terms = ['options', 'call', 'put', 'strike', 'expiry']
            trading_terms = ['buy', 'sell', 'signal', 'alert', 'trade']
            
            forex_found = any(term in page_text.lower() for term in forex_terms)
            options_found = any(term in page_text.lower() for term in options_terms)
            trading_found = any(term in page_text.lower() for term in trading_terms)
            
            logger.info(f"  - Forex content: {forex_found}")
            logger.info(f"  - Options content: {options_found}")
            logger.info(f"  - Trading content: {trading_found}")
            
            # Check page structure
            if '<table' in page_content or 'data-testid' in page_content:
                logger.info("  - Has structured data elements")
            
            # Print sample content
            logger.info("\n📝 Page text sample (first 1000 chars):")
            print(page_text[:1000])
            
            # Look for specific patterns that might indicate content
            if len(page_text) < 500:
                logger.warning("⚠️ Very short content - may be loading issue or restricted access")
                
                # Check if it's a Wix loading issue
                if 'wix' in page_content.lower() or 'loading' in page_text.lower():
                    logger.info("💡 Suggestion: Wix site may need longer loading time")
            
            # Look for error messages
            error_indicators = ['error', 'not found', '404', 'access denied', 'forbidden']
            for indicator in error_indicators:
                if indicator in page_text.lower():
                    logger.warning(f"⚠️ Found error indicator: {indicator}")
        
        else:
            logger.error("❌ No data file found")
            
    except Exception as e:
        logger.error(f"❌ Content check failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(check_page_content())