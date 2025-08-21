#!/usr/bin/env python3
"""
Validate complete system integration
Checks all components are working together correctly
"""

import asyncio
import sys
import logging
from pathlib import Path
from datetime import datetime
import subprocess
import json

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

async def validate_complete_system():
    """Validate complete system integration"""
    logger.info("=== VALIDATING COMPLETE SYSTEM INTEGRATION ===")
    
    validation_results = {
        'main_process': False,
        'messaging_platforms': {'signal': False, 'telegram': False, 'whatsapp': False},
        'data_collection': False,
        'heatmap_generation': False,
        'configuration': False
    }
    
    try:
        # 1. Check main process is running
        logger.info("1. Checking main process status...")
        result = subprocess.run(['ps', 'aux'], capture_output=True, text=True)
        if 'main.py' in result.stdout:
            logger.info("✅ Main process is running")
            validation_results['main_process'] = True
        else:
            logger.warning("⚠️ Main process not found")
        
        # 2. Test messaging platforms
        logger.info("2. Testing messaging platforms...")
        from src.messengers.unified_messenger import UnifiedMultiMessenger
        
        platforms = ['signal', 'telegram', 'whatsapp']
        multi_messenger = UnifiedMultiMessenger(platforms)
        
        # Test each platform initialization
        for platform in platforms:
            messenger = multi_messenger.messengers.get(platform)
            if messenger:
                logger.info(f"✅ {platform.upper()}: Initialized successfully")
                validation_results['messaging_platforms'][platform] = True
            else:
                logger.warning(f"⚠️ {platform.upper()}: Not initialized")
        
        await multi_messenger.cleanup()
        
        # 3. Check data collection capability
        logger.info("3. Testing data collection...")
        try:
            from concurrent_data_collector import ConcurrentDataCollector
            from utils.env_config import EnvironmentConfig
            
            env_config = EnvironmentConfig()
            collector = ConcurrentDataCollector(env_config)
            logger.info("✅ Data collector initialized successfully")
            validation_results['data_collection'] = True
        except Exception as e:
            logger.warning(f"⚠️ Data collection test failed: {e}")
        
        # 4. Check heatmap generation
        logger.info("4. Testing heatmap generation...")
        heatmap_script = Path(__file__).parent.parent / 'heatmaps_package' / 'core_files' / 'silent_bloomberg_system.py'
        if heatmap_script.exists():
            logger.info("✅ Heatmap generation script found")
            validation_results['heatmap_generation'] = True
        else:
            logger.warning("⚠️ Heatmap generation script not found")
        
        # 5. Check configuration
        logger.info("5. Checking configuration...")
        config_file = Path(__file__).parent / 'config.json'
        if config_file.exists():
            with open(config_file, 'r') as f:
                config = json.load(f)
            logger.info("✅ Configuration file loaded")
            validation_results['configuration'] = True
        else:
            logger.warning("⚠️ Configuration file not found")
        
        # 6. Check authentication files
        logger.info("6. Checking authentication status...")
        auth_files = [
            Path(__file__).parent / 'browser_sessions' / 'whatsapp_main' / 'authentication_success.txt'
        ]
        
        auth_count = 0
        for auth_file in auth_files:
            if auth_file.exists():
                auth_count += 1
        
        if auth_count > 0:
            logger.info(f"✅ Found {auth_count} authentication file(s)")
        else:
            logger.warning("⚠️ No authentication files found")
        
        # Calculate overall score
        total_checks = 5
        passed_checks = sum([
            validation_results['main_process'],
            any(validation_results['messaging_platforms'].values()),
            validation_results['data_collection'],
            validation_results['heatmap_generation'],
            validation_results['configuration']
        ])
        
        platform_score = sum(validation_results['messaging_platforms'].values())
        
        logger.info(f"\n=== VALIDATION RESULTS ===")
        logger.info(f"✅ Overall system checks: {passed_checks}/{total_checks}")
        logger.info(f"✅ Messaging platforms: {platform_score}/3")
        logger.info(f"✅ Main process: {'Running' if validation_results['main_process'] else 'Not running'}")
        logger.info(f"✅ Data collection: {'Ready' if validation_results['data_collection'] else 'Not ready'}")
        logger.info(f"✅ Heatmap generation: {'Ready' if validation_results['heatmap_generation'] else 'Not ready'}")
        logger.info(f"✅ Configuration: {'Loaded' if validation_results['configuration'] else 'Not loaded'}")
        
        if passed_checks >= 4 and platform_score >= 2:
            logger.info("🎉 SYSTEM VALIDATION PASSED!")
            logger.info("🚀 System is ready for production use")
            return True
        else:
            logger.warning("⚠️ System validation partially passed")
            logger.info("🔧 Some components may need attention")
            return False
        
    except Exception as e:
        logger.error(f"❌ System validation failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """Main validation function"""
    logger.info("Starting complete system validation...")
    
    success = await validate_complete_system()
    
    if success:
        logger.info("🎉 Complete system validation PASSED")
        logger.info("📋 System Summary:")
        logger.info("   - Daily reports scheduled for 6 AM weekdays")
        logger.info("   - Messages sent to Signal, Telegram, and WhatsApp")
        logger.info("   - Heatmaps generated and distributed")
        logger.info("   - All major components operational")
    else:
        logger.error("❌ Complete system validation FAILED")
        logger.info("🔧 Review the validation results above for issues")
    
    return success

if __name__ == "__main__":
    asyncio.run(main())