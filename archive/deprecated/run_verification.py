import subprocess
import sys
import os

# Change to the correct directory
os.chdir('/home/ohms/OhmsAlertsReports/daily-report')

# Run the verification script
try:
    result = subprocess.run([
        sys.executable, 'verify_fixes.py'
    ], capture_output=True, text=True, timeout=30)
    
    print("=== VERIFICATION OUTPUT ===")
    print(result.stdout)
    
    if result.stderr:
        print("=== ERRORS ===")
        print(result.stderr)
    
    print(f"Return code: {result.returncode}")
    
except subprocess.TimeoutExpired:
    print("Verification timed out")
except Exception as e:
    print(f"Error running verification: {e}")

# Also run a quick test of the playwright installation
print("\n=== PLAYWRIGHT TEST ===")
try:
    result2 = subprocess.run([
        './venv/bin/python', '-c', 
        'import subprocess; print("Testing playwright install..."); subprocess.run(["./venv/bin/python", "-m", "playwright", "install", "--help"], timeout=5)'
    ], capture_output=True, text=True, timeout=10)
    
    if result2.returncode == 0:
        print("✅ Playwright CLI is accessible")
    else:
        print("❌ Playwright CLI issue")
        
except Exception as e:
    print(f"Playwright test failed: {e}")

print("\n=== DISK SPACE CHECK ===")
import shutil
total, used, free = shutil.disk_usage('/')
print(f"Total: {total // (1024**3)} GB")
print(f"Used: {used // (1024**3)} GB") 
print(f"Free: {free // (1024**3)} GB")

# Quick check of /tmp
total_tmp, used_tmp, free_tmp = shutil.disk_usage('/tmp')
print(f"/tmp Free: {free_tmp // (1024**2)} MB")