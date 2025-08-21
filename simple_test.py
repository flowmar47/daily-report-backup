print("Python is working!")
import os
print(f"Current directory: {os.getcwd()}")
print(f"Python version: {os.sys.version}")

# Test if we can remove the duplicate chromium
import shutil
playwright_dup = "/home/ohms/.cache/ms-playwright/chromium_headless_shell-1169"
if os.path.exists(playwright_dup):
    try:
        shutil.rmtree(playwright_dup)
        print(f"✓ Removed duplicate chromium: {playwright_dup}")
    except Exception as e:
        print(f"✗ Could not remove duplicate: {e}")
else:
    print("✓ Duplicate chromium already removed")