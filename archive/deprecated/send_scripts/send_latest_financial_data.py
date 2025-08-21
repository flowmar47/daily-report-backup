#!/usr/bin/env python3
"""
Send Latest Financial Data from Enhanced Scraper
Sends the most recent financial alerts to both Telegram and Signal
"""

import asyncio
import json
import logging
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.messengers.unified_messenger import UnifiedMultiMessenger
from src.data_processors.financial_alerts import FinancialAlertsProcessor

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def send_latest_financial_data():
    """Send the latest financial data to both messengers"""
    try:
        logger.info("🚀 Sending latest financial data from enhanced scraper...")
        
        # Find the latest data file
        output_dir = Path('output/enhanced_browserbase')
        if not output_dir.exists():
            logger.error("❌ No enhanced browserbase output directory found")
            return False
        
        # Get the most recent file
        data_files = list(output_dir.glob('enhanced_browserbase_data_*.json'))
        if not data_files:
            logger.error("❌ No data files found")
            return False
        
        latest_file = max(data_files, key=lambda f: f.stat().st_mtime)
        logger.info(f"📁 Using latest data file: {latest_file.name}")
        
        # Load the data
        with open(latest_file, 'r') as f:
            data = json.load(f)
        
        # Extract the processed data
        processed_data = data.get('data', {})
        
        # Check if we have real data
        if not processed_data.get('has_real_data', False):
            logger.warning("⚠️ No real data found in latest file")
            return False
        
        # Format the financial report
        report = format_financial_report(processed_data)
        
        # Initialize messengers
        messenger = UnifiedMultiMessenger()
        
        # Send to both messengers
        logger.info("📤 Sending to both messengers...")
        results = await messenger.send_to_all(report)
        
        # Check results
        telegram_result = results.get('telegram')
        signal_result = results.get('signal')
        telegram_success = telegram_result.success if telegram_result else False
        signal_success = signal_result.success if signal_result else False
        
        # Summary
        logger.info("==================================================")
        logger.info("📋 FINANCIAL DATA DELIVERY SUMMARY")
        logger.info("==================================================")
        logger.info(f"📊 Data Source: {processed_data.get('source', 'Unknown')}")
        logger.info(f"📈 Forex Alerts: {len(processed_data.get('forex_alerts', []))}")
        logger.info(f"📊 Options Alerts: {len(processed_data.get('options_alerts', []))}")
        logger.info(f"🔄 Swing Trades: {len(processed_data.get('swing_trades', []))}")
        logger.info(f"📈 Day Trades: {len(processed_data.get('day_trades', []))}")
        logger.info(f"📝 Report Length: {len(report)} characters")
        logger.info(f"📱 Telegram: {'✅ Success' if telegram_success else '❌ Failed'}")
        logger.info(f"📡 Signal: {'✅ Success' if signal_success else '❌ Failed'}")
        logger.info(f"🎯 Overall: {'✅ Success' if telegram_success and signal_success else '⚠️ Partial'}")
        logger.info("==================================================")
        
        return telegram_success and signal_success
        
    except Exception as e:
        logger.error(f"❌ Failed to send financial data: {e}")
        import traceback
        traceback.print_exc()
        return False

def format_financial_report(data: Dict[str, Any]) -> str:
    """Format the financial data into a readable report matching the exact format"""
    try:
        report_lines = []
        report_lines.append(f"Generated on: {datetime.now().strftime('%B %d, %Y')}")
        
        # Forex Alerts
        forex_alerts = data.get('forex_alerts', [])
        if forex_alerts:
            report_lines.append("FOREX ALERTS PREMIUM")
            for alert in forex_alerts:
                pair = alert.get('pair', 'N/A')
                high = alert.get('high', 'N/A')
                average = alert.get('average', 'N/A')
                low = alert.get('low', 'N/A')
                mt4_action = alert.get('mt4_action', 'N/A')
                exit_price = alert.get('exit_price', 'N/A')
                status = alert.get('trade_status', 'N/A')
                average_pips = alert.get('average_pips', 'N/A')
                notes = alert.get('notes', '')
                
                report_lines.append(f"{pair}")
                report_lines.append("")
                report_lines.append(f"    HIGH: {high}")
                report_lines.append(f"    AVERAGE: {average}")
                report_lines.append(f"    LOW: {low}")
                if mt4_action != 'N/A':
                    report_lines.append(f"    MT4 ACTION: {mt4_action}")
                if exit_price != 'N/A':
                    report_lines.append(f"    EXIT: {exit_price}")
                if status != 'N/A':
                    report_lines.append(f"    STATUS: {status}")
                if average_pips != 'N/A':
                    report_lines.append(f"    14 DAY AVERAGE: {average_pips} PIPS")
                if notes:
                    report_lines.append(f"    NOTE: {notes}")
                report_lines.append("")
        
        # Swing Trades
        swing_trades = data.get('swing_trades', [])
        if swing_trades:
            report_lines.append("PREMIUM SWING TRADES")
            report_lines.append("")
            report_lines.append("Monday - Wednesday")
            for trade in swing_trades:
                symbol = trade.get('symbol', 'N/A')
                earnings_date = trade.get('earnings_date', 'N/A')
                strategy = trade.get('strategy', 'N/A')
                notes = trade.get('notes', '')
                
                report_lines.append(f"{symbol} – {symbol}")
                report_lines.append("")
                if earnings_date != 'N/A':
                    report_lines.append(f"    EARNINGS DATE: {earnings_date}")
                if strategy != 'N/A':
                    report_lines.append(f"    ANALYSIS: {strategy}")
                if notes:
                    report_lines.append(f"    STRATEGY: {notes}")
                report_lines.append("")
        
        # Day Trades
        day_trades = data.get('day_trades', [])
        if day_trades:
            report_lines.append("PREMIUM DAY TRADES")
            report_lines.append("")
            report_lines.append("Monday - Wednesday")
            for trade in day_trades:
                symbol = trade.get('symbol', 'N/A')
                strategy = trade.get('strategy', 'N/A')
                notes = trade.get('notes', '')
                
                report_lines.append(f"{symbol} – {symbol}")
                report_lines.append("")
                if strategy != 'N/A':
                    report_lines.append(f"    WHY DAY TRADE: {strategy}")
                if notes:
                    report_lines.append(f"    {notes}")
                report_lines.append("")
        
        # Options Alerts
        options_alerts = data.get('options_alerts', [])
        if options_alerts:
            report_lines.append("OPTIONS ALERTS PREMIUM")
            for alert in options_alerts:
                symbol = alert.get('symbol', 'N/A')
                week_high = alert.get('week_high', 'N/A')
                week_low = alert.get('week_low', 'N/A')
                call_strike = alert.get('call_strike', 'N/A')
                put_strike = alert.get('put_strike', 'N/A')
                status = alert.get('trade_status', 'N/A')
                
                report_lines.append(f"{symbol}")
                report_lines.append("")
                if week_high != 'N/A':
                    report_lines.append(f"    52 WEEK HIGH: {week_high}")
                if week_low != 'N/A':
                    report_lines.append(f"    52 WEEK LOW: {week_low}")
                if call_strike != 'N/A':
                    report_lines.append(f"    CALL STRIKE: {call_strike}")
                if put_strike != 'N/A':
                    report_lines.append(f"    PUT STRIKE: {put_strike}")
                if status != 'N/A':
                    report_lines.append(f"    STATUS: {status}")
                report_lines.append("")
        
        return "\n".join(report_lines)
        
    except Exception as e:
        logger.error(f"❌ Error formatting report: {e}")
        return "❌ Error formatting financial report"

async def main():
    """Main function"""
    success = await send_latest_financial_data()
    if success:
        logger.info("✅ Financial data sent successfully!")
    else:
        logger.error("❌ Failed to send financial data")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main()) 