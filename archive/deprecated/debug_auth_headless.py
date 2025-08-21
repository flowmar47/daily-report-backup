#!/usr/bin/env python3
"""
Debug authentication in headless mode
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

async def debug_auth_headless():
    """Debug authentication headless with detailed logging"""
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
            
            # Step 1: Navigate to main page
            logger.info("🌐 Step 1: Navigate to MyMama main page...")
            await page.goto("https://www.mymama.uk", wait_until='domcontentloaded')
            await asyncio.sleep(3)
            
            main_text = await page.inner_text('body')
            logger.info(f"📄 Main page content: {len(main_text)} chars")
            
            # Step 2: Look for login elements
            logger.info("🔍 Step 2: Looking for login elements...")
            
            # Get all links and buttons
            all_links = await page.query_selector_all('a')
            all_buttons = await page.query_selector_all('button')
            
            login_found = False
            
            for link in all_links:
                text = await link.inner_text()
                href = await link.get_attribute('href')
                if text and ('log' in text.lower() or 'sign' in text.lower()):
                    logger.info(f"  Link: '{text}' -> {href}")
                    if not login_found and 'log' in text.lower():
                        logger.info(f"  🖱️ Clicking: {text}")
                        await link.click()
                        await asyncio.sleep(3)
                        login_found = True
                        break
            
            if not login_found:
                # Try direct navigation
                logger.info("🔄 Direct navigation to login page...")
                await page.goto("https://www.mymama.uk/login", wait_until='domcontentloaded')
                await asyncio.sleep(3)
            
            # Step 3: Check what page we're on
            current_url = page.url
            page_text = await page.inner_text('body')
            logger.info(f"📍 Current URL: {current_url}")
            logger.info(f"📄 Page content: {len(page_text)} chars")
            
            # Save page content for analysis
            with open('debug_login_page.txt', 'w') as f:
                f.write(page_text)
            
            # Step 4: Try to find and fill login form
            logger.info("📝 Step 4: Looking for login form...")
            
            # Get all input fields
            inputs = await page.query_selector_all('input')
            logger.info(f"🔍 Found {len(inputs)} input fields")
            
            email_field = None
            password_field = None
            
            for i, inp in enumerate(inputs):
                inp_type = await inp.get_attribute('type') or 'text'
                inp_name = await inp.get_attribute('name') or ''
                inp_placeholder = await inp.get_attribute('placeholder') or ''
                inp_id = await inp.get_attribute('id') or ''
                
                logger.info(f"  Input {i+1}: type={inp_type}, name={inp_name}, id={inp_id}, placeholder={inp_placeholder}")
                
                # Check for email field
                if not email_field and (
                    inp_type == 'email' or 
                    'email' in inp_name.lower() or 
                    'email' in inp_placeholder.lower() or
                    'username' in inp_name.lower()
                ):
                    email_field = inp
                    logger.info(f"  ➡️ Selected as email field")
                
                # Check for password field
                if not password_field and inp_type == 'password':
                    password_field = inp
                    logger.info(f"  ➡️ Selected as password field")
            
            if email_field and password_field:
                logger.info("✅ Found both email and password fields")
                
                # Fill credentials
                await email_field.fill('comfort.uncounted44@mailer.me')
                logger.info("✅ Filled email")
                
                await password_field.fill('5sqR*r3zjrp#FvAA9^@BGXhb')
                logger.info("✅ Filled password")
                
                # Look for submit button
                submit_buttons = await page.query_selector_all('button[type="submit"], button:has-text("Log In"), button:has-text("Sign In"), input[type="submit"]')
                
                if submit_buttons:
                    logger.info(f"✅ Found {len(submit_buttons)} submit buttons")
                    await submit_buttons[0].click()
                    logger.info("✅ Clicked submit")
                else:
                    # Try Enter key
                    await password_field.press('Enter')
                    logger.info("✅ Pressed Enter")
                
                # Wait for login
                await asyncio.sleep(5)
                
                # Check login result
                after_login_url = page.url
                after_login_text = await page.inner_text('body')
                logger.info(f"📍 After login URL: {after_login_url}")
                logger.info(f"📄 After login content: {len(after_login_text)} chars")
                
                # Save after login content
                with open('debug_after_login.txt', 'w') as f:
                    f.write(after_login_text)
                
                # Step 5: Navigate to alerts page
                logger.info("🎯 Step 5: Navigate to alerts page...")
                await page.goto("https://www.mymama.uk/copy-of-alerts-essentials-1", wait_until='domcontentloaded')
                await asyncio.sleep(10)  # Give more time for Wix to load
                
                # Get final content
                final_url = page.url
                final_text = await page.inner_text('body')
                logger.info(f"📍 Final URL: {final_url}")
                logger.info(f"📄 Final content: {len(final_text)} chars")
                
                # Save final content
                with open('debug_final_alerts.txt', 'w') as f:
                    f.write(final_text)
                
                # Analyze content
                has_signup = 'sign up' in final_text.lower() or 'already a member' in final_text.lower()
                has_forex = any(term in final_text.lower() for term in ['forex', 'eur/usd', 'gbp/usd', 'currency'])
                has_options = any(term in final_text.lower() for term in ['options', 'call', 'put', 'strike'])
                has_trades = any(term in final_text.lower() for term in ['trade', 'buy', 'sell', 'signal'])
                
                logger.info("🔍 Final Content Analysis:")
                logger.info(f"  - Has signup form: {has_signup}")
                logger.info(f"  - Has forex content: {has_forex}")
                logger.info(f"  - Has options content: {has_options}")
                logger.info(f"  - Has trading content: {has_trades}")
                logger.info(f"  - Content length: {len(final_text)}")
                
                # Print first 500 chars
                logger.info("📝 Content preview (first 500 chars):")
                print(final_text[:500])
                
                if has_signup and len(final_text) < 200:
                    logger.error("❌ Authentication failed - still on signup page")
                elif len(final_text) > 1000 and (has_forex or has_options or has_trades):
                    logger.info("✅ Authentication successful - found trading content")
                else:
                    logger.warning("⚠️ Authentication unclear - content needs analysis")
                
            else:
                logger.error("❌ Could not find login form fields")
                logger.info("📝 Page content preview:")
                print(page_text[:1000])
                
            await browser.close()
            
    except Exception as e:
        logger.error(f"❌ Debug failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(debug_auth_headless())