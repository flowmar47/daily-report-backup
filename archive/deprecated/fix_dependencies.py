#!/usr/bin/env python3
"""
Fixed Dependency Update Script
Properly updates dependencies within virtual environment with security focus
"""

import subprocess
import sys
import logging
import os
from pathlib import Path

logger = logging.getLogger(__name__)

def ensure_virtual_env():
    """Ensure we're running in the virtual environment"""
    venv_path = Path('venv')
    if not venv_path.exists():
        logger.error("Virtual environment not found!")
        return False
    
    # Check if we're in virtual environment
    if 'VIRTUAL_ENV' not in os.environ:
        logger.error("Virtual environment not activated!")
        logger.info("Please run: source venv/bin/activate")
        return False
    
    logger.info(f"✅ Running in virtual environment: {os.environ['VIRTUAL_ENV']}")
    return True

def update_security_critical_packages():
    """Update packages with known security vulnerabilities"""
    
    security_updates = [
        # Critical security packages
        ('cryptography', '42.0.8'),  # CVE fixes
        ('requests', '2.32.4'),      # Security patches
        ('urllib3', '2.2.2'),       # Security fixes
        ('certifi', '2024.8.30'),   # Certificate updates
        ('pillow', '10.4.0'),       # Security fixes
        
        # Important functionality packages
        ('python-dotenv', '1.0.1'), # Latest stable
        ('beautifulsoup4', '4.12.3'), # Latest stable
        ('lxml', '5.2.2'),          # Security fixes
        ('httpx', '0.27.0'),        # Latest stable
        ('tenacity', '8.5.0')       # Latest stable
    ]
    
    logger.info("🔒 Updating security-critical packages...")
    
    success_count = 0
    failed_packages = []
    
    for package_name, version in security_updates:
        try:
            logger.info(f"Updating {package_name} to {version}...")
            
            # Try to update to specific version first
            result = subprocess.run([
                sys.executable, '-m', 'pip', 'install', f'{package_name}=={version}'
            ], capture_output=True, text=True, timeout=300)
            
            if result.returncode == 0:
                logger.info(f"✅ Updated {package_name} to {version}")
                success_count += 1
            else:
                # Try latest version if specific version fails
                logger.warning(f"Specific version failed for {package_name}, trying latest...")
                result = subprocess.run([
                    sys.executable, '-m', 'pip', 'install', '--upgrade', package_name
                ], capture_output=True, text=True, timeout=300)
                
                if result.returncode == 0:
                    logger.info(f"✅ Updated {package_name} to latest")
                    success_count += 1
                else:
                    logger.error(f"❌ Failed to update {package_name}: {result.stderr}")
                    failed_packages.append(package_name)
                    
        except subprocess.TimeoutExpired:
            logger.error(f"❌ Timeout updating {package_name}")
            failed_packages.append(package_name)
        except Exception as e:
            logger.error(f"❌ Error updating {package_name}: {e}")
            failed_packages.append(package_name)
    
    logger.info(f"📊 Update Summary: {success_count}/{len(security_updates)} packages updated")
    
    if failed_packages:
        logger.warning(f"Failed packages: {', '.join(failed_packages)}")
    
    return success_count, failed_packages

def update_non_critical_packages():
    """Update non-critical packages that are safe to update"""
    
    safe_updates = [
        'schedule',
        'pytz',
        'psutil',
        'aiofiles',
        'aiohttp'
    ]
    
    logger.info("📦 Updating non-critical packages...")
    
    success_count = 0
    for package in safe_updates:
        try:
            logger.info(f"Updating {package}...")
            result = subprocess.run([
                sys.executable, '-m', 'pip', 'install', '--upgrade', package
            ], capture_output=True, text=True, timeout=120)
            
            if result.returncode == 0:
                logger.info(f"✅ Updated {package}")
                success_count += 1
            else:
                logger.warning(f"⚠️ Could not update {package}: {result.stderr}")
                
        except Exception as e:
            logger.warning(f"⚠️ Error updating {package}: {e}")
    
    logger.info(f"📊 Non-critical updates: {success_count}/{len(safe_updates)} packages updated")
    return success_count

def check_critical_imports():
    """Test that critical imports still work after updates"""
    
    critical_modules = [
        'cryptography',
        'requests', 
        'urllib3',
        'certifi',
        'PIL',  # Pillow
        'dotenv',
        'bs4',  # beautifulsoup4
        'lxml',
        'httpx',
        'tenacity',
        'playwright',
        'telegram',
        'schedule',
        'pandas',
        'numpy'
    ]
    
    logger.info("🧪 Testing critical imports...")
    
    failed_imports = []
    for module in critical_modules:
        try:
            result = subprocess.run([
                sys.executable, '-c', f'import {module}; print(f"{module} OK")'
            ], capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                logger.info(f"✅ {module} import successful")
            else:
                logger.error(f"❌ {module} import failed: {result.stderr}")
                failed_imports.append(module)
                
        except Exception as e:
            logger.error(f"❌ Error testing {module}: {e}")
            failed_imports.append(module)
    
    if failed_imports:
        logger.error(f"💥 Failed imports: {', '.join(failed_imports)}")
        return False
    else:
        logger.info("✅ All critical imports successful")
        return True

def update_requirements_file():
    """Update requirements.txt with current installed versions"""
    
    logger.info("📝 Updating requirements.txt...")
    
    try:
        # Get current installed packages
        result = subprocess.run([
            sys.executable, '-m', 'pip', 'freeze'
        ], capture_output=True, text=True, check=True)
        
        installed_packages = {}
        for line in result.stdout.strip().split('\n'):
            if '==' in line and not line.startswith('-e'):
                name, version = line.split('==', 1)
                installed_packages[name.lower()] = f"{name}=={version}"
        
        # Read current requirements
        req_file = Path('requirements.txt')
        if req_file.exists():
            current_requirements = req_file.read_text().strip().split('\n')
        else:
            current_requirements = []
        
        # Update requirements while preserving comments and structure
        updated_requirements = []
        updated_packages = set()
        
        for line in current_requirements:
            line = line.strip()
            if not line or line.startswith('#'):
                updated_requirements.append(line)
                continue
            
            # Extract package name
            if '==' in line:
                package_name = line.split('==')[0].strip()
            elif '>=' in line:
                package_name = line.split('>=')[0].strip()
            else:
                package_name = line.strip()
            
            # Update with current version if available
            if package_name.lower() in installed_packages:
                updated_requirements.append(installed_packages[package_name.lower()])
                updated_packages.add(package_name.lower())
            else:
                updated_requirements.append(line)
        
        # Write updated requirements
        req_file.write_text('\n'.join(updated_requirements) + '\n')
        logger.info(f"✅ Updated requirements.txt with {len(updated_packages)} packages")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Failed to update requirements.txt: {e}")
        return False

def main():
    """Main dependency update process"""
    
    logger.info("🚀 Starting dependency update process...")
    
    # Check virtual environment
    if not ensure_virtual_env():
        return 1
    
    # Update security-critical packages
    security_success, failed_packages = update_security_critical_packages()
    
    # Update non-critical packages
    non_critical_success = update_non_critical_packages()
    
    # Test imports
    imports_ok = check_critical_imports()
    
    if not imports_ok:
        logger.error("💥 Critical imports failed - dependency update has issues")
        return 1
    
    # Update requirements file
    req_updated = update_requirements_file()
    
    # Summary
    logger.info("📊 Dependency Update Summary:")
    logger.info(f"   Security packages: {security_success} updated")
    logger.info(f"   Non-critical packages: {non_critical_success} updated")
    logger.info(f"   Critical imports: {'✅ PASSED' if imports_ok else '❌ FAILED'}")
    logger.info(f"   Requirements.txt: {'✅ UPDATED' if req_updated else '❌ FAILED'}")
    
    if failed_packages:
        logger.warning(f"⚠️ Some packages failed to update: {', '.join(failed_packages)}")
        logger.warning("These may need manual attention or have dependency conflicts")
    
    if imports_ok and security_success > 0:
        logger.info("🎉 Dependency updates completed successfully!")
        return 0
    else:
        logger.error("💥 Dependency updates had issues!")
        return 1

if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO, 
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    exit(main())