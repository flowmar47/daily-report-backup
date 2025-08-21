#!/usr/bin/env python3
"""
Send test message to your phone number so you can forward to group manually
"""

import os
import pywhatkit as kit
import time

# Set display for VNC
os.environ['DISPLAY'] = ':1'

def send_to_phone():
    """Send test message to phone for manual forwarding"""
    print("=" * 60)
    print("SENDING TO PHONE FOR MANUAL FORWARDING")
    print("=" * 60)
    
    phone = "+19093746793"
    
    message = f"""WhatsApp Group Test - {time.strftime('%Y-%m-%d %H:%M:%S')}

PLEASE FORWARD THIS TO THE OHMS ALERTS REPORTS GROUP

This is a test of the daily financial report format:

FOREX PAIRS

Pair: EURUSD
High: 1.0875
Average: 1.0775
Low: 1.0675
MT4 Action: MT4 BUY
Exit: 1.0825

EQUITIES AND OPTIONS

Symbol: SPY
52 Week High: 489.50
52 Week Low: 484.25
Strike Price:

CALL > 495.00

PUT < 480.00
Status: TRADE IN PROFIT

If you receive this message, please:
1. Forward it to the "Ohms Alerts Reports" WhatsApp group
2. This will confirm the message format works
3. We can then troubleshoot the direct group messaging

The system is ready for Monday 6 AM PST with all three platforms."""
    
    try:
        print(f"Sending test message to {phone}...")
        print("You can then forward this to the group manually...")
        
        # Send to phone number
        kit.sendwhatmsg_instantly(
            phone,
            message,
            wait_time=15,
            tab_close=True,
            close_time=3
        )
        
        print("Message sent to your phone!")
        print("Please forward it to the WhatsApp group to test the format.")
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    send_to_phone()