#!/usr/bin/env python3
"""
Send financial alerts to all platforms (Telegram, Signal, WhatsApp)
Production version without test messages
"""

import asyncio
import json
import os
import httpx
import time
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options

class AllPlatformMessenger:
    def __init__(self):
        from dotenv import load_dotenv
        load_dotenv()
        
        # Telegram config
        self.telegram_token = os.getenv('TELEGRAM_BOT_TOKEN')
        self.telegram_group = os.getenv('TELEGRAM_GROUP_ID')
        
        # Signal config
        self.signal_phone = os.getenv('SIGNAL_PHONE_NUMBER', '+16572463906').strip('\'"')
        self.signal_group = os.getenv('SIGNAL_GROUP_ID', 'group.ZmFLQ25IUTBKbWpuNFdpaDdXTjVoVXpYOFZtNGVZZ1lYRGdwMWpMcW0zMD0=').strip('\'"')
        
        # WhatsApp config
        self.whatsapp_phone = os.getenv('WHATSAPP_PHONE_NUMBER')
        self.whatsapp_group = os.getenv('WHATSAPP_GROUP_NAMES')
        
        self.whatsapp_session_path = Path(__file__).parent / 'browser_sessions' / 'whatsapp_session'
        self.whatsapp_session_path.mkdir(parents=True, exist_ok=True)
    
    async def send_telegram(self, message):
        """Send message to Telegram"""
        if not self.telegram_token or not self.telegram_group:
            return False
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"https://api.telegram.org/bot{self.telegram_token}/sendMessage",
                    json={
                        "chat_id": self.telegram_group,
                        "text": message,
                        "parse_mode": "Markdown"
                    }
                )
                result = response.json()
                return result.get('ok', False)
        except Exception as e:
            print(f"Telegram error: {e}")
            return False
    
    async def send_signal(self, message):
        """Send message to Signal"""
        if not self.signal_phone or not self.signal_group:
            return False
        
        try:
            payload = {
                "number": self.signal_phone,
                "recipients": [self.signal_group],
                "message": message
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    "http://localhost:8080/v2/send",
                    json=payload,
                    headers={"Content-Type": "application/json"},
                    timeout=30.0
                )
                return response.status_code in [200, 201]
        except Exception as e:
            print(f"Signal error: {e}")
            return False
    
    def send_whatsapp(self, message):
        """Send message to WhatsApp using Selenium"""
        if not self.whatsapp_phone or not self.whatsapp_group:
            return False
        
        chrome_options = Options()
        chrome_options.add_argument(f"--user-data-dir={self.whatsapp_session_path}")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--headless=new")
        chrome_options.binary_location = "/usr/bin/chromium-browser"
        
        driver = None
        try:
            driver = webdriver.Chrome(options=chrome_options)
            driver.get("https://web.whatsapp.com")
            wait = WebDriverWait(driver, 60)
            
            # Wait for WhatsApp to load
            wait.until(EC.presence_of_element_located((By.XPATH, '//div[@contenteditable="true"][@data-tab="3"]')))
            
            # Search for group
            search_box = driver.find_element(By.XPATH, '//div[@contenteditable="true"][@data-tab="3"]')
            search_box.clear()
            search_box.send_keys(self.whatsapp_group)
            time.sleep(3)
            
            # Click on group
            group = wait.until(EC.element_to_be_clickable((By.XPATH, f'//span[@title="{self.whatsapp_group}"]')))
            group.click()
            
            # Find message input box
            message_box = wait.until(EC.presence_of_element_located((By.XPATH, '//div[@contenteditable="true"][@data-tab="10"]')))
            
            # Send message
            lines = message.split('\n')
            for i, line in enumerate(lines):
                message_box.send_keys(line)
                if i < len(lines) - 1:
                    message_box.send_keys(Keys.SHIFT + Keys.ENTER)
            
            message_box.send_keys(Keys.ENTER)
            time.sleep(2)
            
            return True
            
        except Exception as e:
            print(f"WhatsApp error: {e}")
            return False
            
        finally:
            if driver:
                driver.quit()
    
    def generate_report(self, alerts_data):
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
    
    async def send_to_all(self, message):
        """Send message to all platforms"""
        results = {}
        
        # Send to Telegram and Signal concurrently
        telegram_task = self.send_telegram(message)
        signal_task = self.send_signal(message)
        
        telegram_result, signal_result = await asyncio.gather(telegram_task, signal_task)
        
        results['telegram'] = telegram_result
        results['signal'] = signal_result
        
        # Send to WhatsApp (synchronous)
        whatsapp_result = self.send_whatsapp(message)
        results['whatsapp'] = whatsapp_result
        
        return results

async def main():
    """Main function"""
    messenger = AllPlatformMessenger()
    
    # Load latest alerts
    alerts_file = Path(__file__).parent / 'real_alerts_only' / 'latest_real_alerts.json'
    if not alerts_file.exists():
        print("❌ No alerts file found")
        return
    
    with open(alerts_file, 'r') as f:
        alerts_data = json.load(f)
    
    report = messenger.generate_report(alerts_data)
    
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
        results = await messenger.send_to_all(message)
        
        for platform, success in results.items():
            status = "✅" if success else "❌"
            print(f"{status} {platform.title()}: {'Success' if success else 'Failed'}")
        
        if i < len(parts) - 1:
            await asyncio.sleep(2)

if __name__ == "__main__":
    asyncio.run(main())