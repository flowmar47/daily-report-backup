#!/usr/bin/env python3
"""
Production financial alerts system
Sends to Telegram, Signal, and WhatsApp (if authenticated)
"""

import asyncio
import json
import os
import time
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

def send_whatsapp(message, group_name):
    """Send message to WhatsApp (if session exists)"""
    try:
        from selenium import webdriver
        from selenium.webdriver.common.by import By
        from selenium.webdriver.common.keys import Keys
        from selenium.webdriver.support.ui import WebDriverWait
        from selenium.webdriver.support import expected_conditions as EC
        from selenium.webdriver.chrome.options import Options
        from selenium.webdriver.chrome.service import Service
        
        session_path = Path(__file__).parent / 'browser_sessions' / 'whatsapp_main'
        
        # Check if session exists
        if not session_path.exists():
            print("⚠️ WhatsApp session not found. Run setup_whatsapp_production.py first")
            return False
        
        chrome_options = Options()
        chrome_options.add_argument(f"--user-data-dir={session_path}")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--headless=new")
        chrome_options.binary_location = "/usr/bin/chromium-browser"
        
        service = Service("/usr/bin/chromedriver")
        driver = webdriver.Chrome(service=service, options=chrome_options)
        
        try:
            driver.get("https://web.whatsapp.com")
            wait = WebDriverWait(driver, 30)
            
            # Wait for WhatsApp to load
            wait.until(EC.presence_of_element_located((By.XPATH, '//div[@contenteditable="true"]')))
            
            # Find search box
            search_elements = driver.find_elements(By.XPATH, '//div[@contenteditable="true"]')
            if search_elements:
                search_box = search_elements[0]
                search_box.clear()
                search_box.send_keys(group_name)
                time.sleep(3)
                
                # Click on group
                group_elements = driver.find_elements(By.XPATH, f'//span[@title="{group_name}"]')
                if group_elements:
                    group_elements[0].click()
                    time.sleep(2)
                    
                    # Send message
                    message_elements = driver.find_elements(By.XPATH, '//div[@contenteditable="true"]')
                    if len(message_elements) > 1:
                        message_box = message_elements[-1]
                        
                        lines = message.split('\n')
                        for i, line in enumerate(lines):
                            if line.strip():
                                message_box.send_keys(line)
                            if i < len(lines) - 1:
                                message_box.send_keys(Keys.SHIFT + Keys.ENTER)
                        
                        message_box.send_keys(Keys.ENTER)
                        time.sleep(2)
                        return True
            
            return False
            
        finally:
            driver.quit()
            
    except Exception as e:
        print(f"WhatsApp error: {e}")
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
    
    # Configuration
    telegram_token = os.getenv('TELEGRAM_BOT_TOKEN')
    telegram_group = os.getenv('TELEGRAM_GROUP_ID')
    signal_phone = os.getenv('SIGNAL_PHONE_NUMBER', '+16572463906').strip('\'"')
    signal_group = os.getenv('SIGNAL_GROUP_ID', 'group.ZmFLQ25IUTBKbWpuNFdpaDdXTjVoVXpYOFZtNGVZZ1lYRGdwMWpMcW0zMD0=').strip('\'"')
    whatsapp_group = os.getenv('WHATSAPP_GROUP_NAMES', 'Ohms Alerts Reports')
    
    # Load alerts
    alerts_file = Path(__file__).parent / 'real_alerts_only' / 'latest_real_alerts.json'
    if not alerts_file.exists():
        print("❌ No alerts file found")
        return
    
    with open(alerts_file, 'r') as f:
        alerts_data = json.load(f)
    
    report = generate_report(alerts_data)
    
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
    
    # Send each part
    for i, part in enumerate(parts):
        prefix = f"[Part {i+1}/{len(parts)}]\n\n" if len(parts) > 1 else ""
        message = prefix + part
        
        print(f"📤 Sending part {i+1}/{len(parts)}")
        
        # Send to all platforms
        results = {}
        
        if telegram_token and telegram_group:
            results['telegram'] = await send_telegram(message, telegram_token, telegram_group)
        
        if signal_phone and signal_group:
            results['signal'] = await send_signal(message, signal_phone, signal_group)
        
        if whatsapp_group:
            results['whatsapp'] = send_whatsapp(message, whatsapp_group)
        
        # Report results
        for platform, success in results.items():
            status = "✅" if success else "❌"
            print(f"{status} {platform.title()}: {'Success' if success else 'Failed'}")
        
        if i < len(parts) - 1:
            await asyncio.sleep(2)

if __name__ == "__main__":
    asyncio.run(main())