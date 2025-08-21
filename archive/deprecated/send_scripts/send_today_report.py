#!/usr/bin/env python3
import asyncio
import sys
import os
from datetime import datetime
sys.path.append('.')

from real_only_mymama_scraper import RealOnlyMyMamaScraper
from src.messengers.unified_messenger import send_to_both_messengers

async def send_now():
    print('🚀 Extracting MyMama data...')
    scraper = RealOnlyMyMamaScraper()
    alerts = await scraper.get_real_alerts_only()
    
    if not alerts:
        print('❌ No alerts found')
        return
        
    print('✅ Found alerts, generating structured message...')
    
    # Generate today's date
    today_date = datetime.now().strftime('%B %d, %Y')
    
    # Create a proper structured message
    message = f'Generated on: {today_date}\nFOREX ALERTS PREMIUM\n\n'
    
    # Process forex alerts (they are in a dict format)
    if alerts.get('forex_alerts'):
        for pair, forex_data in alerts['forex_alerts'].items():
            message += f'{pair}\n\n'
            message += f'    HIGH: {forex_data.get("high", "N/A")}\n'
            message += f'    AVERAGE: {forex_data.get("average", "N/A")}\n' 
            message += f'    LOW: {forex_data.get("low", "N/A")}\n'
            message += f'    MT4 ACTION: {forex_data.get("signal", "N/A")} > {forex_data.get("entry", "")}\n'
            message += f'    EXIT: {forex_data.get("exit", "N/A")}\n'
            message += f'    STATUS: TRADE IN PROFIT\n\n'
    
    # Process swing trades
    if alerts.get('swing_trades'):
        message += '\nPREMIUM SWING TRADES\n\nMonday - Wednesday\n'
        for trade in alerts['swing_trades']:
            company = trade.get('company', 'N/A')
            ticker = trade.get('ticker', 'N/A')
            message += f'{company}\n\n'
            
            if trade.get('earnings_date') != 'N/A':
                message += f'    EARNINGS DATE: {trade["earnings_date"]}\n'
            if trade.get('analysis'):
                message += f'    ANALYSIS: {trade["analysis"]}\n'
            if trade.get('strategy'):
                message += f'    STRATEGY: {trade["strategy"]}\n'
            elif trade.get('rationale') != 'N/A':
                message += f'    ANALYSIS: {trade["rationale"]}\n'
            message += '\n'

    # Process day trades
    if alerts.get('day_trades'):
        message += '\nPREMIUM DAY TRADES\n\nMonday - Wednesday\n'
        for trade in alerts['day_trades']:
            company = trade.get('company', 'N/A')
            ticker = trade.get('ticker', 'N/A')
            message += f'{company}\n\n'
            
            if trade.get('why_day_trade'):
                message += f'    WHY DAY TRADE: {trade["why_day_trade"]}\n'
            elif trade.get('rationale') != 'N/A':
                message += f'    WHY DAY TRADE: {trade["rationale"]}\n'
            message += '\n'

    # Process options alerts
    if alerts.get('options_data'):
        message += '\nOPTIONS ALERTS PREMIUM\n'
        for option in alerts['options_data']:
            message += f'{option.get("ticker", "UNKNOWN")}\n\n'
            message += f'    52 WEEK HIGH: {option.get("high_52week", "N/A")}\n'
            message += f'    52 WEEK LOW: {option.get("low_52week", "N/A")}\n'
            if option.get('call_strike'):
                message += f'    CALL STRIKE: > {option["call_strike"]}\n'
            if option.get('put_strike') and option.get('put_strike') != 'N/A':
                message += f'    PUT STRIKE: < {option["put_strike"]}\n'
            message += f'    STATUS: {option.get("status", "N/A")}\n\n'
    
    print('📤 Sending structured message to both messengers...')
    print(f'Message preview:\n{message[:800]}...')
    
    # Send to both messengers
    result = await send_to_both_messengers(message)
    print(f'Send result: {result}')

if __name__ == "__main__":
    asyncio.run(send_now())