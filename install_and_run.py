#!/usr/bin/env python3
"""
Install dependencies and run financial alerts system
"""

import subprocess
import sys
import os
from pathlib import Path

def install_dependencies():
    """Install required dependencies"""
    print("📦 Installing dependencies...")
    
    # Activate virtual environment and install packages
    venv_path = Path(__file__).parent / 'venv'
    if venv_path.exists():
        pip_cmd = str(venv_path / 'bin' / 'pip')
    else:
        pip_cmd = 'pip3'
    
    packages = [
        'selenium>=4.0.0',
        'httpx>=0.24.0',
        'python-dotenv>=1.0.0',
        'tenacity>=8.0.0'
    ]
    
    try:
        for package in packages:
            print(f"Installing {package}...")
            subprocess.run([pip_cmd, 'install', package], check=True, capture_output=True)
        
        print("✅ Dependencies installed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install dependencies: {e}")
        return False

def check_chrome():
    """Check for Chrome/Chromium installation"""
    chrome_paths = [
        '/usr/bin/chromium-browser',
        '/usr/bin/google-chrome',
        '/usr/bin/chrome',
        '/snap/bin/chromium'
    ]
    
    for path in chrome_paths:
        if os.path.exists(path):
            print(f"✅ Found Chrome at: {path}")
            return path
    
    print("❌ Chrome/Chromium not found")
    return None

def run_financial_alerts():
    """Run the financial alerts system"""
    print("🚀 Running financial alerts system...")
    
    # Import and run the alerts system
    try:
        import asyncio
        from send_all_platforms import main
        asyncio.run(main())
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("Falling back to simple script...")
        
        # Fallback to simple version
        import json
        import httpx
        
        alerts_file = Path(__file__).parent / 'real_alerts_only' / 'latest_real_alerts.json'
        if not alerts_file.exists():
            print("❌ No alerts file found")
            return
        
        with open(alerts_file, 'r') as f:
            alerts_data = json.load(f)
        
        # Generate simple report
        report_lines = []
        
        forex_alerts = alerts_data.get('forex_alerts', {})
        if forex_alerts:
            report_lines.append("FOREX PAIRS")
            report_lines.append("")
            for pair, data in forex_alerts.items():
                report_lines.append(f"Pair: {pair}")
                report_lines.append(f"Signal: {data.get('signal', 'N/A')}")
                report_lines.append(f"Entry: {data.get('entry', 'N/A')}")
                report_lines.append(f"Exit: {data.get('exit', 'N/A')}")
                report_lines.append("")
        
        options_data = alerts_data.get('options_data', [])
        if options_data:
            report_lines.append("OPTIONS")
            report_lines.append("")
            for option in options_data:
                report_lines.append(f"Symbol: {option.get('ticker', 'N/A')}")
                report_lines.append(f"Status: {option.get('status', 'N/A')}")
                report_lines.append("")
        
        report = "\n".join(report_lines)
        
        # Send to Telegram only as fallback
        telegram_token = os.getenv('TELEGRAM_BOT_TOKEN')
        telegram_group = os.getenv('TELEGRAM_GROUP_ID')
        
        if telegram_token and telegram_group:
            try:
                import requests
                response = requests.post(
                    f"https://api.telegram.org/bot{telegram_token}/sendMessage",
                    json={
                        "chat_id": telegram_group,
                        "text": report
                    }
                )
                if response.json().get('ok'):
                    print("✅ Telegram: Fallback message sent")
                else:
                    print("❌ Telegram: Fallback failed")
            except Exception as e:
                print(f"❌ Fallback error: {e}")

def main():
    print("🏦 Financial Alerts System Setup")
    print("=" * 40)
    
    # Load environment
    from dotenv import load_dotenv
    load_dotenv()
    
    # Check dependencies
    if not install_dependencies():
        print("❌ Dependency installation failed")
        return
    
    # Check Chrome
    chrome_path = check_chrome()
    if not chrome_path:
        print("⚠️ Chrome not found, WhatsApp messaging will be disabled")
    
    # Run the system
    run_financial_alerts()

if __name__ == "__main__":
    main()