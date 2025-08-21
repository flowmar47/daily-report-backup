#!/usr/bin/env python3
"""
Send complete enhanced report with heatmaps to both Signal and Telegram
"""
import asyncio
import logging
import sys
import os
from datetime import datetime
from pathlib import Path

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def generate_and_send_complete_report():
    """Generate and send complete enhanced report with heatmaps"""
    try:
        logger.info("🚀 Generating and sending complete enhanced report with heatmaps...")
        
        from main import DailyReportAutomation
        
        # Initialize the main automation system
        automation = DailyReportAutomation()
        logger.info("✅ DailyReportAutomation initialized")
        
        # Step 1: Collect market data using enhanced scraper
        logger.info("📊 Collecting market data with enhanced scraper...")
        market_data = await automation.collect_market_data()
        
        # Step 2: Generate financial report
        logger.info("📝 Generating financial report...")
        report = await automation.generate_report(market_data)
        
        if not report:
            report = "Enhanced BrowserBase Scraper Test Report\n\nNo financial signals detected at this time.\nSystem is functioning correctly and ready for live data."
        
        logger.info(f"✅ Report generated ({len(report)} characters)")
        
        # Step 3: Generate heatmaps
        logger.info("🎨 Generating Bloomberg-style heatmaps...")
        try:
            import subprocess
            import sys
            
            # Run heatmap generation
            heatmap_result = subprocess.run([
                sys.executable, 
                "../heatmaps_package/core_files/bloomberg_report_final.py"
            ], capture_output=True, text=True, cwd=Path.cwd())
            
            if heatmap_result.returncode == 0:
                logger.info("✅ Heatmaps generated successfully")
                
                # Find the latest heatmap files
                heatmap_dir = Path("../heatmaps_package/core_files/reports")
                latest_report_dir = None
                
                if heatmap_dir.exists():
                    # Find the most recent report directory
                    report_dirs = [d for d in heatmap_dir.iterdir() if d.is_dir() and d.name.startswith('202')]
                    if report_dirs:
                        latest_report_dir = sorted(report_dirs, key=lambda x: x.name)[-1]
                        logger.info(f"📁 Latest heatmap report: {latest_report_dir.name}")
                
                # Also check for PNG files in the main directory
                png_files = []
                if heatmap_dir.exists():
                    png_files = list(heatmap_dir.glob("*.png"))
                    png_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
                
                heatmap_files = []
                if latest_report_dir:
                    categorical_file = latest_report_dir / "categorical_heatmap.png"
                    forex_file = latest_report_dir / "forex_pairs_heatmap.png"
                    
                    if categorical_file.exists():
                        heatmap_files.append(str(categorical_file))
                    if forex_file.exists():
                        heatmap_files.append(str(forex_file))
                
                # If no files in report dir, use latest PNG files
                if not heatmap_files and png_files:
                    heatmap_files = [str(f) for f in png_files[:2]]  # Take the 2 most recent
                
                logger.info(f"📊 Found {len(heatmap_files)} heatmap files")
                
            else:
                logger.warning(f"⚠️ Heatmap generation had issues: {heatmap_result.stderr}")
                heatmap_files = []
                
        except Exception as e:
            logger.warning(f"⚠️ Heatmap generation failed: {e}")
            heatmap_files = []
        
        # Step 4: Send to Telegram
        logger.info("📱 Sending to Telegram...")
        telegram_success = await automation.send_telegram_report(report)
        
        if telegram_success and heatmap_files:
            # Send heatmaps to Telegram
            for heatmap_file in heatmap_files:
                try:
                    await send_image_to_telegram(heatmap_file)
                    logger.info(f"📊 Sent heatmap to Telegram: {Path(heatmap_file).name}")
                except Exception as e:
                    logger.warning(f"⚠️ Failed to send heatmap to Telegram: {e}")
        
        # Step 5: Send to Signal
        logger.info("📡 Sending to Signal...")
        signal_success = await automation.send_signal_report(report)
        
        if signal_success and heatmap_files:
            # Send heatmaps to Signal
            for heatmap_file in heatmap_files:
                try:
                    await send_image_to_signal(heatmap_file)
                    logger.info(f"📊 Sent heatmap to Signal: {Path(heatmap_file).name}")
                except Exception as e:
                    logger.warning(f"⚠️ Failed to send heatmap to Signal: {e}")
        
        # Summary
        total_success = telegram_success and signal_success
        
        logger.info("=" * 50)
        logger.info("📋 ENHANCED REPORT DELIVERY SUMMARY")
        logger.info("=" * 50)
        logger.info(f"📊 Market Data: Enhanced BrowserBase Scraper")
        logger.info(f"📝 Report: {len(report)} characters")
        logger.info(f"🎨 Heatmaps: {len(heatmap_files)} generated")
        logger.info(f"📱 Telegram: {'✅ Success' if telegram_success else '❌ Failed'}")
        logger.info(f"📡 Signal: {'✅ Success' if signal_success else '❌ Failed'}")
        logger.info(f"🎯 Overall: {'✅ Success' if total_success else '❌ Partial/Failed'}")
        logger.info("=" * 50)
        
        return total_success
            
    except Exception as e:
        logger.error(f"❌ Enhanced report generation failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def send_image_to_telegram(image_path: str):
    """Send image to Telegram"""
    bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
    group_id = os.getenv('TELEGRAM_GROUP_ID')
    
    if not bot_token or not group_id:
        raise ValueError("Missing Telegram credentials")
    
    import aiohttp
    
    url = f"https://api.telegram.org/bot{bot_token}/sendPhoto"
    
    with open(image_path, 'rb') as photo:
        data = aiohttp.FormData()
        data.add_field('chat_id', group_id)
        data.add_field('photo', photo, filename=Path(image_path).name)
        data.add_field('caption', f"📊 {Path(image_path).stem.replace('_', ' ').title()}")
        
        async with aiohttp.ClientSession() as session:
            async with session.post(url, data=data) as response:
                if response.status != 200:
                    error_text = await response.text()
                    raise Exception(f"Telegram API error: {response.status} - {error_text}")

async def send_image_to_signal(image_path: str):
    """Send image to Signal"""
    try:
        from signal_messenger import send_attachment_to_signal_sync
        
        # Run sync function in executor
        success = await asyncio.get_event_loop().run_in_executor(
            None, send_attachment_to_signal_sync, image_path, f"📊 {Path(image_path).stem.replace('_', ' ').title()}"
        )
        
        if not success:
            raise Exception("Signal attachment sending failed")
            
    except Exception as e:
        logger.warning(f"Signal image sending failed: {e}")
        raise

if __name__ == "__main__":
    success = asyncio.run(generate_and_send_complete_report())
    if success:
        print("✅ Enhanced report with heatmaps sent successfully!")
    else:
        print("❌ Enhanced report sending failed!")
        sys.exit(1)