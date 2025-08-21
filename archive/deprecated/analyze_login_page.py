#!/usr/bin/env python3
"""
Analyze the actual MyMama login page structure
"""
import asyncio
import logging
from playwright.async_api import async_playwright

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def analyze_login_page():
    """Analyze the login page structure"""
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)  # Run in headless mode for server
            page = await browser.new_page()
            
            # Navigate to main page first
            logger.info("🌐 Navigating to main page...")
            await page.goto("https://www.mymama.uk", wait_until='networkidle')
            await asyncio.sleep(3)
            
            # Take screenshot of main page
            await page.screenshot(path='main_page.png')
            logger.info("📸 Screenshot saved: main_page.png")
            
            # Look for login links/buttons
            logger.info("🔍 Looking for login elements...")
            
            # Check all clickable elements
            elements = await page.query_selector_all('a, button')
            login_elements = []
            
            for element in elements:
                text = await element.inner_text()
                href = await element.get_attribute('href')
                
                if text and ('log' in text.lower() or 'sign' in text.lower()):
                    login_elements.append({
                        'text': text.strip(),
                        'href': href,
                        'tag': await element.evaluate('el => el.tagName')
                    })
            
            logger.info(f"📋 Found {len(login_elements)} login-related elements:")
            for elem in login_elements:
                logger.info(f"  - {elem['tag']}: '{elem['text']}' -> {elem['href']}")
            
            # Try clicking on "Log In" if it exists
            if login_elements:
                for elem in login_elements:
                    if 'log in' in elem['text'].lower():
                        logger.info(f"🖱️ Clicking on: {elem['text']}")
                        
                        # Find and click the element
                        login_button = await page.query_selector(f"text='{elem['text']}'")
                        if login_button:
                            await login_button.click()
                            await asyncio.sleep(5)
                            
                            # Take screenshot after clicking
                            await page.screenshot(path='after_login_click.png')
                            logger.info("📸 Screenshot saved: after_login_click.png")
                            
                            # Check what page we're on now
                            current_url = page.url
                            logger.info(f"📍 Current URL: {current_url}")
                            
                            # Get page content
                            page_text = await page.inner_text('body')
                            with open('login_page_content.txt', 'w') as f:
                                f.write(page_text)
                            
                            logger.info(f"📄 Login page content ({len(page_text)} chars) saved to login_page_content.txt")
                            
                            # Look for form fields
                            inputs = await page.query_selector_all('input')
                            logger.info(f"📝 Found {len(inputs)} input fields:")
                            
                            for i, inp in enumerate(inputs):
                                inp_type = await inp.get_attribute('type')
                                inp_name = await inp.get_attribute('name')
                                inp_placeholder = await inp.get_attribute('placeholder')
                                inp_id = await inp.get_attribute('id')
                                
                                logger.info(f"  {i+1}. Type: {inp_type}, Name: {inp_name}, ID: {inp_id}, Placeholder: {inp_placeholder}")
                            
                            break
            
            await browser.close()
            
    except Exception as e:
        logger.error(f"❌ Analysis failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(analyze_login_page())