#!/usr/bin/env python3
"""
Debug authentication issue with screenshots
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

async def debug_authentication():
    """Debug authentication with detailed logging"""
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(
                headless=False,  # Use headful mode for debugging
                args=['--no-sandbox', '--disable-setuid-sandbox']
            )
            
            context = await browser.new_context(
                viewport={'width': 1280, 'height': 720},
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36'
            )
            
            page = await context.new_page()
            
            # Step 1: Navigate to main page
            logger.info("🌐 Step 1: Navigate to MyMama main page...")
            await page.goto("https://www.mymama.uk", wait_until='domcontentloaded')
            await asyncio.sleep(3)
            await page.screenshot(path='debug_1_main_page.png')
            
            # Step 2: Click login
            logger.info("🔍 Step 2: Find and click login...")
            login_links = await page.query_selector_all('a:has-text("Log In"), button:has-text("Log In"), a:has-text("Login")')
            
            if login_links:
                logger.info(f"✅ Found {len(login_links)} login links")
                await login_links[0].click()
                await asyncio.sleep(3)
            else:
                logger.info("🔄 No login link found, navigating directly...")
                await page.goto("https://www.mymama.uk/login", wait_until='domcontentloaded')
                await asyncio.sleep(3)
            
            await page.screenshot(path='debug_2_login_page.png')
            page_text = await page.inner_text('body')
            logger.info(f"📄 Login page content length: {len(page_text)}")
            
            # Step 3: Fill login form
            logger.info("📝 Step 3: Fill login form...")
            
            # Debug: List all inputs
            inputs = await page.query_selector_all('input')
            logger.info(f"🔍 Found {len(inputs)} input fields:")
            
            email_field = None
            password_field = None
            
            for i, inp in enumerate(inputs):
                inp_type = await inp.get_attribute('type') or 'text'
                inp_name = await inp.get_attribute('name') or ''
                inp_placeholder = await inp.get_attribute('placeholder') or ''
                inp_id = await inp.get_attribute('id') or ''
                is_visible = await inp.is_visible()
                
                logger.info(f"  Input {i+1}: type={inp_type}, name={inp_name}, id={inp_id}, placeholder={inp_placeholder}, visible={is_visible}")
                
                # Try to identify email field
                if not email_field and is_visible and (
                    inp_type == 'email' or 
                    'email' in inp_name.lower() or 
                    'email' in inp_placeholder.lower() or
                    'username' in inp_name.lower() or
                    inp_type == 'text'
                ):
                    email_field = inp
                    logger.info(f"  ➡️ Selected as email field")
                
                # Try to identify password field
                if not password_field and is_visible and inp_type == 'password':
                    password_field = inp
                    logger.info(f"  ➡️ Selected as password field")
            
            if email_field and password_field:
                # Fill email
                await email_field.click()
                await email_field.fill('')
                await email_field.type('comfort.uncounted44@mailer.me', delay=50)
                logger.info("✅ Filled email")
                
                # Fill password
                await password_field.click()
                await password_field.fill('')
                await password_field.type('5sqR*r3zjrp#FvAA9^@BGXhb', delay=50)
                logger.info("✅ Filled password")
                
                await page.screenshot(path='debug_3_filled_form.png')
                
                # Step 4: Submit form
                logger.info("🖱️ Step 4: Submit login form...")
                
                # Try to find submit button
                submit_selectors = [
                    'button[type="submit"]',
                    'button:has-text("Log In")',
                    'button:has-text("Sign In")',
                    'button:has-text("Login")',
                    'input[type="submit"]',
                    'button[class*="submit"]'
                ]
                
                submit_button = None
                for selector in submit_selectors:
                    try:
                        submit_button = await page.query_selector(selector)
                        if submit_button and await submit_button.is_visible():
                            logger.info(f"✅ Found submit button: {selector}")
                            break
                    except:
                        continue
                
                if submit_button:
                    await submit_button.click()
                    logger.info("✅ Clicked submit button")
                else:
                    # Try pressing Enter
                    await password_field.press('Enter')
                    logger.info("✅ Pressed Enter in password field")
                
                # Wait for navigation
                logger.info("⏳ Waiting for login to complete...")
                await asyncio.sleep(5)
                
                await page.screenshot(path='debug_4_after_login.png')
                current_url = page.url
                logger.info(f"📍 URL after login: {current_url}")
                
                # Step 5: Navigate to alerts page
                logger.info("🎯 Step 5: Navigate to alerts page...")
                await page.goto("https://www.mymama.uk/copy-of-alerts-essentials-1", wait_until='domcontentloaded')
                await asyncio.sleep(5)
                
                await page.screenshot(path='debug_5_alerts_page.png')
                
                # Get final content
                final_text = await page.inner_text('body')
                logger.info(f"📄 Final page content length: {len(final_text)}")
                
                # Save content
                with open('debug_final_content.txt', 'w') as f:
                    f.write(final_text)
                
                # Check content
                has_signup = 'sign up' in final_text.lower() or 'already a member' in final_text.lower()
                has_forex = 'forex' in final_text.lower() or 'eur' in final_text.lower() or 'usd' in final_text.lower()
                has_options = 'options' in final_text.lower() or 'call' in final_text.lower() or 'put' in final_text.lower()
                
                logger.info("🔍 Content Analysis:")
                logger.info(f"  - Has signup form: {has_signup}")
                logger.info(f"  - Has forex content: {has_forex}")
                logger.info(f"  - Has options content: {has_options}")
                
                if has_signup:
                    logger.error("❌ Still on signup page - authentication failed!")
                else:
                    logger.info("✅ Authentication appears successful!")
                
                # Print preview
                logger.info("📝 Content preview:")
                print(final_text[:500])
                
            else:
                logger.error("❌ Could not find email/password fields!")
                
                # Try to click around to find login form
                logger.info("🔍 Looking for any clickable login elements...")
                clickables = await page.query_selector_all('a, button, div[onclick], span[onclick]')
                for elem in clickables:
                    text = await elem.inner_text()
                    if text and ('log' in text.lower() or 'sign' in text.lower()):
                        logger.info(f"  Found: {text}")
            
            # Keep browser open for manual inspection
            logger.info("🔍 Browser will stay open for 60 seconds for inspection...")
            await asyncio.sleep(60)
            
            await browser.close()
            
    except Exception as e:
        logger.error(f"❌ Debug failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(debug_authentication())