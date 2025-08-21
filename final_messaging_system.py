#!/usr/bin/env python3
"""
Final unified messaging system for all platforms
Automatically installs dependencies and sends to all configured platforms
"""

import asyncio
import json
import os
import subprocess
import sys
from pathlib import Path

def install_dependencies():
    """Install required packages"""
    packages = ['httpx>=0.24.0', 'python-dotenv>=1.0.0', 'selenium>=4.0.0']
    
    venv_path = Path(__file__).parent / 'venv'
    if venv_path.exists():
        pip_cmd = str(venv_path / 'bin' / 'pip')
    else:
        pip_cmd = 'pip3'
    
    for package in packages:
        try:
            subprocess.run([pip_cmd, 'install', package], check=True, capture_output=True)
        except:
            pass  # Continue if install fails

class FinalMessagingSystem:
    def __init__(self):
        # Load environment
        try:
            from dotenv import load_dotenv
            load_dotenv()
        except ImportError:
            pass
        
        # Platform configurations
        self.telegram_token = os.getenv('TELEGRAM_BOT_TOKEN')
        self.telegram_group = os.getenv('TELEGRAM_GROUP_ID')
        self.signal_phone = os.getenv('SIGNAL_PHONE_NUMBER', '+16572463906').strip('\'"')
        self.signal_group = os.getenv('SIGNAL_GROUP_ID', 'group.ZmFLQ25IUTBKbWpuNFdpaDdXTjVoVXpYOFZtNGVZZ1lYRGdwMWpMcW0zMD0=').strip('\'"')
        self.whatsapp_phone = os.getenv('WHATSAPP_PHONE_NUMBER')
        self.whatsapp_group = os.getenv('WHATSAPP_GROUP_NAMES')
    
    async def send_telegram(self, message):
        """Send to Telegram"""
        if not self.telegram_token or not self.telegram_group:
            return False, "Not configured"
        
        try:
            import httpx
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"https://api.telegram.org/bot{self.telegram_token}/sendMessage",
                    json={"chat_id": self.telegram_group, "text": message}
                )
                result = response.json()
                return result.get('ok', False), result.get('description', 'Success')
        except Exception as e:
            return False, str(e)
    
    async def send_signal(self, message):
        """Send to Signal"""
        if not self.signal_phone or not self.signal_group:
            return False, "Not configured"
        
        try:
            import httpx
            payload = {
                "number": self.signal_phone,
                "recipients": [self.signal_group],
                "message": message
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    "http://localhost:8080/v2/send",
                    json=payload,
                    timeout=30.0
                )
                return response.status_code in [200, 201], f"Status: {response.status_code}"
        except Exception as e:
            return False, str(e)
    
    def send_whatsapp(self, message):
        """Send to WhatsApp"""
        if not self.whatsapp_phone or not self.whatsapp_group:
            return False, "Not configured"
        
        try:
            from selenium import webdriver
            from selenium.webdriver.common.by import By
            from selenium.webdriver.common.keys import Keys
            from selenium.webdriver.support.ui import WebDriverWait
            from selenium.webdriver.support import expected_conditions as EC
            from selenium.webdriver.chrome.options import Options
            from selenium.webdriver.chrome.service import Service
            import time
            
            session_path = Path(__file__).parent / 'browser_sessions' / 'whatsapp_main'
            session_path.mkdir(parents=True, exist_ok=True)
            
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
                
                # Find and use search box
                search_elements = driver.find_elements(By.XPATH, '//div[@contenteditable="true"]')
                if search_elements:
                    search_box = search_elements[0]
                    search_box.clear()
                    search_box.send_keys(self.whatsapp_group)
                    time.sleep(3)
                    
                    # Click on group
                    group_elements = driver.find_elements(By.XPATH, f'//span[@title="{self.whatsapp_group}"]')
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
                            return True, "Success"
                    else:
                        return False, f"Group '{self.whatsapp_group}' not found"
                else:
                    return False, "Search box not found"
                    
            finally:
                driver.quit()
                
        except ImportError:
            return False, "Selenium not available"
        except Exception as e:
            return False, str(e)
    
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
        """Send to all platforms"""
        results = {}
        
        # Send to Telegram and Signal concurrently
        telegram_task = self.send_telegram(message)
        signal_task = self.send_signal(message)
        
        telegram_result = await telegram_task
        signal_result = await signal_task
        
        results['telegram'] = telegram_result
        results['signal'] = signal_result
        
        # Send to WhatsApp
        whatsapp_result = self.send_whatsapp(message)
        results['whatsapp'] = whatsapp_result
        
        return results

async def main():
    """Main function"""
    print("📦 Installing dependencies...")
    install_dependencies()
    
    print("🚀 Initializing messaging system...")
    messenger = FinalMessagingSystem()
    
    # Load alerts
    alerts_file = Path(__file__).parent / 'real_alerts_only' / 'latest_real_alerts.json'
    if not alerts_file.exists():
        print("❌ No alerts file found")
        return
    
    with open(alerts_file, 'r') as f:
        alerts_data = json.load(f)
    
    report = messenger.generate_report(alerts_data)
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
        results = await messenger.send_to_all(message)
        
        for platform, (success, details) in results.items():
            status = "✅" if success else "❌"
            print(f"{status} {platform.title()}: {details}")
        
        if i < len(parts) - 1:
            await asyncio.sleep(2)
    
    print("\n🎯 Messaging complete!")

if __name__ == "__main__":
    asyncio.run(main())