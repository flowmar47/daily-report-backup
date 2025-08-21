#!/usr/bin/env python3
"""
Simple WhatsApp QR display for 480x320 GPIO display with 16-bit color
"""

import os
import struct
import logging
from pathlib import Path
from PIL import Image

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def rgb_to_rgb565(r, g, b):
    """Convert RGB888 to RGB565 format for 16-bit display"""
    return ((r & 0xF8) << 8) | ((g & 0xFC) << 3) | (b >> 3)

def display_qr_simple():
    """Display QR code on 480x320 16-bit framebuffer"""
    
    qr_file = Path("whatsapp_qr_headless.png")
    if not qr_file.exists():
        logger.error(f"❌ QR code not found: {qr_file}")
        return False
    
    try:
        # Display dimensions from fbset output
        WIDTH = 480
        HEIGHT = 320
        
        logger.info(f"📱 Loading QR code for {WIDTH}x{HEIGHT} display...")
        
        # Load and process QR code
        qr_image = Image.open(qr_file)
        
        # Create display image with white background
        display = Image.new('RGB', (WIDTH, HEIGHT), 'white')
        
        # Resize QR code to fit (leave margins)
        qr_size = min(WIDTH, HEIGHT) - 40  # 280 pixels
        qr_resized = qr_image.resize((qr_size, qr_size), Image.Resampling.LANCZOS)
        
        # Center the QR code
        x = (WIDTH - qr_size) // 2
        y = (HEIGHT - qr_size) // 2
        
        display.paste(qr_resized, (x, y))
        
        # Convert to RGB565 format for 16-bit framebuffer
        logger.info("🔄 Converting to 16-bit format...")
        
        fb_data = bytearray()
        pixels = display.load()
        
        for y in range(HEIGHT):
            for x in range(WIDTH):
                r, g, b = pixels[x, y]
                rgb565 = rgb_to_rgb565(r, g, b)
                # Pack as little-endian 16-bit
                fb_data.extend(struct.pack('<H', rgb565))
        
        # Write to framebuffer
        logger.info("🖥️ Writing to framebuffer...")
        with open('/dev/fb0', 'wb') as fb:
            fb.write(fb_data)
        
        logger.info("✅ QR code displayed!")
        logger.info("📱 Scan with WhatsApp: Settings > Linked Devices > Link Device")
        
        # Keep display active
        import time
        time.sleep(120)  # 2 minutes
        
        # Clear display
        logger.info("🔲 Clearing display...")
        clear_data = bytearray(WIDTH * HEIGHT * 2)  # All zeros = black
        with open('/dev/fb0', 'wb') as fb:
            fb.write(clear_data)
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Error: {e}")
        
        # Try using cat command as fallback
        logger.info("🔄 Trying direct copy method...")
        try:
            # First convert QR to correct size
            os.system(f"python3 -c \"from PIL import Image; img=Image.open('{qr_file}'); img=img.resize((280,280)); display=Image.new('RGB',(480,320),'white'); display.paste(img,((480-280)//2,(320-280)//2)); display.save('qr_display_temp.bmp')\"")
            
            # Try to display using dd
            os.system("dd if=qr_display_temp.bmp of=/dev/fb0 bs=1M 2>/dev/null")
            
            logger.info("✅ QR displayed using dd")
            return True
        except:
            pass
        
        return False

if __name__ == "__main__":
    logger.info("🚀 Simple QR Display for GPIO")
    logger.info("=" * 40)
    
    success = display_qr_simple()
    
    if not success:
        logger.info("\n💡 Alternative: Open whatsapp_qr_headless.png manually")
        logger.info("📍 Location: /home/ohms/OhmsAlertsReports/daily-report/whatsapp_qr_headless.png")