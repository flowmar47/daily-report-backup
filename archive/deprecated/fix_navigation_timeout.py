#!/usr/bin/env python3
"""
Fix navigation timeout by using a more robust approach
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

async def test_navigation_fix():
    """Test navigation with timeout handling"""
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(
                headless=True,
                args=['--no-sandbox', '--disable-setuid-sandbox']
            )
            
            context = await browser.new_context(
                viewport={'width': 1280, 'height': 720},
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36'
            )
            
            page = await context.new_page()
            
            # First navigate to main page
            logger.info("🌐 Navigating to MyMama main page...")
            await page.goto("https://www.mymama.uk", wait_until='domcontentloaded', timeout=60000)
            await asyncio.sleep(2)
            
            # Look for and click login
            logger.info("🔍 Looking for login button...")
            login_links = await page.query_selector_all('a:has-text("Log In"), button:has-text("Log In")')
            
            if login_links:
                logger.info("✅ Found login link, clicking...")
                await login_links[0].click()
                await asyncio.sleep(3)
            else:
                # Try direct navigation to login
                logger.info("🔄 Navigating directly to login page...")
                await page.goto("https://www.mymama.uk/login", wait_until='domcontentloaded', timeout=60000)
                await asyncio.sleep(2)
            
            # Fill login form
            logger.info("📝 Filling login form...")
            
            # Get all input fields
            inputs = await page.query_selector_all('input')
            logger.info(f"Found {len(inputs)} input fields")
            
            # Find email and password fields
            email_field = None
            password_field = None
            
            for inp in inputs:
                inp_type = await inp.get_attribute('type')
                if inp_type == 'email' or (await inp.get_attribute('placeholder') and 'email' in (await inp.get_attribute('placeholder')).lower()):
                    email_field = inp
                elif inp_type == 'password':
                    password_field = inp
            
            if email_field and password_field:
                await email_field.fill('comfort.uncounted44@mailer.me')
                logger.info("✅ Filled email")
                
                await password_field.fill('5sqR*r3zjrp#FvAA9^@BGXhb')
                logger.info("✅ Filled password")
                
                # Submit form
                submit_btn = await page.query_selector('button[type="submit"], button:has-text("Log In")')
                if submit_btn:
                    await submit_btn.click()
                    logger.info("✅ Clicked submit")
                else:
                    # Try pressing Enter
                    await password_field.press('Enter')
                    logger.info("✅ Pressed Enter")
                
                # Wait for navigation
                await asyncio.sleep(5)
                
                # Check current URL
                current_url = page.url
                logger.info(f"📍 Current URL: {current_url}")
                
                # Now try to navigate to alerts page with different wait conditions
                logger.info("🎯 Attempting to navigate to alerts page...")
                
                try:
                    # Try with domcontentloaded first
                    await page.goto("https://www.mymama.uk/copy-of-alerts-essentials-1", 
                                   wait_until='domcontentloaded', 
                                   timeout=30000)
                    logger.info("✅ Page loaded (domcontentloaded)")
                except Exception as e:
                    logger.warning(f"⚠️ domcontentloaded failed: {e}")
                    
                    # Try without waiting
                    try:
                        await page.goto("https://www.mymama.uk/copy-of-alerts-essentials-1", 
                                       wait_until='commit',
                                       timeout=30000)
                        logger.info("✅ Page navigation started (commit)")
                    except Exception as e2:
                        logger.error(f"❌ Navigation failed: {e2}")
                
                # Wait for content to load
                await asyncio.sleep(10)
                
                # Get page content
                page_text = await page.inner_text('body')
                logger.info(f"📄 Page content length: {len(page_text)}")
                
                # Save content
                with open('navigation_fixed_content.txt', 'w') as f:
                    f.write(page_text)
                logger.info("💾 Content saved")
                
                # Check for real content
                has_forex = 'forex' in page_text.lower() or 'eur' in page_text.lower() or 'usd' in page_text.lower()
                has_options = 'options' in page_text.lower() or 'call' in page_text.lower() or 'put' in page_text.lower()
                has_signup = 'sign up' in page_text.lower() or 'already a member' in page_text.lower()
                
                logger.info(f"🔍 Content check:")
                logger.info(f"  - Has forex content: {has_forex}")
                logger.info(f"  - Has options content: {has_options}")
                logger.info(f"  - Has signup form: {has_signup}")
                
                # Print preview
                logger.info("📝 Content preview:")
                print(page_text[:1000])
                
                # Take screenshot
                await page.screenshot(path='alerts_page_fixed.png')
                logger.info("📸 Screenshot saved")
                
            else:
                logger.error("❌ Could not find login fields")
            
            await browser.close()
            
    except Exception as e:
        logger.error(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_navigation_fix())