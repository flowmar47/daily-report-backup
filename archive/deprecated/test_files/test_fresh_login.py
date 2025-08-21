#!/usr/bin/env python3
"""
Test fresh login without stored sessions
"""
import asyncio
import logging
import os
import shutil
from enhanced_browserbase_scraper import EnhancedBrowserBaseScraper

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_fresh_login():
    """Test login without any stored sessions"""
    try:
        # Clear any existing sessions
        session_dir = "browser_sessions/mymama_enhanced_session"
        if os.path.exists(session_dir):
            shutil.rmtree(session_dir)
            logger.info("🗑️ Cleared existing session data")
        
        scraper = EnhancedBrowserBaseScraper()
        
        # Initialize browser
        await scraper.initialize_browser()
        
        # Navigate directly to login page first
        logger.info("🌐 Navigating to login page...")
        await scraper.page.goto("https://www.mymama.uk/login", wait_until='networkidle')
        await asyncio.sleep(3)
        
        # Check what we see
        page_text = await scraper.page.inner_text('body')
        logger.info(f"📄 Login page content length: {len(page_text)}")
        
        # Try authentication
        auth_result = await scraper._perform_authentication()
        logger.info(f"🔐 Authentication result: {auth_result}")
        
        # Navigate to target page after login
        logger.info("🎯 Navigating to target page...")
        await scraper.page.goto(scraper.TARGET_URL, wait_until='networkidle')
        await asyncio.sleep(5)
        
        # Check final content
        final_text = await scraper.page.inner_text('body')
        logger.info(f"📄 Final page content length: {len(final_text)}")
        
        if len(final_text) > 100:
            logger.info("📝 First 500 chars of final content:")
            print(final_text[:500])
        
        # Save final content for analysis
        with open('final_authenticated_content.txt', 'w') as f:
            f.write(final_text)
        
        logger.info("💾 Final content saved to final_authenticated_content.txt")
        
        await scraper.cleanup()
        
    except Exception as e:
        logger.error(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_fresh_login())