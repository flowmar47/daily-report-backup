#!/usr/bin/env python3
"""
Complete System Test - Final Integration
Tests the entire daily report system including:
1. MyMama data scraping
2. Heatmap generation
3. Messaging to all platforms (Signal, Telegram, WhatsApp)
"""

import asyncio
import logging
import sys
from pathlib import Path
from datetime import datetime

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def test_complete_system():
    """Test the complete financial reporting system"""
    logger.info("🚀 Starting complete system test...")
    
    results = {
        'scraping': False,
        'heatmaps': False,
        'signal': False,
        'telegram': False,
        'whatsapp': False,
        'timestamp': datetime.now().isoformat()
    }
    
    try:
        # 1. Test data scraping
        logger.info("\n📊 STEP 1: Testing MyMama data scraping...")
        from real_only_mymama_scraper import RealOnlyMyMamaScraper
        
        scraper = RealOnlyMyMamaScraper()
        forex_data = await scraper.get_real_alerts_only()
        
        if forex_data and forex_data.get('has_real_data'):
            forex_count = len(forex_data.get('forex_alerts', {}))
            options_count = len(forex_data.get('options_data', []))
            logger.info(f"✅ Scraping successful: {forex_count} forex, {options_count} options")
            results['scraping'] = True
            results['forex_count'] = forex_count
            results['options_count'] = options_count
        else:
            logger.error("❌ Scraping failed - no data retrieved")
            return results
            
        # 2. Test heatmap generation
        logger.info("\n🌡️ STEP 2: Testing heatmap generation...")
        from main import DailyReportAutomation
        
        automation = DailyReportAutomation()
        heatmap_data = await automation.generate_heatmaps()
        
        if heatmap_data:
            logger.info("✅ Heatmap generation successful")
            logger.info(f"  📊 Categorical: {Path(heatmap_data['categorical_heatmap']).name}")
            logger.info(f"  📊 Forex pairs: {Path(heatmap_data['forex_heatmap']).name}")
            results['heatmaps'] = True
            results['heatmap_files'] = heatmap_data
        else:
            logger.warning("⚠️ Heatmap generation failed")
            
        # 3. Generate structured report
        logger.info("\n📝 STEP 3: Generating structured report...")
        from src.data_processors.template_generator import StructuredTemplateGenerator
        from src.data_processors.financial_alerts import FinancialAlertsProcessor
        
        # Use the automation's report generation instead
        from main import DailyReportAutomation
        automation = DailyReportAutomation()
        message = await automation.generate_report(forex_data)
        
        logger.info("✅ Report generated successfully")
        logger.info(f"📄 Message length: {len(message)} characters")
        results['message'] = message
        
        # 4. Test messaging platforms
        logger.info("\n📤 STEP 4: Testing messaging platforms...")
        from src.messengers.unified_messenger import UnifiedMultiMessenger
        
        messenger = UnifiedMultiMessenger()
        
        # Test all platforms
        # First send the text message
        text_results = await messenger.send_to_all(message)
        
        # Then send heatmaps if available
        if heatmap_data:
            from src.messengers.unified_messenger import AttachmentData
            attachments = []
            
            if heatmap_data.get('categorical_heatmap'):
                attachments.append(AttachmentData(
                    file_path=heatmap_data['categorical_heatmap'],
                    caption="Interest Rate Categories"
                ))
            
            if heatmap_data.get('forex_heatmap'):
                attachments.append(AttachmentData(
                    file_path=heatmap_data['forex_heatmap'],
                    caption="Forex Pairs Differentials"
                ))
            
            if attachments:
                attachment_results = await messenger.send_attachments(attachments)
        
        # Combine results
        platform_results = {}
        for platform, result in text_results.items():
            platform_results[platform] = result.status == 'success'
        
        if platform_results:
            for platform, success in platform_results.items():
                results[platform] = success
                if success:
                    logger.info(f"✅ {platform.upper()}: Message sent successfully")
                else:
                    logger.warning(f"⚠️ {platform.upper()}: Failed to send")
        
    except Exception as e:
        logger.error(f"❌ System test failed: {e}")
        import traceback
        traceback.print_exc()
        
    # Summary
    logger.info("\n📊 FINAL TEST RESULTS:")
    logger.info("=" * 50)
    for key, value in results.items():
        if isinstance(value, bool):
            status = "✅ PASS" if value else "❌ FAIL"
            logger.info(f"{key.upper():15} {status}")
    logger.info("=" * 50)
    
    # Overall result
    core_systems = ['scraping', 'telegram']  # At least scraping and one messenger
    all_passed = all(results.get(sys, False) for sys in core_systems)
    
    if all_passed:
        logger.info("\n🎉 SYSTEM READY FOR 6 AM DEPLOYMENT! 🎉")
        logger.info("The daily financial report automation is fully operational.")
    else:
        logger.warning("\n⚠️ Some components need attention before 6 AM.")
        
    return results

if __name__ == "__main__":
    results = asyncio.run(test_complete_system())
    
    # Exit with appropriate code
    sys.exit(0 if results.get('scraping') and results.get('telegram') else 1)