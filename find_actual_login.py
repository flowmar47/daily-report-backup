#!/usr/bin/env python3
"""
Find actual login/access method on current MyMama.uk site
"""

import asyncio
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def analyze_actual_site_structure():
    """Analyze what's actually on the MyMama.uk site now"""
    
    try:
        from playwright.async_api import async_playwright
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True, args=['--no-sandbox', '--disable-dev-shm-usage'])
            page = await browser.new_page()
            
            # Navigate to main page
            logger.info("🔍 Analyzing current MyMama.uk site structure...")
            await page.goto('https://www.mymama.uk', wait_until='networkidle', timeout=30000)
            await page.wait_for_timeout(3000)
            
            # Get all links and buttons
            logger.info("\n=== ALL LINKS ON PAGE ===")
            links = await page.locator('a').all()
            for i, link in enumerate(links[:20]):  # First 20 links
                try:
                    href = await link.get_attribute('href')
                    text = await link.inner_text()
                    if href or text.strip():
                        logger.info(f"Link {i}: '{text.strip()[:50]}' -> {href}")
                except:
                    pass
            
            logger.info("\n=== ALL BUTTONS ON PAGE ===")
            buttons = await page.locator('button').all()
            for i, button in enumerate(buttons):
                try:
                    text = await button.inner_text()
                    classes = await button.get_attribute('class')
                    onclick = await button.get_attribute('onclick')
                    logger.info(f"Button {i}: '{text.strip()[:50]}' class='{classes}' onclick='{onclick}'")
                except:
                    pass
            
            # Look for any text containing "member", "account", "login", etc.
            logger.info("\n=== SEARCHING FOR ACCESS-RELATED TEXT ===")
            access_keywords = ['member', 'account', 'login', 'sign', 'access', 'subscribe', 'join']
            page_text = await page.inner_text('body')
            
            for keyword in access_keywords:
                if keyword.lower() in page_text.lower():
                    logger.info(f"✅ Found keyword '{keyword}' in page content")
                    # Find surrounding context
                    lines = page_text.split('\n')
                    for line_num, line in enumerate(lines):
                        if keyword.lower() in line.lower():
                            context_start = max(0, line_num - 2)
                            context_end = min(len(lines), line_num + 3)
                            context = '\n'.join(lines[context_start:context_end])
                            logger.info(f"   Context: {context[:200]}...")
                            break
                else:
                    logger.info(f"❌ No '{keyword}' found")
            
            # Check specific URLs that might work
            logger.info("\n=== TESTING ALTERNATIVE ACCESS URLS ===")
            test_urls = [
                'https://www.mymama.uk/account',
                'https://www.mymama.uk/signin',
                'https://www.mymama.uk/members',
                'https://www.mymama.uk/register',
                'https://www.mymama.uk/dashboard',
                'https://www.mymama.uk/alerts',
                'https://www.mymama.uk/forecast',
                'https://www.mymama.uk/copy-of-alerts-essentials-1',  # Target page
            ]
            
            for url in test_urls:
                try:
                    await page.goto(url, wait_until='networkidle', timeout=10000)
                    await page.wait_for_timeout(2000)
                    
                    title = await page.title()
                    current_url = page.url
                    content_preview = await page.inner_text('body')
                    
                    logger.info(f"\n📍 {url}")
                    logger.info(f"   Final URL: {current_url}")
                    logger.info(f"   Title: {title}")
                    logger.info(f"   Content: {content_preview[:150]}...")
                    
                    # Check if this looks like a login page
                    if any(word in content_preview.lower() for word in ['password', 'email', 'login', 'sign in']):
                        logger.info("   🔐 POSSIBLE LOGIN PAGE DETECTED!")
                        
                        # Save this page
                        html = await page.content()
                        url_safe = url.replace('https://www.mymama.uk/', '').replace('/', '_')
                        with open(f'debug_potential_login_{url_safe}.html', 'w') as f:
                            f.write(html)
                        logger.info(f"   💾 Saved HTML as debug_potential_login_{url_safe}.html")
                    
                except Exception as e:
                    logger.info(f"❌ {url}: {str(e)[:100]}")
            
            await browser.close()
            
    except Exception as e:
        logger.error(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(analyze_actual_site_structure())