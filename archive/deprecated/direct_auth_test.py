#!/usr/bin/env python3
"""
Direct authentication test to understand what's happening
"""
import asyncio
import logging
from playwright.async_api import async_playwright
from dotenv import load_dotenv
import os

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def direct_auth_test():
    """Test authentication step by step"""
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context(
                viewport={'width': 1280, 'height': 720},
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            )
            page = await context.new_page()
            
            logger.info("🌐 Step 1: Navigate to main page...")
            await page.goto("https://www.mymama.uk", wait_until='domcontentloaded')
            await asyncio.sleep(3)
            
            # Save main page
            main_content = await page.inner_text('body')
            logger.info(f"📄 Main page content: {len(main_content)} chars")
            
            with open('step1_main_page.txt', 'w') as f:
                f.write(main_content)
            
            # Look for login
            logger.info("🔍 Step 2: Looking for login...")
            if 'log in' in main_content.lower() or 'login' in main_content.lower():
                logger.info("✅ Found login text on main page")
                
                # Try to click login
                login_elements = await page.query_selector_all('a:has-text("Log In"), a:has-text("Login")')
                if login_elements:
                    logger.info(f"✅ Found {len(login_elements)} login elements")
                    await login_elements[0].click()
                    await asyncio.sleep(3)
                    
                    # Check where we are
                    current_url = page.url
                    logger.info(f"📍 After click URL: {current_url}")
                    
                    login_page_content = await page.inner_text('body')
                    with open('step2_login_page.txt', 'w') as f:
                        f.write(login_page_content)
                    logger.info(f"📄 Login page content: {len(login_page_content)} chars")
                else:
                    logger.warning("⚠️ No clickable login elements found")
                    # Try direct navigation
                    logger.info("🔄 Direct navigation to login...")
                    await page.goto("https://www.mymama.uk/login", wait_until='domcontentloaded')
                    await asyncio.sleep(3)
            
            # Step 3: Try to fill login form
            logger.info("📝 Step 3: Fill login form...")
            
            # Get all inputs
            inputs = await page.query_selector_all('input')
            logger.info(f"🔍 Found {len(inputs)} input fields")
            
            email_field = None
            password_field = None
            
            # Analyze all inputs
            for i, inp in enumerate(inputs):
                inp_type = await inp.get_attribute('type') or 'text'
                inp_name = await inp.get_attribute('name') or ''
                inp_placeholder = await inp.get_attribute('placeholder') or ''
                inp_id = await inp.get_attribute('id') or ''
                
                logger.info(f"  Input {i}: type={inp_type}, name={inp_name}, id={inp_id}, placeholder={inp_placeholder}")
                
                if inp_type == 'email' or 'email' in inp_placeholder.lower():
                    email_field = inp
                elif inp_type == 'password':
                    password_field = inp
            
            if email_field and password_field:
                logger.info("✅ Found email and password fields")
                
                # Fill credentials
                await email_field.fill('comfort.uncounted44@mailer.me')
                await password_field.fill('5sqR*r3zjrp#FvAA9^@BGXhb')
                logger.info("✅ Filled credentials")
                
                # Submit
                submit_btn = await page.query_selector('button[type="submit"], button:has-text("Log In")')
                if submit_btn:
                    await submit_btn.click()
                    logger.info("✅ Clicked submit")
                else:
                    await password_field.press('Enter')
                    logger.info("✅ Pressed Enter")
                
                # Wait and check result
                await asyncio.sleep(5)
                
                # Check authentication result
                auth_url = page.url
                auth_content = await page.inner_text('body')
                logger.info(f"📍 After auth URL: {auth_url}")
                logger.info(f"📄 After auth content: {len(auth_content)} chars")
                
                with open('step3_after_auth.txt', 'w') as f:
                    f.write(auth_content)
                
                # Check for success indicators
                if 'welcome' in auth_content.lower() or 'dashboard' in auth_content.lower():
                    logger.info("✅ Authentication appears successful")
                elif 'sign up' in auth_content.lower() or 'log in' in auth_content.lower():
                    logger.warning("⚠️ Still on login page - auth failed")
                else:
                    logger.info("❓ Authentication status unclear")
                
                # Step 4: Navigate to alerts page
                logger.info("🎯 Step 4: Navigate to alerts page...")
                await page.goto("https://www.mymama.uk/copy-of-alerts-essentials-1", wait_until='domcontentloaded')
                await asyncio.sleep(10)  # Wait longer for Wix
                
                alerts_content = await page.inner_text('body')
                alerts_url = page.url
                logger.info(f"📍 Alerts page URL: {alerts_url}")
                logger.info(f"📄 Alerts content: {len(alerts_content)} chars")
                
                with open('step4_alerts_page.txt', 'w') as f:
                    f.write(alerts_content)
                
                # Analyze alerts page
                if len(alerts_content) < 200:
                    logger.warning("⚠️ Very short alerts content - likely restricted")
                    
                    # Check for specific issues
                    if 'sign up' in alerts_content.lower():
                        logger.error("❌ Redirected back to signup - premium access required?")
                    elif 'loading' in alerts_content.lower():
                        logger.warning("⚠️ Page still loading - may need more time")
                    elif 'not found' in alerts_content.lower():
                        logger.error("❌ Page not found - URL may be incorrect")
                    else:
                        logger.warning("⚠️ Unknown issue with alerts page")
                
                # Print sample content
                logger.info("📝 Alerts page sample:")
                print(alerts_content[:500])
                
            else:
                logger.error("❌ Could not find login form fields")
                current_content = await page.inner_text('body')
                logger.info("📝 Current page sample:")
                print(current_content[:500])
            
            await browser.close()
            
    except Exception as e:
        logger.error(f"❌ Direct auth test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(direct_auth_test())