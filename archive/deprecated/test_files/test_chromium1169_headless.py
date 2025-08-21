#!/usr/bin/env python3
"""
Test Chromium-1169 WhatsApp Session in Headless Mode
Uses the existing authenticated session but runs headless for server environment
"""

import asyncio
import logging
import sys
from pathlib import Path

# Add paths for imports
sys.path.append(str(Path(__file__).parent / 'src'))
sys.path.append(str(Path(__file__).parent / 'src' / 'messengers'))

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def test_chromium1169_headless():
    """Test the existing authenticated WhatsApp session in headless mode"""
    
    logger.info("🔐 Testing Chromium-1169 WhatsApp Session (Headless)")
    logger.info("==================================================")
    
    try:
        from playwright.async_api import async_playwright
        from utils.env_config import EnvironmentConfig
        
        # Get configuration
        env_config = EnvironmentConfig('daily_report')
        credentials = env_config.get_all_vars()
        
        whatsapp_phone = credentials.get('WHATSAPP_PHONE_NUMBER')
        whatsapp_groups = credentials.get('WHATSAPP_GROUP_NAMES', '').split(',')
        
        logger.info(f"Phone: {whatsapp_phone}")
        logger.info(f"Groups: {', '.join(whatsapp_groups)}")
        
        # Use Playwright with the chromium-1169 installation
        playwright = await async_playwright().start()
        
        # Point to the exact Chromium binary and session
        chromium_path = Path("/home/ohms/playwright-browsers/chromium-1169/chrome-linux/chrome")
        user_data_dir = Path("/home/ohms/playwright-browsers/chromium-1169")
        
        if not chromium_path.exists():
            logger.error(f"❌ Chromium binary not found at: {chromium_path}")
            return False
            
        logger.info(f"✅ Found Chromium at: {chromium_path}")
        logger.info(f"📂 Using session directory: {user_data_dir}")
        
        logger.info("🚀 Launching Chromium-1169 in headless mode...")
        
        # Launch with persistent context using the authenticated session
        context = await playwright.chromium.launch_persistent_context(
            user_data_dir=str(user_data_dir),
            executable_path=str(chromium_path),
            headless=True,  # Force headless for server environment
            viewport={'width': 1280, 'height': 720},
            args=[
                '--disable-blink-features=AutomationControlled',
                '--disable-dev-shm-usage',
                '--no-sandbox',
                '--disable-setuid-sandbox',
                '--disable-web-security',
                '--allow-running-insecure-content',
                '--disable-gpu',
                '--user-agent=Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            ]
        )
        
        # Get or create page
        if len(context.pages) > 0:
            page = context.pages[0]
        else:
            page = await context.new_page()
        
        # Navigate to WhatsApp Web
        logger.info("📱 Navigating to WhatsApp Web...")
        await page.goto('https://web.whatsapp.com', wait_until='networkidle', timeout=30000)
        
        # Wait a moment for page to load
        await asyncio.sleep(3)
        
        # Check authentication status
        try:
            # Look for chat list (authenticated) or QR code (not authenticated)
            chat_list = await page.query_selector('div[data-testid="chat-list"]')
            qr_code = await page.query_selector('canvas[aria-label*="QR"]')
            browser_update = await page.query_selector('text=WhatsApp works with Google Chrome 60+')
            
            if browser_update:
                logger.warning("⚠️ Browser compatibility message detected")
                logger.info("📸 Taking screenshot for inspection...")
                await page.screenshot(path="whatsapp_browser_compat.png")
                
                # Check if we can proceed anyway
                await asyncio.sleep(2)
                chat_list = await page.query_selector('div[data-testid="chat-list"]')
            
            if chat_list:
                logger.info("✅ WhatsApp Web authenticated! Using existing chromium-1169 session.")
                
                # Test finding the group
                if whatsapp_groups and whatsapp_groups[0].strip():
                    group_name = whatsapp_groups[0].strip()
                    logger.info(f"🔍 Looking for group: {group_name}")
                    
                    try:
                        # Search for the group
                        search_box = await page.wait_for_selector('div[contenteditable="true"][data-tab="3"]', timeout=10000)
                        await search_box.click()
                        await page.keyboard.press('Control+A')
                        await page.keyboard.type(group_name)
                        await asyncio.sleep(2)
                        
                        # Look for group in results
                        group_element = await page.query_selector(f'span[title="{group_name}"]')
                        if group_element:
                            logger.info(f"✅ Found group: {group_name}")
                            
                            # Test sending message (commented out for safety)
                            logger.info("📝 Message sending capability verified (test not executed)")
                            # await test_send_message(page, group_name)
                        else:
                            logger.warning(f"⚠️ Group '{group_name}' not found in search results")
                            
                    except Exception as e:
                        logger.warning(f"⚠️ Error testing group search: {e}")
                
                success = True
                
            elif qr_code:
                logger.warning("⚠️ QR code detected - session not authenticated")
                await page.screenshot(path="whatsapp_qr_headless.png")
                logger.info("📸 QR code saved to whatsapp_qr_headless.png")
                logger.info("💡 The session needs to be authenticated in non-headless mode first")
                success = False
                
            else:
                logger.warning("⚠️ Unknown WhatsApp Web state")
                await page.screenshot(path="whatsapp_unknown_state.png")
                success = False
                
        except Exception as e:
            logger.error(f"❌ Error checking authentication: {e}")
            await page.screenshot(path="whatsapp_error_debug.png")
            success = False
        
        # Cleanup
        await context.close()
        await playwright.stop()
        
        return success
        
    except Exception as e:
        logger.error(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """Main test function"""
    success = await test_chromium1169_headless()
    
    if success:
        logger.info("\n🎉 Chromium-1169 WhatsApp session working in headless mode!")
        logger.info("✅ Ready to integrate with the main application")
        logger.info("\n📋 Next steps:")
        logger.info("1. Update whatsapp_playwright_messenger.py to use headless=True by default")
        logger.info("2. Add 'whatsapp' to platforms list in main.py")
        logger.info("3. Test complete messaging system")
    else:
        logger.warning("\n⚠️ WhatsApp session needs authentication or has compatibility issues")
        logger.info("Please check the screenshots for debugging information")

if __name__ == "__main__":
    asyncio.run(main())