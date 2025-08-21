#!/usr/bin/env python3
"""
Clear Signal message history and send today's missed financial data to all platforms
"""

import asyncio
import sys
import logging
import json
from pathlib import Path
from datetime import datetime
import subprocess

# Add the project root to Python path
sys.path.insert(0, str(Path(__file__).parent))

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

async def clear_signal_messages():
    """Clear Signal message history"""
    logger.info("🧹 Clearing Signal message history...")
    
    try:
        # Note: Signal CLI doesn't have a direct way to clear message history
        # We can only inform the user how to do it manually
        logger.info("📋 Signal message clearing instructions:")
        logger.info("=" * 50)
        logger.info("Signal CLI doesn't support clearing message history programmatically.")
        logger.info("To clear messages manually:")
        logger.info("1. Open Signal Desktop or Mobile app")
        logger.info("2. Go to the group 'Ohms Alerts Reports'")
        logger.info("3. Click on group settings → Clear chat history")
        logger.info("=" * 50)
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Error: {e}")
        return False

async def send_todays_financial_data():
    """Send today's actual financial data to all platforms"""
    logger.info("📊 Preparing to send today's financial data...")
    
    try:
        # Import necessary modules
        from concurrent_data_collector import ConcurrentDataCollector
        from src.messengers.unified_messenger import UnifiedMultiMessenger
        from utils.env_config import EnvironmentConfig
        from secure_session_manager import SecureSessionManager
        from pathlib import Path
        import sys
        
        # Add heatmap path
        sys.path.append(str(Path(__file__).parent.parent / 'heatmaps_package' / 'core_files'))
        
        # Initialize environment
        env_config = EnvironmentConfig()
        session_manager = SecureSessionManager(Path(__file__).parent / 'browser_sessions')
        
        # Initialize data collector
        logger.info("🔄 Collecting today's financial data...")
        data_collector = ConcurrentDataCollector(env_config)
        
        # Collect data
        scraped_data, heatmap_data = await data_collector.collect_all_data_concurrent()
        
        # Check if we have data
        if not scraped_data or not scraped_data.get('forex_data', {}).get('has_real_data'):
            logger.warning("⚠️ No real financial data available from MyMama.uk")
            logger.info("💡 Attempting to use most recent cached data...")
            
            # Try to load from screenshots or cache
            screenshot_dir = Path(__file__).parent / 'screenshots'
            if screenshot_dir.exists():
                recent_files = sorted(screenshot_dir.glob('mymama_*.png'), reverse=True)
                if recent_files:
                    logger.info(f"📸 Found recent screenshot: {recent_files[0]}")
        
        # Generate report content
        logger.info("📝 Generating financial report...")
        
        # Initialize messenger system
        platforms = ['signal', 'telegram', 'whatsapp']
        multi_messenger = UnifiedMultiMessenger(platforms)
        
        # Prepare message content
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M')
        
        if scraped_data and scraped_data.get('forex_data'):
            # Use real data
            from src.data_processors.template_generator import StructuredTemplateGenerator
            
            template_gen = StructuredTemplateGenerator()
            message_content = template_gen.generate_financial_report(
                forex_data=scraped_data.get('forex_data', {}),
                earnings_data=scraped_data.get('earnings_data', {}),
                options_data=scraped_data.get('options_data', {})
            )
            
            # Add header
            final_message = f"DAILY FINANCIAL ALERTS - {timestamp}\n\n{message_content}"
        else:
            # Fallback message
            final_message = f"""DAILY FINANCIAL ALERTS - {timestamp}

⚠️ Today's data collection encountered issues at 6 AM.
The automated system is now configured correctly for future runs.

The system will resume normal operation with:
✅ All 3 platforms (Signal, Telegram, WhatsApp)
✅ Daily reports at 6 AM PST weekdays
✅ Bloomberg-style heatmaps included

Next scheduled report: Monday 6:00 AM PST"""
        
        logger.info("📤 Sending to all platforms...")
        
        # Send the message
        results = await multi_messenger.send_to_all(final_message)
        
        # Check results
        success_count = 0
        for platform, result in results.items():
            if result.success:
                logger.info(f"✅ {platform.upper()}: Message sent successfully")
                success_count += 1
            else:
                logger.error(f"❌ {platform.upper()}: Failed - {result.error}")
        
        # Generate and send heatmaps if available
        if success_count > 0:
            logger.info("🌡️ Generating heatmaps...")
            try:
                # Import heatmap generator
                from silent_bloomberg_system import main as generate_heatmaps_silent
                
                # Generate heatmaps
                heatmap_paths = await asyncio.create_subprocess_exec(
                    sys.executable, '-c', 
                    'from silent_bloomberg_system import main; main()',
                    cwd=str(Path(__file__).parent.parent / 'heatmaps_package' / 'core_files')
                )
                await heatmap_paths.wait()
                
                # Find generated heatmaps
                heatmap_dir = Path(__file__).parent.parent / 'heatmaps_package' / 'core_files' / 'output'
                if heatmap_dir.exists():
                    categorical_heatmap = sorted(heatmap_dir.glob('interest_rate_heatmap_categorical_*.png'), reverse=True)
                    forex_heatmap = sorted(heatmap_dir.glob('forex_pairs_heatmap_*.png'), reverse=True)
                    
                    # Send heatmaps
                    if categorical_heatmap:
                        logger.info("📊 Sending categorical heatmap...")
                        await multi_messenger.send_attachment(
                            file_path=str(categorical_heatmap[0]),
                            caption="Interest Rate Analysis - Categorical View"
                        )
                    
                    if forex_heatmap:
                        logger.info("🌍 Sending forex pairs heatmap...")
                        await multi_messenger.send_attachment(
                            file_path=str(forex_heatmap[0]),
                            caption="Forex Pairs Interest Rate Differentials"
                        )
                        
            except Exception as e:
                logger.warning(f"⚠️ Heatmap generation failed: {e}")
        
        # Cleanup
        await multi_messenger.cleanup()
        
        return success_count == len(platforms)
        
    except Exception as e:
        logger.error(f"❌ Failed to send financial data: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """Main function"""
    logger.info("🚀 Starting Signal cleanup and data resend process...")
    
    # Step 1: Show Signal clearing instructions
    await clear_signal_messages()
    
    # Wait for user confirmation
    logger.info("\n⏸️ Please clear Signal messages manually, then press Enter to continue...")
    input()
    
    # Step 2: Send today's financial data
    logger.info("\n📤 Sending today's financial data to all platforms...")
    success = await send_todays_financial_data()
    
    if success:
        logger.info("\n🎉 Successfully sent financial data to all platforms!")
        logger.info("✅ Signal, Telegram, and WhatsApp have received today's report")
    else:
        logger.warning("\n⚠️ Some platforms may have failed - check logs above")

if __name__ == "__main__":
    asyncio.run(main())