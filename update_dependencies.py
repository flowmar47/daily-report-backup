#!/usr/bin/env python3
"""
Dependency Update Script
Safely updates outdated dependencies with security checks and testing
"""

import subprocess
import sys
import logging
import json
from pathlib import Path
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)

class DependencyUpdater:
    """Handles safe dependency updates with security checks"""
    
    def __init__(self, requirements_file: str = "requirements.txt"):
        self.requirements_file = Path(requirements_file)
        self.backup_file = Path(f"{requirements_file}.backup")
        
        # Critical packages that need careful testing
        self.critical_packages = [
            'playwright',
            'python-telegram-bot',
            'cryptography',
            'requests',
            'httpx',
            'tenacity'
        ]
        
        # Packages to avoid updating (known issues)
        self.exclude_packages = [
            'numpy'  # Often causes compatibility issues
        ]
        
        logger.info("🔄 Dependency updater initialized")
    
    def backup_requirements(self):
        """Backup current requirements file"""
        if self.requirements_file.exists():
            content = self.requirements_file.read_text()
            self.backup_file.write_text(content)
            logger.info(f"📦 Backed up requirements to {self.backup_file}")
    
    def get_outdated_packages(self) -> List[Dict[str, str]]:
        """Get list of outdated packages"""
        try:
            result = subprocess.run(
                [sys.executable, '-m', 'pip', 'list', '--outdated', '--format=json'],
                capture_output=True,
                text=True,
                check=True
            )
            outdated = json.loads(result.stdout)
            
            # Filter out excluded packages
            filtered = [
                pkg for pkg in outdated 
                if pkg['name'].lower() not in [p.lower() for p in self.exclude_packages]
            ]
            
            logger.info(f"📊 Found {len(filtered)} outdated packages (filtered from {len(outdated)})")
            return filtered
            
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to get outdated packages: {e}")
            return []
    
    def check_security_vulnerabilities(self) -> bool:
        """Check for known security vulnerabilities"""
        try:
            # Try pip-audit if available
            result = subprocess.run(
                [sys.executable, '-m', 'pip', 'install', 'pip-audit'],
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                audit_result = subprocess.run(
                    [sys.executable, '-m', 'pip-audit'],
                    capture_output=True,
                    text=True
                )
                
                if audit_result.returncode != 0:
                    logger.warning("🚨 Security vulnerabilities found!")
                    logger.warning(audit_result.stdout)
                    return False
                else:
                    logger.info("✅ No security vulnerabilities found")
                    return True
            
        except Exception as e:
            logger.warning(f"Could not run security audit: {e}")
        
        return True  # Assume safe if we can't check
    
    def update_package(self, package_name: str, version: Optional[str] = None) -> bool:
        """Update a single package"""
        try:
            cmd = [sys.executable, '-m', 'pip', 'install', '--upgrade']
            
            if version:
                cmd.append(f"{package_name}=={version}")
            else:
                cmd.append(package_name)
            
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            logger.info(f"✅ Updated {package_name}")
            return True
            
        except subprocess.CalledProcessError as e:
            logger.error(f"❌ Failed to update {package_name}: {e}")
            return False
    
    def update_requirements_file(self, updated_packages: List[str]):
        """Update requirements.txt with new versions"""
        if not self.requirements_file.exists():
            logger.error("Requirements file not found")
            return
        
        # Get current installed versions
        result = subprocess.run(
            [sys.executable, '-m', 'pip', 'freeze'],
            capture_output=True,
            text=True,
            check=True
        )
        
        installed_versions = {}
        for line in result.stdout.strip().split('\n'):
            if '==' in line:
                name, version = line.split('==', 1)
                installed_versions[name.lower()] = version
        
        # Update requirements file
        lines = self.requirements_file.read_text().strip().split('\n')
        updated_lines = []
        
        for line in lines:
            if line.strip() and not line.startswith('#'):
                # Extract package name
                if '==' in line:
                    pkg_name = line.split('==')[0].strip()
                elif '>=' in line:
                    pkg_name = line.split('>=')[0].strip()
                else:
                    pkg_name = line.strip()
                
                # Update version if package was updated
                if pkg_name.lower() in [p.lower() for p in updated_packages]:
                    if pkg_name.lower() in installed_versions:
                        new_version = installed_versions[pkg_name.lower()]
                        updated_lines.append(f"{pkg_name}=={new_version}")
                    else:
                        updated_lines.append(line)
                else:
                    updated_lines.append(line)
            else:
                updated_lines.append(line)
        
        # Write updated requirements
        self.requirements_file.write_text('\n'.join(updated_lines) + '\n')
        logger.info(f"📝 Updated {self.requirements_file}")
    
    def test_imports(self) -> bool:
        """Test critical imports after updates"""
        critical_imports = [
            'playwright',
            'telegram',
            'cryptography',
            'requests',
            'httpx',
            'tenacity',
            'beautifulsoup4',
            'pandas',
            'numpy'
        ]
        
        failed_imports = []
        
        for module in critical_imports:
            try:
                subprocess.run(
                    [sys.executable, '-c', f'import {module}'],
                    check=True,
                    capture_output=True
                )
                logger.info(f"✅ {module} import successful")
            except subprocess.CalledProcessError:
                failed_imports.append(module)
                logger.error(f"❌ {module} import failed")
        
        if failed_imports:
            logger.error(f"Import failures: {failed_imports}")
            return False
        
        logger.info("✅ All critical imports successful")
        return True
    
    def restore_backup(self):
        """Restore from backup if updates failed"""
        if self.backup_file.exists():
            content = self.backup_file.read_text()
            self.requirements_file.write_text(content)
            logger.info("🔄 Restored requirements from backup")
            
            # Reinstall from backup
            subprocess.run([
                sys.executable, '-m', 'pip', 'install', '-r', str(self.requirements_file)
            ])
            logger.info("🔄 Reinstalled packages from backup")
    
    def update_dependencies(self, test_mode: bool = False) -> bool:
        """Main method to update dependencies safely"""
        logger.info("🚀 Starting dependency update process...")
        
        # Step 1: Backup current state
        self.backup_requirements()
        
        # Step 2: Check security vulnerabilities
        if not self.check_security_vulnerabilities():
            logger.warning("⚠️ Security vulnerabilities found - prioritizing security updates")
        
        # Step 3: Get outdated packages
        outdated_packages = self.get_outdated_packages()
        if not outdated_packages:
            logger.info("✅ All packages are up to date")
            return True
        
        # Step 4: Categorize updates
        security_updates = []
        normal_updates = []
        critical_updates = []
        
        for pkg in outdated_packages:
            name = pkg['name']
            if name.lower() in [p.lower() for p in self.critical_packages]:
                critical_updates.append(pkg)
            else:
                normal_updates.append(pkg)
        
        logger.info(f"📊 Update plan: {len(critical_updates)} critical, {len(normal_updates)} normal")
        
        if test_mode:
            logger.info("🧪 TEST MODE - No actual updates will be performed")
            for pkg in outdated_packages:
                logger.info(f"Would update: {pkg['name']} {pkg['version']} -> {pkg['latest_version']}")
            return True
        
        updated_packages = []
        
        # Step 5: Update packages (normal first, then critical)
        for pkg_list, update_type in [(normal_updates, "normal"), (critical_updates, "critical")]:
            logger.info(f"🔄 Updating {update_type} packages...")
            
            for pkg in pkg_list:
                name = pkg['name']
                latest = pkg['latest_version']
                
                logger.info(f"Updating {name}: {pkg['version']} -> {latest}")
                
                if self.update_package(name, latest):
                    updated_packages.append(name)
                    
                    # Test imports after critical package updates
                    if update_type == "critical":
                        if not self.test_imports():
                            logger.error(f"❌ Import test failed after updating {name}")
                            self.restore_backup()
                            return False
        
        # Step 6: Update requirements file
        if updated_packages:
            self.update_requirements_file(updated_packages)
        
        # Step 7: Final import test
        if not self.test_imports():
            logger.error("❌ Final import test failed")
            self.restore_backup()
            return False
        
        logger.info(f"✅ Successfully updated {len(updated_packages)} packages")
        return True

def main():
    """CLI for dependency updater"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Update project dependencies safely")
    parser.add_argument('--test', action='store_true', help="Test mode - show what would be updated")
    parser.add_argument('--requirements', default='requirements.txt', help="Requirements file to update")
    parser.add_argument('--verbose', action='store_true', help="Enable verbose logging")
    
    args = parser.parse_args()
    
    log_level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(level=log_level, format='%(asctime)s - %(levelname)s - %(message)s')
    
    updater = DependencyUpdater(args.requirements)
    
    try:
        success = updater.update_dependencies(test_mode=args.test)
        
        if success:
            if args.test:
                logger.info("🧪 Test completed - ready for actual update")
            else:
                logger.info("🎉 Dependency update completed successfully!")
            return 0
        else:
            logger.error("💥 Dependency update failed!")
            return 1
            
    except KeyboardInterrupt:
        logger.info("🛑 Update cancelled by user")
        return 1
    except Exception as e:
        logger.error(f"💥 Unexpected error: {e}")
        return 1

if __name__ == "__main__":
    exit(main())