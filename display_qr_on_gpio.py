#!/usr/bin/env python3
"""
Display WhatsApp QR code on GPIO display using framebuffer
"""

import os
import sys
import time
import logging
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def display_qr_on_framebuffer():
    """Display the WhatsApp QR code on the framebuffer device"""
    
    qr_file = Path("whatsapp_qr_headless.png")
    
    if not qr_file.exists():
        logger.error(f"❌ QR code file not found: {qr_file}")
        logger.info("💡 Generating new QR code...")
        # Try to generate a new QR code first
        os.system("source venv/bin/activate && python whatsapp_playwright_sender.py &")
        time.sleep(10)  # Wait for QR generation
        
        if not qr_file.exists():
            logger.error("❌ Failed to generate QR code")
            return False
    
    try:
        # Open the QR code image
        logger.info("📱 Loading WhatsApp QR code...")
        qr_image = Image.open(qr_file)
        
        # Get framebuffer info
        fb_device = "/dev/fb0"
        
        # Get display dimensions (common for Raspberry Pi displays)
        # You might need to adjust these based on your specific display
        try:
            # Try to get actual framebuffer dimensions
            fbinfo = os.popen("fbset -s").read()
            logger.info(f"Framebuffer info: {fbinfo}")
            
            # Default dimensions for common displays
            display_width = 800
            display_height = 480
            
            # Parse dimensions from fbset if available
            for line in fbinfo.split('\n'):
                if 'geometry' in line:
                    parts = line.split()
                    if len(parts) >= 3:
                        display_width = int(parts[1])
                        display_height = int(parts[2])
                        break
        except:
            # Default dimensions
            display_width = 800
            display_height = 480
        
        logger.info(f"📐 Display dimensions: {display_width}x{display_height}")
        
        # Create a new image with black background
        display_image = Image.new('RGB', (display_width, display_height), 'black')
        draw = ImageDraw.Draw(display_image)
        
        # Add title text
        title = "WhatsApp Authentication"
        subtitle = "Scan QR code with your phone"
        instruction = "Open WhatsApp > Settings > Linked Devices > Link Device"
        
        # Try to use a font (fallback to default if not available)
        try:
            font_size = 24
            title_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", font_size)
            text_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 18)
        except:
            title_font = ImageFont.load_default()
            text_font = ImageFont.load_default()
        
        # Draw title
        title_bbox = draw.textbbox((0, 0), title, font=title_font)
        title_width = title_bbox[2] - title_bbox[0]
        draw.text(((display_width - title_width) // 2, 20), title, fill='white', font=title_font)
        
        # Draw subtitle
        subtitle_bbox = draw.textbbox((0, 0), subtitle, font=text_font)
        subtitle_width = subtitle_bbox[2] - subtitle_bbox[0]
        draw.text(((display_width - subtitle_width) // 2, 60), subtitle, fill='white', font=text_font)
        
        # Resize QR code to fit display
        qr_size = min(display_width - 100, display_height - 200, 300)
        qr_resized = qr_image.resize((qr_size, qr_size), Image.Resampling.LANCZOS)
        
        # Center the QR code
        qr_x = (display_width - qr_size) // 2
        qr_y = (display_height - qr_size) // 2 + 20
        
        # Paste QR code onto display image
        display_image.paste(qr_resized, (qr_x, qr_y))
        
        # Draw instruction at bottom
        instruction_bbox = draw.textbbox((0, 0), instruction, font=text_font)
        instruction_width = instruction_bbox[2] - instruction_bbox[0]
        draw.text(((display_width - instruction_width) // 2, display_height - 40), instruction, fill='yellow', font=text_font)
        
        # Convert to RGB if needed (framebuffer usually wants RGB)
        if display_image.mode != 'RGB':
            display_image = display_image.convert('RGB')
        
        # Save the composed image
        composed_file = Path("whatsapp_qr_display.png")
        display_image.save(composed_file)
        logger.info(f"💾 Composed image saved to: {composed_file}")
        
        # Write directly to framebuffer
        logger.info("🖥️ Writing to framebuffer...")
        
        # Convert image to raw RGB data
        raw_data = display_image.tobytes()
        
        # Write to framebuffer
        with open(fb_device, 'wb') as fb:
            fb.write(raw_data)
        
        logger.info("✅ QR code displayed on GPIO display!")
        logger.info("📱 Please scan the QR code with WhatsApp")
        logger.info("⏰ Display will remain for 2 minutes...")
        
        # Keep the display active
        time.sleep(120)  # 2 minutes
        
        # Clear the display (optional - fill with black)
        logger.info("🔲 Clearing display...")
        black_screen = Image.new('RGB', (display_width, display_height), 'black')
        with open(fb_device, 'wb') as fb:
            fb.write(black_screen.tobytes())
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Error displaying QR code: {e}")
        import traceback
        traceback.print_exc()
        
        # Try alternative method using ImageMagick if available
        logger.info("🔄 Trying alternative display method...")
        try:
            os.system(f"convert {qr_file} -resize 400x400 -gravity center -background black -extent 800x480 rgb:- > /dev/fb0")
            logger.info("✅ QR code displayed using ImageMagick")
            time.sleep(120)
            return True
        except:
            pass
        
        return False

def main():
    """Main function"""
    logger.info("🚀 WhatsApp QR Code Display for GPIO")
    logger.info("=" * 50)
    
    # Check if running as root (might be needed for framebuffer access)
    if os.geteuid() != 0:
        logger.warning("⚠️ Not running as root - framebuffer access might fail")
        logger.info("💡 Try: sudo python3 display_qr_on_gpio.py")
    
    success = display_qr_on_framebuffer()
    
    if success:
        logger.info("\n✅ QR code was displayed successfully")
        logger.info("📱 Once scanned, WhatsApp will be authenticated")
        logger.info("🔄 The daily reports will then include WhatsApp automatically")
    else:
        logger.error("\n❌ Failed to display QR code on GPIO display")
        logger.info("💡 Alternative: Check whatsapp_qr_headless.png file manually")

if __name__ == "__main__":
    main()