#!/usr/bin/env python3
"""
Critical Dependencies Update Script
Updates only security-critical dependencies to avoid breaking changes
"""

import subprocess
import sys
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

def update_critical_dependencies():
    """Update only critical security dependencies"""
    
    # Critical security updates
    critical_updates = [
        'cryptography>=42.0.8',  # Security fixes
        'requests>=2.31.0',      # Security fixes
        'certifi>=2025.6.15',   # Latest certificate bundle
        'urllib3>=1.26.18',     # Security fixes
        'python-dotenv>=1.0.1'  # Latest stable
    ]
    
    logger.info("🔒 Updating critical security dependencies...")
    
    success_count = 0
    for package in critical_updates:
        try:
            logger.info(f"Updating {package}...")
            subprocess.run([
                sys.executable, '-m', 'pip', 'install', '--upgrade', package
            ], check=True, capture_output=True)
            logger.info(f"✅ Updated {package}")
            success_count += 1
        except subprocess.CalledProcessError as e:
            logger.error(f"❌ Failed to update {package}: {e}")
    
    logger.info(f"🎉 Updated {success_count}/{len(critical_updates)} critical packages")
    return success_count == len(critical_updates)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    
    success = update_critical_dependencies()
    
    if success:
        logger.info("✅ Critical dependency updates completed successfully")
        print("✅ All critical dependencies updated")
    else:
        logger.error("❌ Some critical dependency updates failed")
        print("❌ Some updates failed - check logs")
    
    exit(0 if success else 1)