#!/usr/bin/env python3
"""
Test real authentication with provided credentials
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
                headless=False,  # Show browser for debugging
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
            
            # Navigate to MyMama login page
            logger.info("🌐 Navigating to MyMama login page...")
            await page.goto("https://www.mymama.uk/login", wait_until='networkidle')
            await asyncio.sleep(3)
            
            # Look for email/username field
            logger.info("🔍 Looking for login fields...")
            
            # Try different selectors for email field
            email_selectors = [
                'input[type="email"]',
                'input[name="email"]',
                'input[placeholder*="email" i]',
                'input[placeholder*="username" i]',
                'input[id*="email" i]',
                'input[id*="username" i]',
                'input[aria-label*="email" i]'
            ]
            
            email_field = None
            for selector in email_selectors:
                try:
                    email_field = await page.query_selector(selector)
                    if email_field:
                        logger.info(f"✅ Found email field with selector: {selector}")
                        break
                except:
                    continue
            
            if not email_field:
                # If no email field found, list all input fields
                inputs = await page.query_selector_all('input')
                logger.info(f"📝 Found {len(inputs)} input fields:")
                for i, inp in enumerate(inputs):
                    inp_type = await inp.get_attribute('type')
                    inp_name = await inp.get_attribute('name')
                    inp_placeholder = await inp.get_attribute('placeholder')
                    inp_id = await inp.get_attribute('id')
                    logger.info(f"  {i+1}. Type: {inp_type}, Name: {inp_name}, ID: {inp_id}, Placeholder: {inp_placeholder}")
                
                # Try the first non-hidden input
                for inp in inputs:
                    inp_type = await inp.get_attribute('type')
                    if inp_type not in ['hidden', 'submit', 'button']:
                        email_field = inp
                        logger.info("📧 Using first available input field for email")
                        break
            
            if email_field:
                # Fill email
                await email_field.click()
                await email_field.fill('')  # Clear first
                await email_field.type('comfort.uncounted44@mailer.me', delay=100)
                logger.info("✅ Filled email field")
                
                # Look for password field
                password_selectors = [
                    'input[type="password"]',
                    'input[name="password"]',
                    'input[placeholder*="password" i]',
                    'input[id*="password" i]'
                ]
                
                password_field = None
                for selector in password_selectors:
                    try:
                        password_field = await page.query_selector(selector)
                        if password_field:
                            logger.info(f"✅ Found password field with selector: {selector}")
                            break
                    except:
                        continue
                
                if password_field:
                    await password_field.click()
                    await password_field.fill('')  # Clear first
                    await password_field.type('5sqR*r3zjrp#FvAA9^@BGXhb', delay=100)
                    logger.info("✅ Filled password field")
                    
                    # Look for submit button
                    submit_selectors = [
                        'button[type="submit"]',
                        'button:has-text("Log In")',
                        'button:has-text("Sign In")',
                        'input[type="submit"]',
                        'button:has-text("Submit")'
                    ]
                    
                    submit_button = None
                    for selector in submit_selectors:
                        try:
                            submit_button = await page.query_selector(selector)
                            if submit_button:
                                logger.info(f"✅ Found submit button with selector: {selector}")
                                break
                        except:
                            continue
                    
                    if submit_button:
                        # Take screenshot before submitting
                        await page.screenshot(path='before_login_submit.png')
                        logger.info("📸 Screenshot saved: before_login_submit.png")
                        
                        # Submit login
                        await submit_button.click()
                        logger.info("🖱️ Clicked submit button")
                        
                        # Wait for navigation
                        await asyncio.sleep(5)
                        
                        # Check where we are now
                        current_url = page.url
                        logger.info(f"📍 Current URL after login: {current_url}")
                        
                        # Take screenshot after login
                        await page.screenshot(path='after_login_submit.png')
                        logger.info("📸 Screenshot saved: after_login_submit.png")
                        
                        # Navigate to alerts page
                        logger.info("🎯 Navigating to alerts page...")
                        await page.goto("https://www.mymama.uk/copy-of-alerts-essentials-1", wait_until='networkidle')
                        await asyncio.sleep(5)
                        
                        # Get page content
                        page_text = await page.inner_text('body')
                        logger.info(f"📄 Page content length: {len(page_text)}")
                        
                        # Save content
                        with open('authenticated_content.txt', 'w') as f:
                            f.write(page_text)
                        logger.info("💾 Content saved to authenticated_content.txt")
                        
                        # Take final screenshot
                        await page.screenshot(path='alerts_page.png')
                        logger.info("📸 Screenshot saved: alerts_page.png")
                        
                        # Print first 1000 chars
                        logger.info("📝 First 1000 chars of content:")
                        print(page_text[:1000])
                        
                        # Check for specific content
                        if 'forex' in page_text.lower() or 'eur' in page_text.lower() or 'usd' in page_text.lower():
                            logger.info("✅ Found forex-related content!")
                        else:
                            logger.warning("⚠️ No forex content found")
                        
                        if 'options' in page_text.lower() or 'call' in page_text.lower() or 'put' in page_text.lower():
                            logger.info("✅ Found options-related content!")
                        else:
                            logger.warning("⚠️ No options content found")
            
            # Keep browser open for manual inspection
            logger.info("🔍 Browser will stay open for 30 seconds for inspection...")
            await asyncio.sleep(30)
            
            await browser.close()
            
    except Exception as e:
        logger.error(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_real_authentication())