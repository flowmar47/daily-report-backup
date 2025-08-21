#!/usr/bin/env python3
"""
Test real authentication with provided credentials in headless mode
"""
import asyncio
import logging
import os
from playwright.async_api import async_playwright
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_real_authentication():
    """Test authentication with real credentials"""
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(
                headless=True,  # Headless mode
                args=[
                    '--disable-blink-features=AutomationControlled',
                    '--no-sandbox',
                    '--disable-setuid-sandbox'
                ]
            )
            
            context = await browser.new_context(
                viewport={'width': 1280, 'height': 720},
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36'
            )
            
            page = await context.new_page()
            
            # First, update the .env file with the correct credentials
            logger.info("🔧 Updating credentials in .env file...")
            env_content = []
            env_path = '.env'
            
            # Read existing .env
            if os.path.exists(env_path):
                with open(env_path, 'r') as f:
                    for line in f:
                        if line.startswith('MYMAMA_USERNAME='):
                            env_content.append('MYMAMA_USERNAME=comfort.uncounted44@mailer.me\n')
                        elif line.startswith('MYMAMA_PASSWORD='):
                            env_content.append('MYMAMA_PASSWORD=5sqR*r3zjrp#FvAA9^@BGXhb\n')
                        else:
                            env_content.append(line)
            
            # Write updated .env
            with open(env_path, 'w') as f:
                f.writelines(env_content)
            logger.info("✅ Updated .env file with correct credentials")
            
            # Navigate to MyMama
            logger.info("🌐 Navigating to MyMama...")
            await page.goto("https://www.mymama.uk", wait_until='networkidle')
            await asyncio.sleep(3)
            
            # Look for login button on main page
            login_buttons = await page.query_selector_all('a:has-text("Log In"), button:has-text("Log In")')
            if login_buttons:
                logger.info(f"✅ Found {len(login_buttons)} login buttons")
                await login_buttons[0].click()
                await asyncio.sleep(3)
            
            # Check current URL
            current_url = page.url
            logger.info(f"📍 Current URL: {current_url}")
            
            # Look for login form
            logger.info("🔍 Looking for login fields...")
            
            # Find all input fields
            inputs = await page.query_selector_all('input')
            logger.info(f"📝 Found {len(inputs)} input fields")
            
            # Find email and password fields
            email_field = None
            password_field = None
            
            for inp in inputs:
                inp_type = await inp.get_attribute('type')
                inp_name = await inp.get_attribute('name')
                inp_placeholder = await inp.get_attribute('placeholder')
                
                if inp_type == 'email' or (inp_placeholder and 'email' in inp_placeholder.lower()):
                    email_field = inp
                    logger.info(f"✅ Found email field")
                elif inp_type == 'password':
                    password_field = inp
                    logger.info(f"✅ Found password field")
            
            if email_field and password_field:
                # Fill credentials
                await email_field.click()
                await email_field.fill('comfort.uncounted44@mailer.me')
                logger.info("✅ Filled email")
                
                await password_field.click()
                await password_field.fill('5sqR*r3zjrp#FvAA9^@BGXhb')
                logger.info("✅ Filled password")
                
                # Find submit button
                submit_button = await page.query_selector('button[type="submit"], button:has-text("Log In"), button:has-text("Sign In")')
                if submit_button:
                    await submit_button.click()
                    logger.info("✅ Clicked submit button")
                    
                    # Wait for navigation
                    await asyncio.sleep(5)
                    
                    # Check if logged in
                    current_url = page.url
                    logger.info(f"📍 URL after login: {current_url}")
                    
                    # Navigate to alerts page
                    logger.info("🎯 Navigating to alerts page...")
                    await page.goto("https://www.mymama.uk/copy-of-alerts-essentials-1", wait_until='networkidle')
                    await asyncio.sleep(5)
                    
                    # Get page content
                    page_text = await page.inner_text('body')
                    logger.info(f"📄 Page content length: {len(page_text)}")
                    
                    # Save content
                    with open('authenticated_alerts_content.txt', 'w') as f:
                        f.write(page_text)
                    logger.info("💾 Content saved to authenticated_alerts_content.txt")
                    
                    # Check for real content
                    has_forex = 'forex' in page_text.lower() or 'eur' in page_text.lower() or 'usd' in page_text.lower()
                    has_options = 'options' in page_text.lower() or 'call' in page_text.lower() or 'put' in page_text.lower()
                    has_signup = 'sign up' in page_text.lower() or 'already a member' in page_text.lower()
                    
                    logger.info(f"🔍 Content check:")
                    logger.info(f"  - Has forex content: {has_forex}")
                    logger.info(f"  - Has options content: {has_options}")
                    logger.info(f"  - Has signup form: {has_signup}")
                    
                    if has_signup:
                        logger.warning("⚠️ Still seeing signup page - authentication may have failed")
                    else:
                        logger.info("✅ Appears to be authenticated content")
                    
                    # Print first 500 chars
                    logger.info("📝 Content preview:")
                    print(page_text[:500])
                    
            else:
                logger.error("❌ Could not find login fields")
            
            await browser.close()
            
            # Now let's test with the enhanced scraper
            logger.info("\n🚀 Testing enhanced scraper with updated credentials...")
            from enhanced_browserbase_scraper import EnhancedBrowserBaseScraper
            
            scraper = EnhancedBrowserBaseScraper()
            result = await scraper.scrape_data()
            
            if result.get('success'):
                logger.info("✅ Enhanced scraper succeeded!")
                logger.info(f"📊 Data extracted:")
                logger.info(f"  - Forex alerts: {len(result.get('forex_alerts', []))}")
                logger.info(f"  - Options alerts: {len(result.get('options_alerts', []))}")
                logger.info(f"  - Swing trades: {len(result.get('swing_trades', []))}")
                logger.info(f"  - Day trades: {len(result.get('day_trades', []))}")
                
                # Save result
                import json
                with open('enhanced_scraper_result.json', 'w') as f:
                    json.dump(result, f, indent=2)
                logger.info("💾 Result saved to enhanced_scraper_result.json")
            else:
                logger.error(f"❌ Enhanced scraper failed: {result.get('error')}")
            
    except Exception as e:
        logger.error(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_real_authentication())