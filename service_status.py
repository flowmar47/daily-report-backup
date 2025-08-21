#!/usr/bin/env python3
"""
Service Status Dashboard for Ohms Daily Alerts
Shows current status of all components
"""
import os
import subprocess
import requests
from datetime import datetime
from pathlib import Path
import json

def check_service(service_name):
    """Check if systemd service is active"""
    try:
        result = subprocess.run(
            ['systemctl', 'is-active', service_name],
            capture_output=True,
            text=True
        )
        return result.stdout.strip() == 'active'
    except:
        return False

def check_signal_api():
    """Check Signal API health"""
    try:
        response = requests.get('http://localhost:8080/v1/health', timeout=5)
        return response.status_code == 200
    except:
        return False

def get_last_report_time():
    """Get time of last report"""
    try:
        reports_dir = Path('reports')
        if reports_dir.exists():
            report_files = list(reports_dir.glob('daily_report_*.json'))
            if report_files:
                latest = max(report_files, key=lambda p: p.stat().st_mtime)
                return datetime.fromtimestamp(latest.stat().st_mtime)
    except:
        pass
    return None

def get_next_run_time():
    """Calculate next scheduled run"""
    with open('config.json', 'r') as f:
        config = json.load(f)
    
    report_time = config['app_settings']['report_time']
    report_days = config['app_settings']['report_days']
    
    # Convert to datetime
    hour, minute = map(int, report_time.split(':'))
    now = datetime.now()
    
    # Find next weekday
    days_map = {
        'monday': 0, 'tuesday': 1, 'wednesday': 2,
        'thursday': 3, 'friday': 4
    }
    
    weekdays = [days_map[day.lower()] for day in report_days]
    
    # Find next scheduled day
    for i in range(7):
        future = now + timedelta(days=i)
        if future.weekday() in weekdays:
            next_run = future.replace(hour=hour, minute=minute, second=0, microsecond=0)
            if next_run > now:
                return next_run
    
    return None

def main():
    print("=" * 60)
    print("Ohms Daily Alerts - Service Status Dashboard")
    print("=" * 60)
    print(f"Current Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} PST")
    print("")
    
    # Service Status
    print("Service Status:")
    print("-" * 30)
    
    services = [
        ('daily-alerts.service', 'Main Service'),
        ('signal-api.service', 'Signal API'),
        ('monitor.service', 'Monitor Service')
    ]
    
    for service, name in services:
        status = "🟢 Active" if check_service(service) else "🔴 Inactive"
        print(f"{name:20} {status}")
    
    # API Status
    print("")
    print("API Status:")
    print("-" * 30)
    signal_status = "🟢 Healthy" if check_signal_api() else "🔴 Unavailable"
    print(f"Signal API:          {signal_status}")
    
    # Report Status
    print("")
    print("Report Status:")
    print("-" * 30)
    
    last_report = get_last_report_time()
    if last_report:
        time_ago = datetime.now() - last_report
        hours_ago = time_ago.total_seconds() / 3600
        print(f"Last Report:         {last_report.strftime('%Y-%m-%d %H:%M')} ({hours_ago:.1f} hours ago)")
    else:
        print("Last Report:         No reports found")
    
    # Next scheduled run
    try:
        from datetime import timedelta
        next_run = get_next_run_time()
        if next_run:
            time_until = next_run - datetime.now()
            hours_until = time_until.total_seconds() / 3600
            print(f"Next Scheduled:      {next_run.strftime('%Y-%m-%d %H:%M')} ({hours_until:.1f} hours)")
    except:
        print("Next Scheduled:      Unable to calculate")
    
    # Quick Actions
    print("")
    print("Quick Actions:")
    print("-" * 30)
    print("View logs:           sudo journalctl -u daily-alerts -f")
    print("Restart service:     sudo systemctl restart daily-alerts")
    print("Send test report:    ./manage_service.sh test-report")
    print("Check config:        ./manage_service.sh test")
    
    print("=" * 60)

if __name__ == "__main__":
    main()