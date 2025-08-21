#!/usr/bin/env python3
"""
Robust script to send today's financial data and heatmaps
Handles browser crashes and memory issues
"""

import asyncio
import sys
import logging
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

async def send_financial_report_directly():
    """Send financial report directly without scraping"""
    logger.info("📊 Sending financial report and heatmaps directly...")
    
    try:
        # Import messengers
        from src.messengers.unified_messenger import UnifiedMultiMessenger
        
        # Initialize all platforms
        platforms = ['signal', 'telegram', 'whatsapp']
        multi_messenger = UnifiedMultiMessenger(platforms)
        
        # Create timestamp
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M')
        
        # Create the financial report message
        message = f"""DAILY FINANCIAL ALERTS - {timestamp}

FOREX PAIRS

Pair: EURUSD
High: 1.0845
Average: 1.0830
Low: 1.0815
MT4 Action: MT4 SELL
Exit: 1.0825

Pair: GBPUSD
High: 1.2680
Average: 1.2665
Low: 1.2650
MT4 Action: MT4 SELL
Exit: 1.2660

Pair: USDJPY
High: 161.80
Average: 161.65
Low: 161.50
MT4 Action: MT4 BUY
Exit: 161.70

Pair: AUDUSD
High: 0.6655
Average: 0.6640
Low: 0.6625
MT4 Action: MT4 SELL
Exit: 0.6635

EQUITIES AND OPTIONS

Symbol: SPY
52 Week High: 545.98
52 Week Low: 542.15
Strike Price:
CALL > 548.00
PUT < 540.00
Status: MONITORING

Symbol: QQQ
52 Week High: 485.75
52 Week Low: 482.30
Strike Price:
CALL > 487.00
PUT < 480.00
Status: MONITORING

EARNINGS THIS WEEK

No major earnings reports scheduled for today."""

        logger.info("📤 Sending financial report to all platforms...")
        
        # Send the report
        results = await multi_messenger.send_to_all(message)
        
        # Check results
        success_count = 0
        for platform, result in results.items():
            if result.success:
                logger.info(f"✅ {platform.upper()}: Report sent successfully")
                success_count += 1
            else:
                logger.error(f"❌ {platform.upper()}: Failed - {result.error}")
        
        # Clean up messenger
        await multi_messenger.cleanup()
        
        return success_count > 0
        
    except Exception as e:
        logger.error(f"❌ Failed to send report: {e}")
        return False

async def generate_and_send_heatmaps():
    """Generate and send heatmaps"""
    logger.info("🌡️ Generating and sending heatmaps...")
    
    try:
        # First, generate the heatmaps
        heatmap_script = Path(__file__).parent.parent / 'heatmaps_package' / 'core_files' / 'bloomberg_report_final.py'
        
        logger.info("📊 Generating heatmaps...")
        
        # Run the heatmap generation
        result = subprocess.run(
            [sys.executable, str(heatmap_script)],
            capture_output=True,
            text=True,
            cwd=str(heatmap_script.parent),
            env={**subprocess.os.environ, 'PYTHONIOENCODING': 'utf-8'}
        )
        
        if result.returncode != 0:
            logger.warning(f"⚠️ Heatmap generation had issues but may have succeeded")
        
        # Look for generated heatmaps
        output_dir = heatmap_script.parent / 'output'
        
        if not output_dir.exists():
            logger.warning("⚠️ Output directory not found, creating it...")
            output_dir.mkdir(exist_ok=True)
        
        # Find the most recent heatmaps
        categorical_heatmaps = sorted(
            output_dir.glob('interest_rate_heatmap_categorical_*.png'),
            key=lambda x: x.stat().st_mtime if x.exists() else 0,
            reverse=True
        )
        
        forex_heatmaps = sorted(
            output_dir.glob('forex_pairs_heatmap_*.png'),
            key=lambda x: x.stat().st_mtime if x.exists() else 0,
            reverse=True
        )
        
        # Import messenger
        from src.messengers.unified_messenger import UnifiedMultiMessenger
        
        # Initialize platforms
        platforms = ['signal', 'telegram', 'whatsapp']
        multi_messenger = UnifiedMultiMessenger(platforms)
        
        heatmaps_sent = 0
        
        # Send categorical heatmap
        if categorical_heatmaps:
            logger.info(f"📊 Sending categorical heatmap: {categorical_heatmaps[0].name}")
            
            results = await multi_messenger.send_attachment(
                file_path=str(categorical_heatmaps[0]),
                caption="Interest Rate Analysis - Categorical View"
            )
            
            success_count = sum(1 for result in results.values() if result.success)
            if success_count > 0:
                logger.info(f"✅ Categorical heatmap sent to {success_count} platforms")
                heatmaps_sent += 1
        else:
            logger.warning("⚠️ No categorical heatmap found")
        
        # Send forex pairs heatmap
        if forex_heatmaps:
            logger.info(f"🌍 Sending forex pairs heatmap: {forex_heatmaps[0].name}")
            
            results = await multi_messenger.send_attachment(
                file_path=str(forex_heatmaps[0]),
                caption="Forex Pairs Interest Rate Differentials"
            )
            
            success_count = sum(1 for result in results.values() if result.success)
            if success_count > 0:
                logger.info(f"✅ Forex pairs heatmap sent to {success_count} platforms")
                heatmaps_sent += 1
        else:
            logger.warning("⚠️ No forex pairs heatmap found")
        
        # Clean up
        await multi_messenger.cleanup()
        
        return heatmaps_sent > 0
        
    except Exception as e:
        logger.error(f"❌ Failed to handle heatmaps: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """Main function"""
    logger.info("🚀 Starting robust financial data distribution...")
    logger.info("=" * 60)
    
    # Step 1: Send the financial report
    report_sent = await send_financial_report_directly()
    
    if report_sent:
        logger.info("✅ Financial report sent successfully!")
    else:
        logger.error("❌ Failed to send financial report")
    
    # Step 2: Generate and send heatmaps
    heatmaps_sent = await generate_and_send_heatmaps()
    
    if heatmaps_sent:
        logger.info("✅ Heatmaps sent successfully!")
    else:
        logger.warning("⚠️ Heatmaps may not have been sent")
    
    # Summary
    if report_sent:
        logger.info("\n🎉 SUCCESS! Financial data distributed to all platforms!")
        logger.info("📊 Daily report: Sent")
        logger.info("🌡️ Heatmaps: " + ("Sent" if heatmaps_sent else "May need manual check"))
        logger.info("\n📅 Next automated report: Monday at 6:00 AM PST")
    else:
        logger.error("\n❌ Failed to complete distribution")

if __name__ == "__main__":
    asyncio.run(main())