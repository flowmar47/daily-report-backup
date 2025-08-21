#!/usr/bin/env python3
"""
Send financial alerts to all configured groups
"""

import asyncio
import json
import os
import httpx
from pathlib import Path
from datetime import datetime

async def send_to_telegram(message: str, bot_token: str, group_id: str):
    """Send message to Telegram"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"https://api.telegram.org/bot{bot_token}/sendMessage",
                json={
                    "chat_id": group_id,
                    "text": message,
                    "parse_mode": "Markdown"
                }
            )
            result = response.json()
            if result.get('ok'):
                print(f"✅ Telegram: Message sent successfully")
            else:
                print(f"❌ Telegram: {result.get('description', 'Unknown error')}")
    except Exception as e:
        print(f"❌ Telegram error: {e}")

async def send_to_signal(message: str, phone: str, group_id: str):
    """Send message to Signal"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "http://localhost:8080/v2/send",
                json={
                    "number": phone,
                    "recipients": [group_id],
                    "message": message
                }
            )
            if response.status_code in [200, 201]:
                print(f"✅ Signal: Message sent successfully")
            else:
                print(f"❌ Signal: HTTP {response.status_code}")
    except Exception as e:
        print(f"❌ Signal error: {e}")

async def send_telegram_photo(file_path: str, caption: str, bot_token: str, group_id: str):
    """Send photo to Telegram"""
    try:
        async with httpx.AsyncClient() as client:
            with open(file_path, 'rb') as f:
                files = {'photo': f}
                data = {'chat_id': group_id, 'caption': caption}
                response = await client.post(
                    f"https://api.telegram.org/bot{bot_token}/sendPhoto",
                    data=data,
                    files=files
                )
                result = response.json()
                if result.get('ok'):
                    print(f"✅ Telegram: Photo sent successfully")
                else:
                    print(f"❌ Telegram photo: {result.get('description', 'Unknown error')}")
    except Exception as e:
        print(f"❌ Telegram photo error: {e}")

def generate_report(alerts_data):
    """Generate structured financial report"""
    sections = []
    
    # Forex section
    forex_alerts = alerts_data.get('forex_alerts', {})
    if forex_alerts:
        sections.append("FOREX PAIRS\n")
        for pair, data in forex_alerts.items():
            sections.append(f"Pair: {pair}")
            sections.append(f"High: {data.get('high', 'N/A')}")
            sections.append(f"Average: {data.get('average', 'N/A')}")
            sections.append(f"Low: {data.get('low', 'N/A')}")
            sections.append(f"MT4 Action: MT4 {data.get('signal', 'N/A')}")
            sections.append(f"Exit: {data.get('exit', 'N/A')}")
            sections.append("")
    
    # Options section
    options_data = alerts_data.get('options_data', [])
    if options_data:
        sections.append("EQUITIES AND OPTIONS\n")
        for option in options_data:
            sections.append(f"Symbol: {option.get('ticker', 'N/A')}")
            sections.append(f"52 Week High: {option.get('high_52week', 'N/A')}")
            sections.append(f"52 Week Low: {option.get('low_52week', 'N/A')}")
            sections.append("Strike Price:")
            sections.append("")
            sections.append(f"CALL > {option.get('call_strike', 'N/A')}")
            sections.append("")
            sections.append(f"PUT < {option.get('put_strike', 'N/A')}")
            sections.append(f"Status: {option.get('status', 'N/A')}")
            sections.append("")
    
    # Premium trades sections
    swing_trades = alerts_data.get('swing_trades', [])
    if swing_trades:
        sections.append("PREMIUM SWING TRADES (Monday - Wednesday)\n")
        for trade in swing_trades:
            sections.append(f"{trade.get('company', 'N/A')} ({trade.get('ticker', 'N/A')})")
            sections.append(f"Earnings Report: {trade.get('earnings_date', 'N/A')}")
            if 'analysis' in trade and trade['analysis']:
                sections.append(f"Rationale: {trade['analysis']}")
            sections.append("")
    
    day_trades = alerts_data.get('day_trades', [])
    if day_trades:
        sections.append("PREMIUM DAY TRADES (Wednesday - Friday)\n")
        for trade in day_trades:
            sections.append(f"{trade.get('company', 'N/A')} ({trade.get('ticker', 'N/A')})")
            if 'analysis' in trade and trade['analysis']:
                sections.append(f"Analysis: {trade['analysis']}")
            sections.append("")
    
    return "\n".join(sections).strip()

async def main():
    """Main function"""
    # Load environment variables
    from dotenv import load_dotenv
    load_dotenv()
    
    # Get credentials
    telegram_token = os.getenv('TELEGRAM_BOT_TOKEN')
    telegram_group = os.getenv('TELEGRAM_GROUP_ID')
    signal_phone = os.getenv('SIGNAL_PHONE_NUMBER')
    signal_group = os.getenv('SIGNAL_GROUP_ID')
    
    # Load latest alerts
    alerts_file = Path(__file__).parent / 'real_alerts_only' / 'latest_real_alerts.json'
    if not alerts_file.exists():
        print("❌ No alerts file found")
        return
    
    with open(alerts_file, 'r') as f:
        alerts_data = json.load(f)
    
    # Generate report
    report = generate_report(alerts_data)
    print(f"\n📊 Report length: {len(report)} characters")
    print("=" * 50)
    
    # Split message if too long
    max_length = 4000
    if len(report) > max_length:
        # Split by sections
        parts = []
        current_part = ""
        for line in report.split('\n'):
            if len(current_part + line + '\n') > max_length:
                parts.append(current_part.strip())
                current_part = line + '\n'
            else:
                current_part += line + '\n'
        if current_part:
            parts.append(current_part.strip())
        
        print(f"📝 Message split into {len(parts)} parts")
        
        # Send each part
        for i, part in enumerate(parts):
            prefix = f"[Part {i+1}/{len(parts)}]\n\n" if len(parts) > 1 else ""
            message = prefix + part
            
            tasks = []
            if telegram_token and telegram_group:
                tasks.append(send_to_telegram(message, telegram_token, telegram_group))
            
            if signal_phone and signal_group:
                tasks.append(send_to_signal(message, signal_phone, signal_group))
            
            await asyncio.gather(*tasks)
            await asyncio.sleep(1)  # Brief delay between parts
    else:
        # Send as single message
        tasks = []
        
        if telegram_token and telegram_group:
            tasks.append(send_to_telegram(report, telegram_token, telegram_group))
        
        if signal_phone and signal_group:
            tasks.append(send_to_signal(report, signal_phone, signal_group))
        
        await asyncio.gather(*tasks)
    
    # Send heatmaps
    heatmap_dir = Path(__file__).parent / 'heatmaps' / 'reports'
    if heatmap_dir.exists():
        heatmap_dirs = sorted([d for d in heatmap_dir.iterdir() if d.is_dir()], reverse=True)
        if heatmap_dirs:
            latest = heatmap_dirs[0]
            print(f"\n📊 Sending heatmaps from: {latest.name}")
            
            categorical = latest / 'categorical_heatmap.png'
            forex_pairs = latest / 'forex_pairs_heatmap.png'
            
            heatmap_tasks = []
            
            if telegram_token and telegram_group:
                if categorical.exists():
                    heatmap_tasks.append(send_telegram_photo(
                        str(categorical),
                        "Interest Rate Categorical Analysis",
                        telegram_token,
                        telegram_group
                    ))
                if forex_pairs.exists():
                    heatmap_tasks.append(send_telegram_photo(
                        str(forex_pairs),
                        "Forex Pairs Differential Matrix",
                        telegram_token,
                        telegram_group
                    ))
            
            if heatmap_tasks:
                await asyncio.gather(*heatmap_tasks)
    
    print("\n✅ All messages sent!")

if __name__ == "__main__":
    asyncio.run(main())