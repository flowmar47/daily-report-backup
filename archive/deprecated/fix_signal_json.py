#!/usr/bin/env python3
"""
Fix Signal messenger JSON formatting issues
"""

import os
import json
import httpx
import asyncio
from pathlib import Path

async def test_signal_api():
    """Test Signal API with proper JSON formatting"""
    
    phone_number = os.getenv('SIGNAL_PHONE_NUMBER', '+16572463906').strip('\'"')
    group_id = os.getenv('SIGNAL_GROUP_ID', 'group.ZmFLQ25IUTBKbWpuNFdpaDdXTjVoVXpYOFZtNGVZZ1lYRGdwMWpMcW0zMD0=').strip('\'"')
    
    payload = {
        "number": phone_number,
        "recipients": [group_id],
        "message": "Test message with proper JSON formatting"
    }
    
    print(f"Testing Signal API with payload: {json.dumps(payload, indent=2)}")
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "http://localhost:8080/v2/send",
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=30.0
            )
            
            print(f"Response status: {response.status_code}")
            print(f"Response text: {response.text}")
            
            if response.status_code in [200, 201]:
                print("✅ Signal API test successful")
                return True
            else:
                print(f"❌ Signal API test failed: {response.status_code}")
                return False
                
    except Exception as e:
        print(f"❌ Signal API error: {e}")
        return False

def fix_unified_messenger():
    """Fix the Signal messenger JSON construction"""
    
    file_path = Path(__file__).parent / 'src' / 'messengers' / 'unified_messenger.py'
    
    with open(file_path, 'r') as f:
        content = f.read()
    
    # Find and fix the Signal send method
    old_payload = '''payload = {
                'number': self.config['phone_number'],
                'recipients': [target_group],
                'message': message
            }'''
    
    new_payload = '''# Ensure proper JSON formatting
            payload = {
                "number": str(self.config['phone_number']).strip('\\"\''),
                "recipients": [str(target_group).strip('\\"\'')],
                "message": str(message)
            }'''
    
    if old_payload in content:
        content = content.replace(old_payload, new_payload)
        
        with open(file_path, 'w') as f:
            f.write(content)
        
        print("✅ Fixed Signal messenger JSON formatting")
    else:
        print("⚠️ Signal payload not found in expected format")

async def send_financial_report():
    """Send financial report using corrected Signal API"""
    
    from dotenv import load_dotenv
    load_dotenv()
    
    # Load latest alerts
    alerts_file = Path(__file__).parent / 'real_alerts_only' / 'latest_real_alerts.json'
    
    if not alerts_file.exists():
        print("❌ No alerts file found")
        return
    
    with open(alerts_file, 'r') as f:
        alerts_data = json.load(f)
    
    # Generate report
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
    
    report = "\n".join(sections).strip()
    
    # Send to Signal and Telegram
    phone_number = os.getenv('SIGNAL_PHONE_NUMBER', '+16572463906').strip('\'"')
    group_id = os.getenv('SIGNAL_GROUP_ID', 'group.ZmFLQ25IUTBKbWpuNFdpaDdXTjVoVXpYOFZtNGVZZ1lYRGdwMWpMcW0zMD0=').strip('\'"')
    telegram_token = os.getenv('TELEGRAM_BOT_TOKEN')
    telegram_group = os.getenv('TELEGRAM_GROUP_ID')
    
    # Split if too long
    max_length = 2000
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
    
    async with httpx.AsyncClient() as client:
        for i, part in enumerate(parts):
            prefix = f"[Part {i+1}/{len(parts)}]\n\n" if len(parts) > 1 else ""
            message = prefix + part
            
            # Send to Signal
            signal_payload = {
                "number": phone_number,
                "recipients": [group_id],
                "message": message
            }
            
            try:
                response = await client.post(
                    "http://localhost:8080/v2/send",
                    json=signal_payload,
                    headers={"Content-Type": "application/json"},
                    timeout=30.0
                )
                
                if response.status_code in [200, 201]:
                    print(f"✅ Signal: Part {i+1} sent successfully")
                else:
                    print(f"❌ Signal: Part {i+1} failed - {response.status_code}")
                    
            except Exception as e:
                print(f"❌ Signal error: {e}")
            
            # Send to Telegram
            if telegram_token and telegram_group:
                try:
                    response = await client.post(
                        f"https://api.telegram.org/bot{telegram_token}/sendMessage",
                        json={
                            "chat_id": telegram_group,
                            "text": message,
                            "parse_mode": "Markdown"
                        }
                    )
                    
                    result = response.json()
                    if result.get('ok'):
                        print(f"✅ Telegram: Part {i+1} sent successfully")
                    else:
                        print(f"❌ Telegram: Part {i+1} failed - {result.get('description')}")
                        
                except Exception as e:
                    print(f"❌ Telegram error: {e}")
            
            if i < len(parts) - 1:
                await asyncio.sleep(2)

async def main():
    print("🔧 Fixing Signal JSON formatting...")
    fix_unified_messenger()
    
    print("\n🧪 Testing Signal API...")
    if await test_signal_api():
        print("\n📊 Sending financial report...")
        await send_financial_report()
    else:
        print("❌ Signal API test failed, skipping report send")

if __name__ == "__main__":
    asyncio.run(main())