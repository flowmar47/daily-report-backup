#!/usr/bin/env python3
"""Test script to verify setup"""

import sys
import importlib
import os
from pathlib import Path

def test_imports():
    """Test that all required modules can be imported"""
    modules = [
        'playwright', 'telegram', 'dotenv', 'schedule',
        'bs4', 'aiofiles', 'pandas', 'psutil'
    ]
    
    print("Testing Python imports...")
    for module in modules:
        try:
            importlib.import_module(module)
            print(f"✓ {module}")
        except ImportError as e:
            print(f"✗ {module}: {e}")
            return False
    return True

def test_files():
    """Test that required files exist"""
    files = [
        '.env', 'main.py', 'utils.py', 'config.json',
        'requirements.txt', 'example.md'
    ]
    
    print("\nChecking required files...")
    for file in files:
        if Path(file).exists():
            print(f"✓ {file}")
        else:
            print(f"✗ {file} not found")
            return False
    return True

def test_directories():
    """Test that required directories exist"""
    dirs = ['browser_sessions', 'logs', 'reports']
    
    print("\nChecking directories...")
    for dir in dirs:
        if Path(dir).is_dir():
            print(f"✓ {dir}/")
        else:
            print(f"✗ {dir}/ not found")
            return False
    return True

def test_env():
    """Test environment variables"""
    from dotenv import load_dotenv
    load_dotenv()
    
    vars = [
        'MYMAMA_USERNAME', 'MYMAMA_PASSWORD',
        'XYNTH_USERNAME', 'XYNTH_PASSWORD',
        'TELEGRAM_BOT_TOKEN', 'TELEGRAM_GROUP_ID'
    ]
    
    print("\nChecking environment variables...")
    all_set = True
    for var in vars:
        value = os.getenv(var)
        if value and value != f'your_{var.lower()}_here':
            print(f"✓ {var} is set")
        else:
            print(f"✗ {var} not configured")
            all_set = False
    
    return all_set

if __name__ == "__main__":
    print("Running setup tests...\n")
    
    imports_ok = test_imports()
    files_ok = test_files()
    dirs_ok = test_directories()
    env_ok = test_env()
    
    print("\n" + "="*40)
    if all([imports_ok, files_ok, dirs_ok]):
        print("✓ Basic setup complete!")
        if not env_ok:
            print("⚠ Please configure your .env file with actual credentials")
    else:
        print("✗ Setup incomplete. Please check the errors above.")
        sys.exit(1)
