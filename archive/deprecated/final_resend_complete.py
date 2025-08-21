#!/usr/bin/env python3
"""
Final Complete Resend - No Dependencies
Send today's financial data and heatmaps without dependency issues
"""

import json
import subprocess
import requests
import logging
from datetime import datetime
from pathlib import Path

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Configuration
TELEGRAM_BOT_TOKEN = "7695859844:AAE_PxUOckN57S5eGyFKVW4fp4pReR0zzMI"
TELEGRAM_GROUP_ID = "-1002548864790"
SIGNAL_PHONE = "+16572463906"
SIGNAL_GROUP = "group.ZmFLQ25IUTBKbWpuNFdpaDdXTjVoVXpYOFZtNGVZZ1lYRGdwMWpMcW0zMD0="

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

def format_complete_financial_report(data):
    """Format complete financial report from JSON data"""
    try:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M PST")
        
        # Header
        report = f"DAILY FINANCIAL ALERTS - {timestamp}\n\n"
        
        # Forex Section
        forex_alerts = data.get('forex_alerts', {})
        if forex_alerts:
            report += "FOREX PAIRS\n\n"
            for pair, forex_data in forex_alerts.items():
                report += f"Pair: {pair}\n"
                report += f"High: {forex_data.get('high', 'N/A')}\n"
                report += f"Average: {forex_data.get('average', 'N/A')}\n"
                report += f"Low: {forex_data.get('low', 'N/A')}\n"
                report += f"MT4 Action: MT4 {forex_data.get('signal', 'N/A')}\n"
                report += f"Exit: {forex_data.get('exit', 'N/A')}\n\n"
        
        # Options Section
        options_data = data.get('options_data', [])
        if options_data:
            report += "EQUITIES AND OPTIONS\n\n"
            for option in options_data:
                report += f"Symbol: {option.get('ticker', 'N/A')}\n"
                report += f"52 Week High: {option.get('high_52week', 'N/A')}\n"
                report += f"52 Week Low: {option.get('low_52week', 'N/A')}\n"
                report += "Strike Price:\n\n"
                report += f"CALL > {option.get('call_strike', 'N/A')}\n\n"
                report += f"PUT < {option.get('put_strike', 'N/A')}\n"
                report += f"Status: {option.get('status', 'N/A')}\n\n"
        
        # Swing Trades Section
        swing_trades = data.get('swing_trades', [])
        if swing_trades:
            report += "PREMIUM SWING TRADES (Monday - Wednesday)\n\n"
            for trade in swing_trades:
                company = trade.get('company', 'N/A')
                ticker = trade.get('ticker', 'N/A')
                earnings_date = clean_unicode_for_telegram(trade.get('earnings_date', 'N/A'))
                analysis = clean_unicode_for_telegram(trade.get('analysis', 'N/A')[:200])
                
                report += f"{company} ({ticker})\n"
                report += f"Earnings Report: {earnings_date}\n"
                report += f"Current Price: N/A\n"
                report += f"Rationale: {analysis}...\n\n"
        
        # Day Trades Section
        day_trades = data.get('day_trades', [])
        if day_trades:
            report += "PREMIUM DAY TRADES\n\n"
            for trade in day_trades:
                company = trade.get('company', 'N/A')
                ticker = trade.get('ticker', 'N/A')
                analysis = clean_unicode_for_telegram(trade.get('analysis', 'N/A')[:200])
                
                report += f"{company} ({ticker})\n"
                report += f"Strategy: {analysis}...\n\n"
        
        # Footer
        report += "=" * 50
        
        return clean_unicode_for_telegram(report)
        
    except Exception as e:
        logger.error(f"❌ Error formatting report: {e}")
        return None

def send_to_telegram(message):
    """Send message to Telegram"""
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        payload = {
            'chat_id': TELEGRAM_GROUP_ID,
            'text': message
        }
        
        response = requests.post(url, json=payload, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            if result.get('ok'):
                logger.info(f"✅ TELEGRAM: Message sent successfully (ID: {result['result']['message_id']})")
                return True
            else:
                logger.error(f"❌ TELEGRAM: API error - {result.get('description')}")
                return False
        else:
            logger.error(f"❌ TELEGRAM: HTTP {response.status_code}: {response.text}")
            return False
            
    except Exception as e:
        logger.error(f"❌ TELEGRAM: Exception - {e}")
        return False

def send_to_signal(message):
    """Send message to Signal"""
    try:
        payload = {
            'number': SIGNAL_PHONE,
            'recipients': [SIGNAL_GROUP],
            'message': message
        }
        
        cmd = [
            'curl', '-X', 'POST', 'http://localhost:8080/v2/send',
            '-H', 'Content-Type: application/json',
            '-d', json.dumps(payload),
            '--max-time', '30'
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=35)
        
        if result.returncode == 0:
            logger.info(f"✅ SIGNAL: Message sent successfully")
            return True
        else:
            logger.error(f"❌ SIGNAL: Failed - {result.stderr}")
            return False
            
    except Exception as e:
        logger.error(f"❌ SIGNAL: Exception - {e}")
        return False

def send_heatmap_to_telegram(image_path, caption):
    """Send heatmap to Telegram"""
    try:
        if not image_path.exists():
            logger.warning(f"⚠️ Heatmap not found: {image_path}")
            return False
            
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendPhoto"
        
        with open(image_path, 'rb') as image_file:
            files = {'photo': image_file}
            data = {
                'chat_id': TELEGRAM_GROUP_ID,
                'caption': caption
            }
            
            response = requests.post(url, data=data, files=files, timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                if result.get('ok'):
                    logger.info(f"✅ TELEGRAM: Heatmap sent successfully ({image_path.name})")
                    return True
                else:
                    logger.error(f"❌ TELEGRAM: Heatmap API error - {result.get('description')}")
                    return False
            else:
                logger.error(f"❌ TELEGRAM: Heatmap HTTP {response.status_code}")
                return False
                
    except Exception as e:
        logger.error(f"❌ TELEGRAM: Heatmap exception - {e}")
        return False

def main():
    """Complete resend workflow"""
    logger.info("=" * 70)
    logger.info("FINAL COMPLETE RESEND - Financial Data + Heatmaps")
    logger.info("=" * 70)
    
    # Load today's financial data
    try:
        data_file = Path('real_alerts_only/real_alerts_20250702_060141.json')
        with open(data_file, 'r', encoding='utf-8') as f:
            financial_data = json.load(f)
        logger.info(f"✅ Loaded financial data from {data_file}")
    except Exception as e:
        logger.error(f"❌ Failed to load financial data: {e}")
        return
    
    # Format complete report
    complete_report = format_complete_financial_report(financial_data)
    if not complete_report:
        logger.error("❌ Failed to format financial report")
        return
    
    logger.info(f"📝 Generated complete report: {len(complete_report)} characters")
    
    # Send financial data to both platforms
    telegram_success = send_to_telegram(complete_report)
    signal_success = send_to_signal(complete_report)
    
    # Find and send most recent heatmaps
    heatmap_dir = Path("../heatmaps_package/core_files")
    
    # Look for recent heatmap files in all subdirectories
    categorical_files = list(heatmap_dir.rglob("*categorical*.png"))
    forex_files = list(heatmap_dir.rglob("*forex*.png"))
    
    heatmap_success = False
    if categorical_files or forex_files:
        # Sort by modification time
        if categorical_files:
            categorical_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
            latest_categorical = categorical_files[0]
            
            success = send_heatmap_to_telegram(
                latest_categorical, 
                f"📊 Interest Rate Categorical Analysis - {datetime.now().strftime('%Y-%m-%d %H:%M PST')}"
            )
            if success:
                heatmap_success = True
        
        if forex_files:
            forex_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
            latest_forex = forex_files[0]
            
            success = send_heatmap_to_telegram(
                latest_forex, 
                f"📊 Forex Pairs Differential Matrix - {datetime.now().strftime('%Y-%m-%d %H:%M PST')}"
            )
            if success:
                heatmap_success = True
    else:
        logger.warning("⚠️ No heatmap files found")
    
    # Send heatmap notification to Signal
    if heatmap_success:
        send_to_signal(f"📊 Interest Rate Heatmaps sent via Telegram - {datetime.now().strftime('%Y-%m-%d %H:%M PST')}")
    
    # Final summary
    total_success = sum([telegram_success, signal_success, heatmap_success])
    logger.info(f"📊 FINAL DELIVERY SUMMARY:")
    logger.info(f"  ✅ Telegram Financial Data: {'SUCCESS' if telegram_success else 'FAILED'}")
    logger.info(f"  ✅ Signal Financial Data: {'SUCCESS' if signal_success else 'FAILED'}")
    logger.info(f"  ✅ Heatmap Images: {'SUCCESS' if heatmap_success else 'FAILED'}")
    logger.info(f"  📈 Overall: {total_success}/3 components successful")
    
    if total_success >= 2:
        logger.info("✅ MISSION ACCOMPLISHED - Today's data successfully delivered!")
    else:
        logger.warning("⚠️ Partial success - some components failed")

if __name__ == "__main__":
    main()