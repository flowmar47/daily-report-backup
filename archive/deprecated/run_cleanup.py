import subprocess
import sys

# Run the cleanup script
try:
    result = subprocess.run([sys.executable, "/home/ohms/OhmsAlertsReports/daily-report/cleanup.py"], 
                          capture_output=True, text=True)
    print("STDOUT:")
    print(result.stdout)
    if result.stderr:
        print("STDERR:")
        print(result.stderr)
    print(f"Return code: {result.returncode}")
except Exception as e:
    print(f"Error running cleanup: {e}")