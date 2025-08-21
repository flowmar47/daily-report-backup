#!/usr/bin/env python3
"""
Final working financial alerts system
Sends to Telegram and Signal (proven working)
WhatsApp can be added once session is properly configured
"""

import asyncio
import json
import os
from pathlib import Path

async def send_telegram(message, token, group_id):
    """Send message to Telegram"""
    try:
        import httpx
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"https://api.telegram.org/bot{token}/sendMessage",
                json={"chat_id": group_id, "text": message}
            )
            result = response.json()
            return result.get('ok', False)
    except Exception as e:
        print(f"Telegram error: {e}")
        return False

async def send_signal(message, phone, group_id):
    """Send message to Signal"""
    try:
        import httpx
        payload = {
            "number": phone,
            "recipients": [group_id],
            "message": message
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "http://localhost:8080/v2/send",
                json=payload,
                timeout=30.0
            )
            return response.status_code in [200, 201]
    except Exception as e:
        print(f"Signal error: {e}")
        return False

async def send_telegram_photo(file_path, caption, token, group_id):
    """Send photo to Telegram"""
    try:
        import httpx
        async with httpx.AsyncClient() as client:
            with open(file_path, 'rb') as f:
                files = {'photo': f}
                data = {'chat_id': group_id, 'caption': caption}
                response = await client.post(
                    f"https://api.telegram.org/bot{token}/sendPhoto",
                    data=data,
                    files=files
                )
                result = response.json()
                return result.get('ok', False)
    except Exception as e:
        print(f"Telegram photo error: {e}")
        return False

def generate_report(alerts_data):
    """Generate financial report"""
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
    
    return "\n".join(sections).strip()

async def main():
    """Main function"""
    from dotenv import load_dotenv
    load_dotenv()
    
    print("🚀 Financial Alerts System")
    print("=" * 40)
    
    # Configuration
    telegram_token = os.getenv('TELEGRAM_BOT_TOKEN')
    telegram_group = os.getenv('TELEGRAM_GROUP_ID')
    signal_phone = os.getenv('SIGNAL_PHONE_NUMBER', '+16572463906').strip('\'"')
    signal_group = os.getenv('SIGNAL_GROUP_ID', 'group.ZmFLQ25IUTBKbWpuNFdpaDdXTjVoVXpYOFZtNGVZZ1lYRGdwMWpMcW0zMD0=').strip('\'"')
    
    # Load alerts
    alerts_file = Path(__file__).parent / 'real_alerts_only' / 'latest_real_alerts.json'
    if not alerts_file.exists():
        print("❌ No alerts file found")
        return
    
    with open(alerts_file, 'r') as f:
        alerts_data = json.load(f)
    
    report = generate_report(alerts_data)
    print(f"📊 Report generated: {len(report)} characters")
    
    # Split if too long
    max_length = 3000
    if len(report) > max_length:
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
    else:
        parts = [report]
    
    print(f"📤 Sending {len(parts)} part(s)...")
    
    # Send each part
    for i, part in enumerate(parts):
        prefix = f"[Part {i+1}/{len(parts)}]\n\n" if len(parts) > 1 else ""
        message = prefix + part
        
        print(f"\n📨 Part {i+1}/{len(parts)}:")
        
        # Send to Telegram
        if telegram_token and telegram_group:
            telegram_success = await send_telegram(message, telegram_token, telegram_group)
            status = "✅" if telegram_success else "❌"
            print(f"{status} Telegram: {'Success' if telegram_success else 'Failed'}")
        else:
            print("⚠️ Telegram: Not configured")
        
        # Send to Signal
        if signal_phone and signal_group:
            signal_success = await send_signal(message, signal_phone, signal_group)
            status = "✅" if signal_success else "❌"
            print(f"{status} Signal: {'Success' if signal_success else 'Failed'}")
        else:
            print("⚠️ Signal: Not configured")
        
        if i < len(parts) - 1:
            await asyncio.sleep(2)
    
    # Send heatmaps
    heatmap_dir = Path(__file__).parent / 'heatmaps' / 'reports'
    if heatmap_dir.exists() and telegram_token and telegram_group:
        heatmap_dirs = sorted([d for d in heatmap_dir.iterdir() if d.is_dir()], reverse=True)
        if heatmap_dirs:
            latest = heatmap_dirs[0]
            print(f"\n📊 Sending heatmaps from: {latest.name}")
            
            categorical = latest / 'categorical_heatmap.png'
            forex_pairs = latest / 'forex_pairs_heatmap.png'
            
            if categorical.exists():
                success = await send_telegram_photo(
                    str(categorical),
                    "Interest Rate Categorical Analysis",
                    telegram_token,
                    telegram_group
                )
                status = "✅" if success else "❌"
                print(f"{status} Telegram: Categorical heatmap")
            
            if forex_pairs.exists():
                success = await send_telegram_photo(
                    str(forex_pairs),
                    "Forex Pairs Differential Matrix",
                    telegram_token,
                    telegram_group
                )
                status = "✅" if success else "❌"
                print(f"{status} Telegram: Forex pairs heatmap")
    
    print("\n🎯 Financial alerts sent successfully!")
    print("\nℹ️ WhatsApp Integration:")
    print("   • Phone: +19093746793")
    print("   • Group: 'Ohms Alerts Reports'")
    print("   • To enable: Set up WhatsApp Web authentication")
    print("   • URL: https://web.whatsapp.com")

if __name__ == "__main__":
    asyncio.run(main())