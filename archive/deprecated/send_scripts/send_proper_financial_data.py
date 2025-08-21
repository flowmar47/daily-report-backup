#!/usr/bin/env python3
"""
Send ONLY financial data to Signal/Telegram + fresh heatmaps
No status messages, just clean financial alerts
"""

import asyncio
import os
import sys
import logging
import re
from datetime import datetime
from pathlib import Path

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def parse_clean_financial_data():
    """Parse MyMama data into clean financial format only"""
    
    # Use the latest successful scrape
    data_file = "/home/ohms/OhmsAlertsReports/daily-report/real_alerts_only/essentials_text_20250703_103513.txt"
    
    if not os.path.exists(data_file):
        logger.error(f"Data file not found: {data_file}")
        return None
    
    with open(data_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Parse forex pairs
    forex_pairs = {}
    lines = content.split('\n')
    i = 0
    
    while i < len(lines):
        line = lines[i].strip()
        line_upper = line.upper()
        
        # Look for forex pairs
        if line_upper in ['EURUSD', 'GBPUSD', 'USDJPY', 'USDCHF', 'USDCAD', 'AUDUSD']:
            pair_name = line_upper
            pair_data = {'pair': pair_name}
            
            # Look ahead for data
            j = i + 1
            while j < len(lines) and j < i + 15:
                next_line = lines[j].strip()
                next_upper = next_line.upper()
                
                # Stop if we hit another forex pair
                if next_upper in ['EURUSD', 'GBPUSD', 'USDJPY', 'USDCHF', 'USDCAD', 'AUDUSD']:
                    break
                
                # Extract data
                high_match = re.search(r'HIGH:\s*([\d.]+)', next_upper)
                if high_match:
                    pair_data['high'] = high_match.group(1)
                
                avg_match = re.search(r'AVERAGE:\s*([\d.]+)', next_upper)
                if avg_match:
                    pair_data['average'] = avg_match.group(1)
                
                low_match = re.search(r'LOW:\s*([\d.]+)', next_upper)
                if low_match:
                    pair_data['low'] = low_match.group(1)
                
                # Extract MT4 Action
                if 'MT4' in next_upper and ('BUY' in next_upper or 'SELL' in next_upper):
                    if 'SELL' in next_upper:
                        pair_data['mt4_action'] = 'MT4 SELL'
                        sell_match = re.search(r'SELL\s*>\s*([\d.]+)', next_line)
                        if sell_match:
                            pair_data['entry'] = sell_match.group(1)
                    elif 'BUY' in next_upper:
                        pair_data['mt4_action'] = 'MT4 BUY'
                        buy_match = re.search(r'BUY\s*<\s*([\d.]+)', next_line)
                        if buy_match:
                            pair_data['entry'] = buy_match.group(1)
                
                # Extract EXIT
                exit_match = re.search(r'EXIT:?\s*([\d.]+|TBD)', next_line)
                if exit_match:
                    pair_data['exit'] = exit_match.group(1)
                
                j += 1
            
            if len(pair_data) > 1:
                forex_pairs[pair_name] = pair_data
            
            i = j - 1
        
        i += 1
    
    # Create CLEAN financial message (no status, no emojis)
    output_lines = []
    
    if forex_pairs:
        output_lines.append("FOREX PAIRS")
        output_lines.append("")
        
        for pair_name, pair_data in forex_pairs.items():
            output_lines.append(f"Pair: {pair_name}")
            if 'high' in pair_data:
                output_lines.append(f"High: {pair_data['high']}")
            if 'average' in pair_data:
                output_lines.append(f"Average: {pair_data['average']}")
            if 'low' in pair_data:
                output_lines.append(f"Low: {pair_data['low']}")
            if 'mt4_action' in pair_data:
                output_lines.append(f"MT4 Action: {pair_data['mt4_action']}")
            if 'exit' in pair_data:
                output_lines.append(f"Exit: {pair_data['exit']}")
            output_lines.append("")
    
    # Add timestamp at end only
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    output_lines.append(f"Generated: {timestamp}")
    
    return '\n'.join(output_lines)

async def send_clean_financial_data():
    """Send ONLY clean financial data to Signal/Telegram"""
    try:
        # Parse clean data
        message = parse_clean_financial_data()
        
        if not message:
            logger.error("Failed to parse financial data")
            return False
        
        logger.info("Parsed clean financial data successfully")
        
        # Import unified messenger
        sys.path.append(os.path.dirname(os.path.abspath(__file__)))
        from src.messengers.unified_messenger import UnifiedMultiMessenger
        
        # Initialize ONLY Signal and Telegram (no WhatsApp status)
        platforms = ['telegram', 'signal']
        multi_messenger = UnifiedMultiMessenger(platforms)
        
        logger.info("Sending clean financial data...")
        
        # Send clean message
        results = await multi_messenger.send_structured_financial_data(message)
        
        # Check results
        success_count = 0
        for platform, result in results.items():
            if result.success:
                logger.info(f"Financial data sent to {platform.upper()}")
                success_count += 1
            else:
                logger.error(f"{platform.upper()} failed: {result.error}")
        
        # Cleanup
        await multi_messenger.cleanup()
        
        return success_count > 0
        
    except Exception as e:
        logger.error(f"Error sending financial data: {e}")
        import traceback
        traceback.print_exc()
        return False

def send_heatmaps_via_signal():
    """Send heatmaps via Signal CLI directly"""
    try:
        signal_group_id = os.getenv('SIGNAL_GROUP_ID')
        if not signal_group_id:
            logger.error("Signal group ID not found in .env")
            return False
        
        heatmap_files = [
            "/home/ohms/OhmsAlertsReports/daily-report/categorical_heatmap_20250703_102238.png",
            "/home/ohms/OhmsAlertsReports/daily-report/forex_pairs_20250703_102238.png"
        ]
        
        success_count = 0
        
        for heatmap_path in heatmap_files:
            if os.path.exists(heatmap_path):
                heatmap_name = os.path.basename(heatmap_path)
                
                # Send via Signal CLI directly
                cmd = f'curl -X POST http://localhost:8080/v2/send -H "Content-Type: application/json" -d \'{{"message": "Financial Heatmap: {heatmap_name}", "number": "{signal_group_id}", "recipients": ["{signal_group_id}"], "base64_attachments": ["{get_base64_image(heatmap_path)}"]}}\''
                
                result = os.system(cmd)
                if result == 0:
                    logger.info(f"Heatmap sent via Signal: {heatmap_name}")
                    success_count += 1
                else:
                    logger.error(f"Failed to send heatmap via Signal: {heatmap_name}")
        
        return success_count > 0
        
    except Exception as e:
        logger.error(f"Error sending heatmaps: {e}")
        return False

def get_base64_image(image_path):
    """Convert image to base64 for Signal"""
    import base64
    
    try:
        with open(image_path, 'rb') as f:
            image_data = f.read()
        
        return base64.b64encode(image_data).decode('utf-8')
        
    except Exception as e:
        logger.error(f"Error converting image to base64: {e}")
        return ""

async def send_heatmaps_via_telegram():
    """Send heatmaps via Telegram"""
    try:
        import httpx
        
        bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
        chat_id = os.getenv('TELEGRAM_GROUP_ID')
        
        if not bot_token or not chat_id:
            logger.error("Telegram credentials not found")
            return False
        
        heatmap_files = [
            "/home/ohms/OhmsAlertsReports/daily-report/categorical_heatmap_20250703_102238.png",
            "/home/ohms/OhmsAlertsReports/daily-report/forex_pairs_20250703_102238.png"
        ]
        
        success_count = 0
        
        async with httpx.AsyncClient() as client:
            for heatmap_path in heatmap_files:
                if os.path.exists(heatmap_path):
                    heatmap_name = os.path.basename(heatmap_path)
                    
                    url = f"https://api.telegram.org/bot{bot_token}/sendPhoto"
                    
                    with open(heatmap_path, 'rb') as f:
                        files = {'photo': f}
                        data = {
                            'chat_id': chat_id,
                            'caption': f'Financial Heatmap: {heatmap_name}'
                        }
                        
                        response = await client.post(url, files=files, data=data)
                        
                        if response.status_code == 200:
                            logger.info(f"Heatmap sent via Telegram: {heatmap_name}")
                            success_count += 1
                        else:
                            logger.error(f"Failed to send heatmap via Telegram: {response.text}")
        
        return success_count > 0
        
    except Exception as e:
        logger.error(f"Error sending heatmaps via Telegram: {e}")
        return False

async def main():
    """Main function - send clean financial data + heatmaps"""
    logger.info("Sending clean financial data and fresh heatmaps...")
    
    # Send clean financial data (no status messages)
    financial_success = await send_clean_financial_data()
    
    # Send heatmaps separately
    logger.info("Sending fresh heatmaps...")
    telegram_heatmaps = await send_heatmaps_via_telegram()
    signal_heatmaps = send_heatmaps_via_signal()
    
    # Summary
    logger.info("=" * 50)
    logger.info("CLEAN DELIVERY SUMMARY:")
    logger.info(f"Financial Data: {'SUCCESS' if financial_success else 'FAILED'}")
    logger.info(f"Telegram Heatmaps: {'SUCCESS' if telegram_heatmaps else 'FAILED'}")
    logger.info(f"Signal Heatmaps: {'SUCCESS' if signal_heatmaps else 'FAILED'}")
    
    if financial_success:
        print("\nCLEAN financial data sent successfully!")
        print("No status messages - only forex alerts")
        if telegram_heatmaps or signal_heatmaps:
            print("Fresh heatmaps delivered!")
        
    return financial_success

if __name__ == "__main__":
    asyncio.run(main())