#!/usr/bin/env python3
"""
Simple test to display an image on GPIO using fbi (framebuffer imageviewer)
"""

import os
import subprocess
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_fbi_display():
    """Test using fbi to display QR code"""
    
    qr_file = Path("whatsapp_qr_headless.png")
    
    if not qr_file.exists():
        logger.error(f"QR file not found: {qr_file}")
        return False
    
    try:
        # Try using fbi (framebuffer imageviewer)
        logger.info("Testing fbi framebuffer display...")
        
        # Kill any existing fbi processes
        subprocess.run(["sudo", "pkill", "-f", "fbi"], capture_output=True)
        
        # Display image using fbi in background
        cmd = [
            "sudo", "fbi", 
            "-d", "/dev/fb0",  # Framebuffer device
            "-T", "1",         # Use terminal 1 
            "--noverbose",     # Quiet mode
            "-a",              # Autozoom to fit screen
            str(qr_file)
        ]
        
        logger.info(f"Running: {' '.join(cmd)}")
        
        # Start fbi in background
        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        # Wait a moment to see if it starts successfully
        import time
        time.sleep(2)
        
        # Check if process is still running
        if process.poll() is None:
            logger.info("✅ fbi started successfully - QR should be visible")
            logger.info("📱 Please scan the QR code with WhatsApp")
            logger.info("⏰ Will display for 60 seconds...")
            
            # Wait 60 seconds then kill
            time.sleep(60)
            process.terminate()
            time.sleep(1)
            subprocess.run(["sudo", "pkill", "-f", "fbi"], capture_output=True)
            
            logger.info("🔲 Display cleared")
            return True
        else:
            stdout, stderr = process.communicate()
            logger.error(f"fbi failed: {stderr.decode()}")
            return False
            
    except Exception as e:
        logger.error(f"Error with fbi: {e}")
        return False

def test_fim_display():
    """Test using fim (another framebuffer imageviewer)"""
    
    qr_file = Path("whatsapp_qr_headless.png")
    
    try:
        logger.info("Testing fim framebuffer display...")
        
        cmd = [
            "sudo", "fim",
            "-T", "/dev/fb0",  # Framebuffer device
            "-q",              # Quiet
            "-a",              # Autoscale
            str(qr_file)
        ]
        
        logger.info(f"Running: {' '.join(cmd)}")
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
        
        if result.returncode == 0:
            logger.info("✅ fim displayed image successfully")
            return True
        else:
            logger.error(f"fim failed: {result.stderr}")
            return False
            
    except subprocess.TimeoutExpired:
        logger.info("⏰ fim timed out (image may be showing)")
        return True
    except Exception as e:
        logger.error(f"Error with fim: {e}")
        return False

def main():
    logger.info("🖥️ Testing framebuffer image display tools")
    logger.info("=" * 50)
    
    # Check if image exists
    qr_file = Path("whatsapp_qr_headless.png")
    if not qr_file.exists():
        logger.error("❌ QR code image not found")
        logger.info("💡 Generate it first: python whatsapp_playwright_sender.py")
        return
    
    # Test fbi first
    if test_fbi_display():
        logger.info("✅ fbi test completed")
    else:
        logger.info("❌ fbi test failed")
        
        # Try fim as backup
        if test_fim_display():
            logger.info("✅ fim test completed")
        else:
            logger.info("❌ Both fbi and fim failed")
            logger.info("💡 Your display may not support these tools")

if __name__ == "__main__":
    main()