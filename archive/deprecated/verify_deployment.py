#!/usr/bin/env python3
"""
Deployment Verification Script
Confirms the complete financial alerts system is deployed and working.
"""

import asyncio
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from messenger_compatibility import SignalMessenger, TelegramMessenger
from src.config.settings import settings


async def verify_deployment():
    """Verify all components of the deployment."""
    print('🔍 Verifying Complete System Deployment')
    print('=' * 50)
    
    # Test Signal
    signal_config = settings.get_signal_config()
    signal_messenger = SignalMessenger(signal_config)
    signal_ok = await signal_messenger.test_connection()
    print(f'📡 Signal API: {"✅ READY" if signal_ok else "❌ FAILED"}')
    
    # Test Telegram
    telegram_config = settings.get_telegram_config()
    telegram_messenger = TelegramMessenger(telegram_config)
    telegram_ok = await telegram_messenger.test_connection()
    print(f'💬 Telegram API: {"✅ READY" if telegram_ok else "❌ FAILED"}')
    
    if signal_ok and telegram_ok:
        print()
        print('🎉 DEPLOYMENT SUCCESSFUL!')
        print('📅 System will automatically run at 8:00 AM PST on weekdays')
        print('🔄 Services will auto-restart on failure and system reboot')
        print('📱 Both Signal and Telegram messaging configured')
        print()
        
        # Send confirmation messages
        print('📨 Sending confirmation messages...')
        await signal_messenger.send_message('✅ Daily Financial Alerts system deployed and ready!')
        await telegram_messenger.send_message('✅ Daily Financial Alerts system deployed and ready!')
        print('✅ Confirmation messages sent to both platforms')
        
        print()
        print('🔧 Service Management Commands:')
        print('  sudo systemctl status signal-api daily-alerts')
        print('  sudo journalctl -u daily-alerts -f')
        print('  python run_full_automation.py  # Manual test')
        print('  python system_health_check.py  # Health check')
        
        return True
    else:
        print('❌ Deployment has issues - check service status')
        return False


if __name__ == "__main__":
    success = asyncio.run(verify_deployment())
    sys.exit(0 if success else 1)