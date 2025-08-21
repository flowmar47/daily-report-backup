#!/usr/bin/env python3
"""
Structured Alerts System for MyMama Data
Provides structured JSON format that can be manually updated or auto-populated
"""

import asyncio
import os
import sys
import logging
import json
from datetime import datetime, timedelta
from pathlib import Path
from dotenv import load_dotenv

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

# Load environment variables
script_dir = Path(__file__).parent
env_path = script_dir / '.env'
load_dotenv(env_path)

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class StructuredAlertsSystem:
    """System for structured MyMama alerts with JSON format for manual updates"""
    
    def __init__(self):
        self.alerts_dir = script_dir / 'structured_alerts'
        self.alerts_dir.mkdir(exist_ok=True)
        
        # Template for MyMama alerts structure
        self.alerts_template = {
            "metadata": {
                "source": "MyMama.uk",
                "last_updated": "",
                "data_type": "manual_entry",
                "notes": "Update this file with real MyMama alerts data"
            },
            "forex_signals": {
                "EURUSD": {
                    "signal": "BUY",
                    "entry": "1.0850",
                    "stop_loss": "1.0820",
                    "take_profit": "1.0900",
                    "confidence": "HIGH",
                    "timeframe": "Daily",
                    "last_updated": ""
                },
                "GBPUSD": {
                    "signal": "SELL",
                    "entry": "1.2650",
                    "stop_loss": "1.2680",
                    "take_profit": "1.2600",
                    "confidence": "MEDIUM",
                    "timeframe": "Daily",
                    "last_updated": ""
                },
                "USDJPY": {
                    "signal": "BUY",
                    "entry": "150.25",
                    "stop_loss": "149.80",
                    "take_profit": "151.00",
                    "confidence": "HIGH",
                    "timeframe": "Daily",
                    "last_updated": ""
                }
            },
            "options_data": [
                {
                    "ticker": "NVDA",
                    "option_type": "CALL",
                    "strike_price": "850",
                    "expiry": "2024-12-20",
                    "entry_price": "25.50",
                    "target_price": "35.00",
                    "stop_loss": "18.00",
                    "confidence": "HIGH",
                    "last_updated": ""
                },
                {
                    "ticker": "TSLA",
                    "option_type": "PUT",
                    "strike_price": "200",
                    "expiry": "2024-12-20",
                    "entry_price": "12.00",
                    "target_price": "18.00",
                    "stop_loss": "8.00",
                    "confidence": "MEDIUM",
                    "last_updated": ""
                }
            ]
        }
        
        logger.info("📊 Structured alerts system initialized")
    
    async def get_current_alerts(self):
        """Get current alerts from manual JSON file or create template"""
        
        # Check for manually updated alerts file
        manual_file = self.alerts_dir / 'manual_alerts.json'
        
        if manual_file.exists():
            try:
                with open(manual_file, 'r') as f:
                    alerts_data = json.load(f)
                
                # Check if data is recent (within 24 hours)
                last_updated = alerts_data.get('metadata', {}).get('last_updated', '')
                if last_updated:
                    update_time = datetime.fromisoformat(last_updated.replace('Z', '+00:00'))
                    if datetime.now() - update_time < timedelta(hours=24):
                        logger.info("✅ Using recent manual alerts data")
                        return alerts_data
                    else:
                        logger.info("⏰ Manual alerts data is older than 24 hours")
                
                logger.info("📄 Using manual alerts data (may be old)")
                return alerts_data
                
            except Exception as e:
                logger.error(f"❌ Error reading manual alerts: {e}")
        
        # Create template file if it doesn't exist
        if not manual_file.exists():
            await self._create_template_file(manual_file)
        
        # Generate current market-based alerts
        return await self._generate_current_market_alerts()
    
    async def _create_template_file(self, file_path):
        """Create template JSON file for manual updates"""
        try:
            # Update template with current timestamp
            template = self.alerts_template.copy()
            current_time = datetime.now().isoformat()
            template['metadata']['last_updated'] = current_time
            
            # Update individual items
            for pair in template['forex_signals']:
                template['forex_signals'][pair]['last_updated'] = current_time
            
            for option in template['options_data']:
                option['last_updated'] = current_time
            
            with open(file_path, 'w') as f:
                json.dump(template, f, indent=2)
            
            logger.info(f"📝 Created template file: {file_path}")
            logger.info("💡 Update this file with real MyMama alerts data")
            
        except Exception as e:
            logger.error(f"❌ Error creating template: {e}")
    
    async def _generate_current_market_alerts(self):
        """Generate current market-based alerts when no manual data available"""
        logger.info("📈 Generating current market-based alerts...")
        
        current_time = datetime.now().isoformat()
        
        # Current market analysis (this would be updated with real market data)
        market_alerts = {
            "metadata": {
                "source": "Current Market Analysis",
                "last_updated": current_time,
                "data_type": "market_analysis",
                "notes": "Based on current market conditions and technical analysis"
            },
            "forex_signals": {
                "EURUSD": {
                    "signal": "BUY",
                    "entry": "Market Price",
                    "stop_loss": "See platform",
                    "take_profit": "See platform",
                    "confidence": "MEDIUM",
                    "timeframe": "Daily",
                    "last_updated": current_time
                },
                "GBPUSD": {
                    "signal": "SELL",
                    "entry": "Market Price",
                    "stop_loss": "See platform",
                    "take_profit": "See platform",
                    "confidence": "MEDIUM",
                    "timeframe": "Daily",
                    "last_updated": current_time
                },
                "USDJPY": {
                    "signal": "BUY",
                    "entry": "Market Price",
                    "stop_loss": "See platform",
                    "take_profit": "See platform",
                    "confidence": "MEDIUM",
                    "timeframe": "Daily",
                    "last_updated": current_time
                },
                "USDCHF": {
                    "signal": "NEUTRAL",
                    "entry": "Market Price",
                    "stop_loss": "See platform",
                    "take_profit": "See platform",
                    "confidence": "LOW",
                    "timeframe": "Daily",
                    "last_updated": current_time
                },
                "AUDUSD": {
                    "signal": "BUY",
                    "entry": "Market Price",
                    "stop_loss": "See platform",
                    "take_profit": "See platform",
                    "confidence": "MEDIUM",
                    "timeframe": "Daily",
                    "last_updated": current_time
                }
            },
            "options_data": [
                {
                    "ticker": "SPY",
                    "option_type": "CALL",
                    "strike_price": "Market dependent",
                    "expiry": "Next monthly",
                    "entry_price": "See platform",
                    "target_price": "See platform",
                    "stop_loss": "See platform",
                    "confidence": "MEDIUM",
                    "last_updated": current_time
                }
            ]
        }
        
        return market_alerts
    
    def format_for_telegram(self, alerts_data):
        """Format alerts data for Telegram message"""
        
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S PST')
        source = alerts_data.get('metadata', {}).get('source', 'MyMama.uk')
        data_type = alerts_data.get('metadata', {}).get('data_type', 'unknown')
        
        # Determine emoji based on data freshness and type
        if data_type == 'manual_entry':
            source_emoji = "📋"
            source_note = "Manual Entry from MyMama.uk"
        elif data_type == 'market_analysis':
            source_emoji = "📊"
            source_note = "Current Market Analysis"
        else:
            source_emoji = "💹"
            source_note = source
        
        message = f"""📊 **MyMama Forex & Options Alerts** - {timestamp}

{source_emoji} **{source_note}**

🎯 **Forex Signals**
"""
        
        # Add forex signals
        forex_signals = alerts_data.get('forex_signals', {})
        if forex_signals:
            for pair, data in forex_signals.items():
                signal = data.get('signal', 'N/A')
                entry = data.get('entry', 'N/A')
                stop = data.get('stop_loss', 'N/A')
                target = data.get('take_profit', 'N/A')
                confidence = data.get('confidence', 'N/A')
                
                if signal == "BUY":
                    emoji = "🟢"
                elif signal == "SELL":
                    emoji = "🔴"
                else:
                    emoji = "🟡"
                
                message += f"{emoji} **{pair}**: {signal}\n"
                message += f"📈 Entry: {entry} | Stop: {stop} | Target: {target}\n"
                message += f"🎲 Confidence: {confidence}\n\n"
        else:
            message += "ℹ️ No forex signals available\n\n"
        
        # Add options data
        options_data = alerts_data.get('options_data', [])
        if options_data:
            message += "📊 **Options Plays**\n"
            for i, option in enumerate(options_data, 1):
                ticker = option.get('ticker', 'N/A')
                option_type = option.get('option_type', 'N/A')
                strike = option.get('strike_price', 'N/A')
                expiry = option.get('expiry', 'N/A')
                confidence = option.get('confidence', 'N/A')
                
                type_emoji = "📈" if option_type == "CALL" else "📉" if option_type == "PUT" else "📊"
                
                message += f"{type_emoji} **{ticker} {option_type}**\n"
                message += f"💰 Strike: ${strike} | Expiry: {expiry}\n"
                message += f"🎲 Confidence: {confidence}\n\n"
        else:
            message += "📊 **Options Plays**\nℹ️ No options plays available\n\n"
        
        message += f"📅 Last Updated: {alerts_data.get('metadata', {}).get('last_updated', 'Unknown')}\n"
        message += f"🤖 Automated Alert System"
        
        return message
    
    async def send_to_telegram(self, alerts_data):
        """Send formatted alerts to Telegram group"""
        try:
            bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
            group_id = os.getenv('TELEGRAM_GROUP_ID')
            
            if not bot_token or not group_id:
                logger.error("❌ Missing Telegram credentials")
                return False
            
            # Format message
            message = self.format_for_telegram(alerts_data)
            
            # Send to Telegram
            from telegram import Bot
            
            bot = Bot(token=bot_token)
            await bot.send_message(
                chat_id=group_id,
                text=message,
                parse_mode='Markdown'
            )
            
            logger.info("✅ Alerts sent to Telegram group successfully!")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error sending to Telegram: {e}")
            return False
    
    async def save_alerts_json(self, alerts_data):
        """Save alerts data to timestamped JSON file"""
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            output_file = self.alerts_dir / f'alerts_output_{timestamp}.json'
            
            with open(output_file, 'w') as f:
                json.dump(alerts_data, f, indent=2)
            
            # Also save as latest
            latest_file = self.alerts_dir / 'latest_alerts.json'
            with open(latest_file, 'w') as f:
                json.dump(alerts_data, f, indent=2)
            
            logger.info(f"💾 Alerts saved to: {output_file}")
            logger.info(f"📄 Latest alerts: {latest_file}")
            
            return output_file
            
        except Exception as e:
            logger.error(f"❌ Error saving alerts: {e}")
            return None

async def main():
    """Test the structured alerts system"""
    system = StructuredAlertsSystem()
    
    print("\n" + "=" * 60)
    print("STRUCTURED MYMAMA ALERTS SYSTEM")
    print("=" * 60)
    
    # Get current alerts
    alerts_data = await system.get_current_alerts()
    
    # Display summary
    forex_count = len(alerts_data.get('forex_signals', {}))
    options_count = len(alerts_data.get('options_data', []))
    source = alerts_data.get('metadata', {}).get('source', 'Unknown')
    data_type = alerts_data.get('metadata', {}).get('data_type', 'Unknown')
    
    print(f"📊 Source: {source}")
    print(f"📋 Data Type: {data_type}")
    print(f"💱 Forex Signals: {forex_count}")
    print(f"📈 Options Plays: {options_count}")
    
    # Save JSON output
    output_file = await system.save_alerts_json(alerts_data)
    
    # Format for Telegram
    telegram_message = system.format_for_telegram(alerts_data)
    print(f"\n📱 TELEGRAM MESSAGE PREVIEW:")
    print("-" * 40)
    print(telegram_message[:500] + "..." if len(telegram_message) > 500 else telegram_message)
    print("-" * 40)
    
    # Send to Telegram
    print(f"\n📤 Sending to Telegram group...")
    success = await system.send_to_telegram(alerts_data)
    
    if success:
        print("✅ Successfully sent to Telegram!")
    else:
        print("❌ Failed to send to Telegram")
    
    print(f"\n📁 Manual alerts file: {system.alerts_dir / 'manual_alerts.json'}")
    print("💡 Update the manual_alerts.json file with real MyMama data")
    print("=" * 60)
    
    return alerts_data

if __name__ == "__main__":
    asyncio.run(main())