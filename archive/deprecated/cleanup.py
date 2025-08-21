#!/usr/bin/env python3
"""
System cleanup script to free up disk space
"""

import os
import shutil
import subprocess
import glob
from pathlib import Path

def run_command(cmd, ignore_errors=True):
    """Run a shell command safely"""
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✓ {cmd}")
            return True
        else:
            if not ignore_errors:
                print(f"✗ {cmd}: {result.stderr}")
            return False
    except Exception as e:
        if not ignore_errors:
            print(f"✗ {cmd}: {e}")
        return False

def clean_directory(path, pattern="*", days_old=None):
    """Clean files in directory matching pattern"""
    try:
        if days_old:
            # Clean files older than specified days
            import time
            cutoff_time = time.time() - (days_old * 24 * 60 * 60)
            
        for file_path in glob.glob(os.path.join(path, pattern)):
            try:
                if os.path.isfile(file_path):
                    if days_old:
                        if os.path.getmtime(file_path) < cutoff_time:
                            os.remove(file_path)
                            print(f"Removed old file: {file_path}")
                    else:
                        os.remove(file_path)
                        print(f"Removed: {file_path}")
                elif os.path.isdir(file_path):
                    shutil.rmtree(file_path)
                    print(f"Removed directory: {file_path}")
            except Exception as e:
                print(f"Could not remove {file_path}: {e}")
        return True
    except Exception as e:
        print(f"Error cleaning {path}: {e}")
        return False

def main():
    print("🧹 Starting system cleanup...")
    
    # 1. Clean APT cache
    print("\n📦 Cleaning package manager cache...")
    run_command("sudo apt clean")
    run_command("sudo apt autoremove -y")
    
    # 2. Remove playwright duplicates
    print("\n🎭 Cleaning playwright duplicates...")
    playwright_duplicate = "/home/ohms/.cache/ms-playwright/chromium_headless_shell-1169"
    if os.path.exists(playwright_duplicate):
        try:
            shutil.rmtree(playwright_duplicate)
            print(f"✓ Removed duplicate: {playwright_duplicate}")
        except Exception as e:
            print(f"✗ Could not remove {playwright_duplicate}: {e}")
    
    # 3. Clean Python cache files
    print("\n🐍 Cleaning Python cache files...")
    base_path = "/home/ohms/OhmsAlertsReports"
    
    # Remove __pycache__ directories
    for pycache_dir in Path(base_path).rglob("__pycache__"):
        try:
            shutil.rmtree(pycache_dir)
            print(f"✓ Removed: {pycache_dir}")
        except Exception as e:
            print(f"✗ Could not remove {pycache_dir}: {e}")
    
    # Remove .pyc files
    for pyc_file in Path(base_path).rglob("*.pyc"):
        try:
            pyc_file.unlink()
            print(f"✓ Removed: {pyc_file}")
        except Exception as e:
            print(f"✗ Could not remove {pyc_file}: {e}")
    
    # 4. Clean pip cache
    print("\n📋 Cleaning pip cache...")
    run_command("pip cache purge")
    
    # 5. Clean old log files (older than 7 days)
    print("\n📄 Cleaning old log files...")
    log_patterns = [
        "/home/ohms/OhmsAlertsReports/**/*.log",
        "/home/ohms/OhmsAlertsReports/**/logs/*.log"
    ]
    
    import time
    cutoff_time = time.time() - (7 * 24 * 60 * 60)  # 7 days
    
    for pattern in log_patterns:
        for log_file in glob.glob(pattern, recursive=True):
            try:
                if os.path.getmtime(log_file) < cutoff_time:
                    os.remove(log_file)
                    print(f"✓ Removed old log: {log_file}")
            except Exception as e:
                print(f"✗ Could not remove {log_file}: {e}")
    
    # 6. Clean browser sessions
    print("\n🌐 Cleaning browser sessions...")
    browser_sessions = "/home/ohms/OhmsAlertsReports/daily-report/browser_sessions"
    if os.path.exists(browser_sessions):
        clean_directory(browser_sessions)
    
    # 7. Clean docker if available
    print("\n🐳 Cleaning docker system...")
    run_command("sudo docker system prune -f")
    
    # 8. Clean npm cache if available
    print("\n📦 Cleaning npm cache...")
    run_command("npm cache clean --force")
    
    # 9. Show disk usage
    print("\n💾 Disk usage after cleanup:")
    run_command("df -h | grep -E '(Filesystem|/$|/tmp)'", ignore_errors=False)
    
    print("\n✨ Cleanup completed!")

if __name__ == "__main__":
    main()