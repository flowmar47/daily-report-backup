#!/usr/bin/env python3
"""
Display WhatsApp QR code using fbi framebuffer imageviewer
"""

import os
import subprocess
import time
import signal
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def display_qr_with_fbi():
    """Display QR code using fbi"""
    
    qr_file = Path("whatsapp_qr_headless.png")
    
    if not qr_file.exists():
        logger.error(f"❌ QR file not found: {qr_file}")
        return False
    
    try:
        logger.info("🖥️ Displaying QR code on GPIO display with fbi...")
        
        # Kill any existing fbi processes
        subprocess.run(["sudo", "pkill", "-f", "fbi"], capture_output=True)
        
        # Display QR code using fbi
        cmd = [
            "sudo", "fbi", 
            "-d", "/dev/fb0",     # Framebuffer device
            "-T", "1",            # Virtual terminal 1
            "--noverbose",        # Suppress verbose output
            "-a",                 # Autozoom to fit
            "--once",             # Show once, don't loop
            str(qr_file)
        ]
        
        logger.info(f"📱 Running: {' '.join(cmd)}")
        
        # Start fbi process
        process = subprocess.Popen(
            cmd, 
            stdout=subprocess.PIPE, 
            stderr=subprocess.PIPE,
            preexec_fn=os.setsid  # Create new process group
        )
        
        logger.info("✅ QR code should now be visible on your GPIO display!")
        logger.info("📱 To authenticate WhatsApp:")
        logger.info("   1. Open WhatsApp on your phone")
        logger.info("   2. Go to Settings > Linked Devices")
        logger.info("   3. Tap 'Link Device'")
        logger.info("   4. Scan the QR code on your display")
        logger.info("")
        logger.info("⏰ Display will remain active for 2 minutes...")
        
        # Keep display active for 2 minutes
        time.sleep(120)
        
        # Clean shutdown
        logger.info("🔲 Clearing display...")
        
        try:
            # Terminate the process group
            os.killpg(os.getpgid(process.pid), signal.SIGTERM)
            process.wait(timeout=5)
        except:
            # Force kill if needed
            subprocess.run(["sudo", "pkill", "-f", "fbi"], capture_output=True)
        
        # Clear framebuffer to black
        with open('/dev/fb0', 'wb') as fb:
            fb.write(b'\x00\x00' * 76800)  # 480*320 pixels in RGB565
        
        logger.info("✅ Display cleared successfully")
        return True
        
    except Exception as e:
        logger.error(f"❌ Error displaying QR code: {e}")
        # Cleanup on error
        subprocess.run(["sudo", "pkill", "-f", "fbi"], capture_output=True)
        return False

def main():
    logger.info("🚀 WhatsApp QR Code Display using fbi")
    logger.info("=" * 50)
    
    success = display_qr_with_fbi()
    
    if success:
        logger.info("🎉 QR display completed successfully!")
        logger.info("🔍 Now checking WhatsApp authentication status...")
        
        # Check if authentication was successful
        try:
            subprocess.run(["python", "check_whatsapp_auth.py"], check=True)
        except subprocess.CalledProcessError:
            logger.warning("⚠️ Could not check WhatsApp auth status")
            
    else:
        logger.error("❌ Failed to display QR code")
        logger.info("💡 Alternative: View the QR code manually:")
        logger.info(f"📍 {Path('whatsapp_qr_headless.png').absolute()}")

if __name__ == "__main__":
    main()