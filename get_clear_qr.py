#!/usr/bin/env python3
"""
Get a clear, large QR code from WhatsApp Web
"""

import asyncio
from playwright.async_api import async_playwright
import logging
from PIL import Image, ImageEnhance, ImageFilter
import io

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def get_clear_qr():
    """Get a high-quality QR code"""
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=['--no-sandbox', '--disable-dev-shm-usage']
        )
        
        # Larger viewport for better quality
        context = await browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            device_scale_factor=2  # Higher resolution
        )
        
        page = await context.new_page()
        
        logger.info("Getting high-quality QR code...")
        
        # Navigate to WhatsApp
        await page.goto('https://web.whatsapp.com')
        await page.wait_for_timeout(5000)
        
        try:
            # Wait for QR container
            qr_container = await page.wait_for_selector('[data-testid="qrcode"]', timeout=10000)
            
            if not qr_container:
                # Try alternative selector
                qr_container = await page.wait_for_selector('div._nggjq11', timeout=5000)
            
            # Take high-res screenshot
            logger.info("Taking high-resolution screenshot...")
            
            # Get bounding box
            box = await qr_container.bounding_box()
            
            # Take full page screenshot
            full_screenshot = await page.screenshot()
            
            # Also take element screenshot with padding
            element_screenshot = await qr_container.screenshot()
            
            # Process the QR code
            logger.info("Processing QR code for clarity...")
            
            # Load element screenshot
            qr_img = Image.open(io.BytesIO(element_screenshot))
            
            # Make it larger
            new_size = (800, 800)
            qr_large = qr_img.resize(new_size, Image.Resampling.LANCZOS)
            
            # Enhance contrast
            enhancer = ImageEnhance.Contrast(qr_large)
            qr_enhanced = enhancer.enhance(2.0)
            
            # Convert to pure black and white
            qr_bw = qr_enhanced.convert('L')
            threshold = 128
            qr_bw = qr_bw.point(lambda p: 255 if p > threshold else 0, mode='1')
            
            # Save different versions
            qr_img.save('whatsapp_qr_original.png')
            qr_large.save('whatsapp_qr_large.png')
            qr_bw.save('whatsapp_qr_clear.png')
            
            logger.info("QR codes saved:")
            logger.info("- whatsapp_qr_original.png (original)")
            logger.info("- whatsapp_qr_large.png (800x800)")
            logger.info("- whatsapp_qr_clear.png (high contrast B&W)")
            
            # Update for web server
            import shutil
            shutil.copy('whatsapp_qr_clear.png', 'whatsapp_qr_fresh.png')
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to get QR: {e}")
            
            # Try alternative method
            logger.info("Trying alternative method...")
            
            # Take viewport screenshot
            await page.set_viewport_size({'width': 1920, 'height': 1080})
            await page.screenshot(path='whatsapp_full_viewport.png')
            
            # Look for QR in specific area
            qr_elements = await page.query_selector_all('canvas')
            for i, canvas in enumerate(qr_elements):
                try:
                    await canvas.screenshot(path=f'whatsapp_canvas_{i}.png')
                    logger.info(f"Saved canvas {i}")
                except:
                    pass
                    
            return False
            
        finally:
            await browser.close()

async def main():
    logger.info("Getting clear WhatsApp QR code...")
    logger.info("=" * 50)
    
    success = await get_clear_qr()
    
    if success:
        logger.info("\n✅ Clear QR codes generated!")
        logger.info("Check http://192.168.0.175:8888 for the new QR")
        logger.info("\nAlso saved locally as:")
        logger.info("- whatsapp_qr_clear.png (best for scanning)")
        logger.info("- whatsapp_qr_large.png (enlarged version)")
    else:
        logger.info("\n❌ Failed to get clear QR")
        logger.info("Check whatsapp_full_viewport.png for manual cropping")

if __name__ == "__main__":
    asyncio.run(main())