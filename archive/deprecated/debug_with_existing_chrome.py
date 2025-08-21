#!/usr/bin/env python3
"""
Debug authentication using existing chrome installation
"""
import asyncio
import logging
from playwright.async_api import async_playwright
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def debug_with_existing_chrome():
    """Debug with existing chrome"""
    try:
        async with async_playwright() as p:
            # Use the existing chromium installation with channel
            browser = await p.chromium.launch(
                headless=True,
                channel='chrome',  # Use system Chrome if available
                args=['--no-sandbox', '--disable-setuid-sandbox']
            )
            
            context = await browser.new_context(
                viewport={'width': 1280, 'height': 720},
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36'
            )
            
            page = await context.new_page()
            
            logger.info("🌐 Navigating to MyMama...")
            await page.goto("https://www.mymama.uk", wait_until='domcontentloaded')
            await asyncio.sleep(3)
            
            content = await page.inner_text('body')
            logger.info(f"📄 Content length: {len(content)}")
            
            # Save content for analysis
            with open('debug_mymama_content.txt', 'w') as f:
                f.write(content)
            
            logger.info("📝 Content preview:")
            print(content[:500])
            
            await browser.close()
            
    except Exception as first_error:
        logger.warning(f"⚠️ Chrome channel failed: {first_error}")
        
        # Fallback to direct chromium executable
        try:
            chrome_path = "/home/ohms/.cache/ms-playwright/chromium-1169/chrome-linux/chrome"
            
            async with async_playwright() as p:
                browser = await p.chromium.launch(
                    headless=True,
                    executable_path=chrome_path,
                    args=['--no-sandbox', '--disable-setuid-sandbox']
                )
                
                context = await browser.new_context(
                    viewport={'width': 1280, 'height': 720},
                    user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36'
                )
                
                page = await context.new_page()
                
                logger.info("🌐 Using direct chrome path - Navigating to MyMama...")
                await page.goto("https://www.mymama.uk", wait_until='domcontentloaded')
                await asyncio.sleep(3)
                
                content = await page.inner_text('body')
                logger.info(f"📄 Content length: {len(content)}")
                
                # Save content for analysis
                with open('debug_mymama_content.txt', 'w') as f:
                    f.write(content)
                
                logger.info("📝 Content preview:")
                print(content[:500])
                
                await browser.close()
                
        except Exception as e:
            logger.error(f"❌ All browser launch methods failed: {e}")

if __name__ == "__main__":
    asyncio.run(debug_with_existing_chrome())