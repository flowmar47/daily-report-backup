#!/usr/bin/env python3
"""
Simple Data Resend - Fix Unicode and resend today's data
"""

import json
import asyncio
import requests
import logging
from datetime import datetime

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Environment variables
TELEGRAM_BOT_TOKEN = "7695859844:AAE_PxUOckN57S5eGyFKVW4fp4pReR0zzMI"
TELEGRAM_GROUP_ID = "-1002548864790"

def clean_unicode_for_telegram(text):
    """Clean Unicode characters that cause Telegram 400 errors"""
    if not text:
        return ""
    
    # Fix specific Unicode issues found in financial data
    cleaned = text
    cleaned = cleaned.replace('\u202f', ' ')  # Narrow no-break space -> regular space
    cleaned = cleaned.replace('\u200b', '')   # Zero-width space -> remove
    cleaned = cleaned.replace('\u2013', '-')  # En dash -> regular hyphen
    cleaned = cleaned.replace('\u2014', '-')  # Em dash -> regular hyphen
    cleaned = cleaned.replace('\u2018', "'")  # Left single quote -> apostrophe
    cleaned = cleaned.replace('\u2019', "'")  # Right single quote -> apostrophe
    cleaned = cleaned.replace('\u201c', '"')  # Left double quote -> regular quote
    cleaned = cleaned.replace('\u201d', '"')  # Right double quote -> regular quote
    cleaned = cleaned.replace('\u00a0', ' ')  # Non-breaking space -> regular space
    
    return cleaned

def format_forex_data(forex_alerts):
    """Format forex data into structured plaintext"""
    if not forex_alerts:
        return ""
    
    lines = ["FOREX PAIRS", ""]
    
    for pair, data in forex_alerts.items():
        lines.extend([
            f"Pair: {pair}",
            f"High: {data.get('high', 'N/A')}",
            f"Average: {data.get('average', 'N/A')}",
            f"Low: {data.get('low', 'N/A')}",
            f"MT4 Action: MT4 {data.get('signal', 'N/A')}",
            f"Exit: {data.get('exit', 'N/A')}",
            ""
        ])
    
    return "\n".join(lines)

def format_options_data(options_data):
    """Format options data into structured plaintext"""
    if not options_data:
        return ""
    
    lines = ["EQUITIES AND OPTIONS", ""]
    
    for option in options_data:
        lines.extend([
            f"Symbol: {option.get('ticker', 'N/A')}",
            f"52 Week High: {option.get('high_52week', 'N/A')}",
            f"52 Week Low: {option.get('low_52week', 'N/A')}",
            "Strike Price:",
            "",
            f"CALL > {option.get('call_strike', 'N/A')}",
            "",
            f"PUT < {option.get('put_strike', 'N/A')}",
            f"Status: {option.get('status', 'N/A')}",
            ""
        ])
    
    return "\n".join(lines)

def format_swing_trades(swing_trades):
    """Format swing trades into structured plaintext"""
    if not swing_trades:
        return ""
    
    lines = ["PREMIUM SWING TRADES (Monday - Wednesday)", ""]
    
    for trade in swing_trades:
        company = trade.get('company', 'N/A')
        ticker = trade.get('ticker', 'N/A')
        earnings_date = trade.get('earnings_date', 'N/A')
        
        lines.extend([
            f"{company} ({ticker})",
            f"Earnings Report: {earnings_date}",
            f"Current Price: N/A",
            f"Rationale: {trade.get('analysis', 'N/A')[:200]}...",
            ""
        ])
    
    return "\n".join(lines)

def format_day_trades(day_trades):
    """Format day trades into structured plaintext"""
    if not day_trades:
        return ""
    
    lines = ["PREMIUM DAY TRADES", ""]
    
    for trade in day_trades:
        company = trade.get('company', 'N/A')
        ticker = trade.get('ticker', 'N/A')
        
        lines.extend([
            f"{company} ({ticker})",
            f"Strategy: {trade.get('analysis', 'N/A')[:200]}...",
            ""
        ])
    
    return "\n".join(lines)

async def send_to_telegram(message):
    """Send message to Telegram with proper error handling"""
    try:
        # Clean Unicode issues
        cleaned_message = clean_unicode_for_telegram(message)
        
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        payload = {
            'chat_id': TELEGRAM_GROUP_ID,
            'text': cleaned_message,
            'parse_mode': 'Markdown'
        }
        
        response = requests.post(url, json=payload, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            if result.get('ok'):
                logger.info(f"✅ TELEGRAM: Message sent successfully (ID: {result['result']['message_id']})")
                return True
            else:
                logger.error(f"❌ TELEGRAM: API returned not ok: {result.get('description', 'Unknown error')}")
                return False
        else:
            logger.error(f"❌ TELEGRAM: HTTP {response.status_code}: {response.text}")
            return False
            
    except Exception as e:
        logger.error(f"❌ TELEGRAM: Exception - {e}")
        return False

async def send_to_signal(message):
    """Send message to Signal CLI using curl"""
    try:
        import subprocess
        import json as json_module
        
        # Clean Unicode issues
        cleaned_message = clean_unicode_for_telegram(message)
        
        payload = {
            'number': '+16572463906',
            'recipients': ['group.ZmFLQ25IUTBKbWpuNFdpaDdXTjVoVXpYOFZtNGVZZ1lYRGdwMWpMcW0zMD0='],
            'message': cleaned_message
        }
        
        # Use curl to send the request
        cmd = [
            'curl', '-X', 'POST',
            'http://localhost:8080/v2/send',
            '-H', 'Content-Type: application/json',
            '-d', json_module.dumps(payload),
            '--max-time', '30'
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=35)
        
        if result.returncode == 0:
            logger.info(f"✅ SIGNAL: Message sent successfully")
            return True
        else:
            logger.error(f"❌ SIGNAL: curl failed with code {result.returncode}: {result.stderr}")
            return False
            
    except Exception as e:
        logger.error(f"❌ SIGNAL: Exception - {e}")
        return False

def load_financial_data():
    """Load today's financial data"""
    try:
        data_file = 'real_alerts_only/real_alerts_20250702_060141.json'
        with open(data_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        logger.info(f"✅ Loaded financial data from {data_file}")
        return data
        
    except Exception as e:
        logger.error(f"❌ Failed to load data: {e}")
        return None

async def main():
    """Main resend function"""
    logger.info("=" * 60)
    logger.info("EMERGENCY RESEND - Fixing Telegram Unicode Issues")
    logger.info("=" * 60)
    
    # Load data
    data = load_financial_data()
    if not data:
        logger.error("❌ Cannot proceed without data")
        return
    
    # Format the report
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M PST")
    
    report_parts = [
        f"DAILY FINANCIAL ALERTS - {timestamp}",
        "",
        format_forex_data(data.get('forex_alerts', {})),
        format_options_data(data.get('options_data', [])),
        format_swing_trades(data.get('swing_trades', [])),
        format_day_trades(data.get('day_trades', [])),
        "=" * 50
    ]
    
    full_report = "\n".join(filter(None, report_parts))
    
    logger.info(f"📝 Generated report: {len(full_report)} characters")
    
    # Send to both platforms
    telegram_success = await send_to_telegram(full_report)
    signal_success = await send_to_signal(full_report)
    
    # Summary
    success_count = sum([telegram_success, signal_success])
    logger.info(f"📊 DELIVERY SUMMARY: {success_count}/2 platforms successful")
    
    if success_count == 2:
        logger.info("✅ Emergency resend completed successfully!")
    else:
        logger.warning("⚠️ Partial success - check individual platform logs")

if __name__ == "__main__":
    asyncio.run(main())