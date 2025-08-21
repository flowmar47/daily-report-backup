import subprocess
import sys
import os

# Change to correct directory
os.chdir('/home/ohms/OhmsAlertsReports/daily-report')

# Run the fresh data test
print("Starting fresh data verification...")
result = subprocess.run([sys.executable, 'test_fresh_data.py'], capture_output=True, text=True)

print("=== TEST OUTPUT ===")
print(result.stdout)

if result.stderr:
    print("=== ERRORS ===")
    print(result.stderr)

print(f"Return code: {result.returncode}")

# Check if verification result was created
if os.path.exists('verification_result.json'):
    import json
    with open('verification_result.json', 'r') as f:
        verification = json.load(f)
    
    print("\n=== VERIFICATION RESULT ===")
    print(json.dumps(verification, indent=2))