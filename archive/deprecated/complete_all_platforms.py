#!/usr/bin/env python3
"""
Complete financial alerts system for all platforms
Uses authenticated WhatsApp Web session
"""

import asyncio
import json
import os
import time
from pathlib import Path
from playwright.async_api import async_playwright

class CompleteMessagingSystem:
    def __init__(self):
        from dotenv import load_dotenv
        load_dotenv()
        
        # Platform configurations
        self.telegram_token = os.getenv('TELEGRAM_BOT_TOKEN')
        self.telegram_group = os.getenv('TELEGRAM_GROUP_ID')
        self.signal_phone = os.getenv('SIGNAL_PHONE_NUMBER', '+16572463906').strip('\'"')
        self.signal_group = os.getenv('SIGNAL_GROUP_ID', 'group.ZmFLQ25IUTBKbWpuNFdpaDdXTjVoVXpYOFZtNGVZZ1lYRGdwMWpMcW0zMD0=').strip('\'"')
        self.whatsapp_group = os.getenv('WHATSAPP_GROUP_NAMES', 'Ohms Alerts Reports')
    
    async def send_telegram(self, message):
        """Send message to Telegram"""
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
                return result.get('ok', False), "Success" if result.get('ok') else result.get('description', 'Failed')
        except Exception as e:
            return False, str(e)
    
    async def send_signal(self, message):
        """Send message to Signal"""
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
                return response.status_code in [200, 201], f"Status {response.status_code}"
        except Exception as e:
            return False, str(e)
    
    async def send_whatsapp(self, message):
        """Send message to WhatsApp using authenticated browser session"""
        async with async_playwright() as p:
            try:
                # Use the existing authenticated session directory
                session_path = Path(__file__).parent / 'browser_sessions'
                user_data_dir = None
                
                # Look for existing browser session directories
                possible_sessions = [
                    Path.home() / '.config' / 'chromium',  # Main authenticated Chromium session
                    session_path / 'mymama_session',
                    session_path / 'whatsapp_session', 
                    session_path / 'main_session',
                    Path.home() / '.cache' / 'chromium'
                ]
                
                for session_dir in possible_sessions:
                    if session_dir.exists():
                        user_data_dir = str(session_dir)
                        break
                
                if user_data_dir:
                    # Use persistent context with existing session
                    context = await p.chromium.launch_persistent_context(
                        user_data_dir=user_data_dir,
                        headless=True,  # Use headless for server environment
                        args=['--no-sandbox', '--disable-dev-shm-usage', '--disable-gpu']
                    )
                    page = await context.new_page()
                else:
                    # Launch browser without specific session
                    browser = await p.chromium.launch(
                        headless=True,
                        args=['--no-sandbox', '--disable-dev-shm-usage', '--disable-gpu']
                    )
                    context = await browser.new_context()
                    page = await context.new_page()
                
                # Navigate to WhatsApp Web
                await page.goto("https://web.whatsapp.com")
                
                # Wait for WhatsApp to load (authenticated session should load quickly)
                try:
                    await page.wait_for_selector('div[contenteditable="true"]', timeout=30000)
                except:
                    return False, "WhatsApp Web not loaded or not authenticated"
                
                # Wait a moment for full load
                await page.wait_for_timeout(3000)
                
                # Find search box and search for group
                search_elements = await page.query_selector_all('div[contenteditable="true"]')
                if not search_elements:
                    return False, "Search box not found"
                
                search_box = search_elements[0]
                await search_box.click()
                await search_box.fill(self.whatsapp_group)
                await page.wait_for_timeout(3000)
                
                # Click on the group
                try:
                    group_selector = f'span[title="{self.whatsapp_group}"]'
                    await page.wait_for_selector(group_selector, timeout=10000)
                    await page.click(group_selector)
                    await page.wait_for_timeout(2000)
                except:
                    return False, f"Group '{self.whatsapp_group}' not found"
                
                # Find message input box
                message_elements = await page.query_selector_all('div[contenteditable="true"]')
                if len(message_elements) < 2:
                    return False, "Message input box not found"
                
                message_box = message_elements[-1]
                await message_box.click()
                
                # Send message
                lines = message.split('\n')
                for i, line in enumerate(lines):
                    if line.strip():
                        await message_box.type(line, delay=30)
                    if i < len(lines) - 1:
                        await page.keyboard.press('Shift+Enter')
                
                await page.keyboard.press('Enter')
                await page.wait_for_timeout(2000)
                
                return True, "Success"
                
            except Exception as e:
                return False, str(e)
                
            finally:
                try:
                    if 'browser' in locals():
                        await browser.close()
                    elif 'context' in locals():
                        await context.close()
                except:
                    pass
    
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
        
        print(f"📤 Sending message ({len(message)} chars) to all platforms...")
        
        # Send to all platforms concurrently
        telegram_task = self.send_telegram(message)
        signal_task = self.send_signal(message)
        whatsapp_task = self.send_whatsapp(message)
        
        telegram_result, signal_result, whatsapp_result = await asyncio.gather(
            telegram_task, signal_task, whatsapp_task
        )
        
        results['telegram'] = telegram_result
        results['signal'] = signal_result
        results['whatsapp'] = whatsapp_result
        
        return results

async def main():
    """Main function"""
    print("🚀 Complete Financial Alerts System")
    print("📱 Telegram + Signal + WhatsApp")
    print("=" * 50)
    
    messenger = CompleteMessagingSystem()
    
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
    
    print("\n🎯 Complete financial alerts sent to all platforms!")

if __name__ == "__main__":
    asyncio.run(main())