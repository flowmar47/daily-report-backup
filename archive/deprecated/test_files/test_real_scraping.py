#!/usr/bin/env python3
"""
Test real scraping with proper authentication
"""
import asyncio
import logging
import json
from enhanced_browserbase_scraper import EnhancedBrowserBaseScraper
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_real_scraping():
    """Test real scraping with authentication"""
    try:
        logger.info("🚀 Starting real data scraping test...")
        
        # Initialize scraper
        scraper = EnhancedBrowserBaseScraper()
        
        # Perform scraping
        result = await scraper.scrape_data()
        
        # Check results
        if result.get('success'):
            logger.info("✅ Scraping succeeded!")
            
            # Check what data we got
            forex_alerts = result.get('forex_alerts', [])
            options_alerts = result.get('options_alerts', [])
            swing_trades = result.get('swing_trades', [])
            day_trades = result.get('day_trades', [])
            
            logger.info(f"📊 Data Summary:")
            logger.info(f"  - Forex alerts: {len(forex_alerts)}")
            logger.info(f"  - Options alerts: {len(options_alerts)}")
            logger.info(f"  - Swing trades: {len(swing_trades)}")
            logger.info(f"  - Day trades: {len(day_trades)}")
            
            # Save full result
            with open('real_scraped_data.json', 'w') as f:
                json.dump(result, f, indent=2)
            logger.info("💾 Saved to real_scraped_data.json")
            
            # If we have data, send a test report
            if forex_alerts or options_alerts or swing_trades or day_trades:
                logger.info("\n🎯 Sending real data to groups...")
                
                from main import DailyReportAutomation
                automation = DailyReportAutomation()
                
                # Generate report
                report = await automation.generate_report(result)
                
                if report:
                    logger.info(f"📝 Generated report ({len(report)} chars)")
                    
                    # Generate heatmaps
                    logger.info("🎨 Generating heatmaps...")
                    heatmap_files = []
                    try:
                        import subprocess
                        import sys
                        from pathlib import Path
                        
                        heatmap_result = subprocess.run([
                            sys.executable, 
                            "../heatmaps_package/core_files/bloomberg_report_final.py"
                        ], capture_output=True, text=True, cwd=".")
                        
                        if heatmap_result.returncode == 0:
                            logger.info("✅ Heatmaps generated")
                            
                            # Find heatmap files
                            heatmap_dir = Path("../heatmaps_package/core_files/reports")
                            if heatmap_dir.exists():
                                report_dirs = [d for d in heatmap_dir.iterdir() if d.is_dir() and d.name.startswith('202')]
                                if report_dirs:
                                    latest_report_dir = sorted(report_dirs, key=lambda x: x.name)[-1]
                                    
                                    categorical_file = latest_report_dir / "categorical_heatmap.png"
                                    forex_file = latest_report_dir / "forex_pairs_heatmap.png"
                                    
                                    if categorical_file.exists():
                                        heatmap_files.append(str(categorical_file))
                                    if forex_file.exists():
                                        heatmap_files.append(str(forex_file))
                    except Exception as e:
                        logger.warning(f"⚠️ Heatmap generation failed: {e}")
                    
                    # Send to Telegram
                    logger.info("📱 Sending to Telegram...")
                    telegram_success = await automation.send_telegram_report(report)
                    
                    if telegram_success and heatmap_files:
                        # Send heatmaps to Telegram
                        for heatmap_file in heatmap_files:
                            try:
                                import os
                                import aiohttp
                                from pathlib import Path
                                
                                bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
                                group_id = os.getenv('TELEGRAM_GROUP_ID')
                                
                                url = f"https://api.telegram.org/bot{bot_token}/sendPhoto"
                                
                                with open(heatmap_file, 'rb') as photo:
                                    data = aiohttp.FormData()
                                    data.add_field('chat_id', group_id)
                                    data.add_field('photo', photo, filename=Path(heatmap_file).name)
                                    data.add_field('caption', f"📊 {Path(heatmap_file).stem.replace('_', ' ').title()}")
                                    
                                    async with aiohttp.ClientSession() as session:
                                        async with session.post(url, data=data) as response:
                                            if response.status == 200:
                                                logger.info(f"📊 Sent heatmap: {Path(heatmap_file).name}")
                            except Exception as e:
                                logger.warning(f"⚠️ Failed to send heatmap: {e}")
                    
                    # Send to Signal
                    logger.info("📡 Sending to Signal...")
                    signal_success = await automation.send_signal_report(report)
                    
                    # Summary
                    logger.info("=" * 60)
                    logger.info("📋 REAL DATA SCRAPING SUMMARY")
                    logger.info("=" * 60)
                    logger.info(f"🔍 Scraped successfully: ✅")
                    logger.info(f"📊 Total alerts: {len(forex_alerts) + len(options_alerts) + len(swing_trades) + len(day_trades)}")
                    logger.info(f"📝 Report generated: ✅")
                    logger.info(f"🎨 Heatmaps: {len(heatmap_files)} generated")
                    logger.info(f"📱 Telegram: {'✅' if telegram_success else '❌'}")
                    logger.info(f"📡 Signal: {'✅' if signal_success else '❌'}")
                    logger.info("=" * 60)
                    
                    # Print report preview
                    logger.info("📄 Report Preview:")
                    logger.info("-" * 40)
                    print(report[:1000] + "..." if len(report) > 1000 else report)
                
            else:
                logger.warning("⚠️ No data found to send")
                
                # Check what page content we got
                page_text = result.get('page_text', '')
                if page_text:
                    logger.info("📄 Page content preview:")
                    print(page_text[:500])
                    
                    # Save for debugging
                    with open('debug_page_content.txt', 'w') as f:
                        f.write(page_text)
                    logger.info("💾 Saved debug content to debug_page_content.txt")
                
        else:
            logger.error(f"❌ Scraping failed: {result.get('error')}")
            
    except Exception as e:
        logger.error(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_real_scraping())